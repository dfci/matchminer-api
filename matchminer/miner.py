import os
import binascii
import time
import logging
import json
import hashlib
import pandas as pd
import datetime
from jinja2 import Environment, PackageLoader
import oncotreenx
import networkx as nx
import dateutil.parser
import re
from bson import ObjectId


from tcm.engine import CBioEngine
from matchminer.constants import synonyms
from matchminer import settings, data_model, database, custom
from matchminer.utilities import REREPLACEMENTS, get_recursively
from matchminer.templates.emails import emails

# logging
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', )


def _email_text(user, num_matches, match_str, num_filters, cur_date, cur_stamp):
    html = '''<html><head></head><body>%s</body></html>''' % emails.FILTER_MATCH_BODY.format(
      user['first_name'],
      user['last_name'],
      num_matches,
      match_str,
      num_filters,
      cur_date,
      cur_stamp
    )
    return html


def _email_counts(teamid, match_db, filter_db):

    num_matches = 0
    num_filters = 0

    # look for matches.
    matches = list(match_db.find({'TEAM_ID': ObjectId(teamid)}))

    # calculate number of matches.
    counts = custom._count_matches(matches, match_db)
    num_matches += counts['new_matches']

    # get the number of filters.
    num_filters += filter_db.find({'TEAM_ID': teamid, 'status': 1}).count()

    # return the counts
    return num_filters, num_matches


def email_matches():

    # get the database links.
    match_db = database.get_collection("match")
    user_db = database.get_collection('user')
    filter_db = database.get_collection('filter')

    logging.info("emailing filter matches - starting email search")

    # get distinct list of team ids
    teams = match_db.find().distinct("TEAM_ID")

    # loop over each team.
    message_list = []
    for teamid in teams:

        # get the counts.
        num_filters, num_matches = _email_counts(teamid, match_db, filter_db)

        # skip if no updates.
        if num_matches < 1:
            continue

        # get users in this team
        team_members = list(user_db.find({'teams': {'$elemMatch': {'$in': [teamid]}}}))
        for user in team_members:

            # skip if silenced.
            if 'silent' in user and user['silent']:
                continue

            # simplify.
            recipient_email = user['email']
            match_str = "matches"
            if num_matches == 1:
                match_str = "match"

            # create the message.
            cur_date = datetime.date.today().strftime("%B %d, %Y")
            cur_stamp = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")

            # generate text
            html = _email_text(user, num_matches, match_str, num_filters, cur_date, cur_stamp)

            db = database.get_db()
            email_item = {
                'email_from': settings.EMAIL_AUTHOR_PROTECTED,
                'email_to': recipient_email,
                'subject': 'New MatchMiner Hits - %s' % cur_date,
                'body': html,
                'cc': [],
                'sent': False,
                'num_failures': 0,
                'errors': []
            }
            db['email'].insert(email_item)

            message_list.append(html)

    # return the message lists
    return message_list


def rerun_filters(dpi=None):
    """ re-runs all filters against new data. preserves options set on
    old matches.

    :return: count of new matches
    """

    # get the database links.
    match_db = database.get_collection('match')
    filter_db = database.get_collection('filter')

    # create the object.
    cbio = CBioEngine(settings.MONGO_URI,
                      settings.MONGO_DBNAME,
                      data_model.match_schema,
                      muser=settings.MONGO_USERNAME,
                      mpass=settings.MONGO_PASSWORD,
                      collection_clinical=settings.COLLECTION_CLINICAL,
                      collection_genomic=settings.COLLECTION_GENOMIC)

    query = {'status': 1, 'temporary': False, 'trial_watch': {'$exists': False}}
    filters = list(filter_db.find(query))
    for filter_ in filters:

        # lots of logging.
        logging.info("rerun_filters: filter: %s" % filter_['_id'])

        # prepare the filters.
        c, g, txt = prepare_criteria(filter_)

        # execute the match.
        cbio.match(c=c, g=g)

        if cbio.match_df is not None and cbio.genomic_df is not None and cbio.clinical_df is not None:
            logging.info("rerun_filters: new matches: match=%d, genomic=%d, clinical=%d" % (len(cbio.match_df), len(cbio.genomic_df), len(cbio.clinical_df)))

        # get existing matches for this filter.
        matches = list(match_db.find({'FILTER_ID': ObjectId(filter_['_id'])}))

        rec_cnt = 0
        for m in matches:
            rec_cnt += len(m['VARIANTS'])

        logging.info("rerun_filters: exisiting: %d %d" % (len(matches), rec_cnt))

        # parse the old matches.
        clinical_old_id = set()
        old_lu = {}
        match_lu = {}
        for match in matches:

            # get the clincal id.
            clinical_id = match['CLINICAL_ID']

            # now build tuples of variants.
            for genomic_id in match['VARIANTS']:

                # make pair
                pair = (clinical_id, genomic_id)
                clinical_old_id.add(pair)

                # build id lookup.
                old_lu[pair] = match['_id']

                # cache matches.
                match_lu[pair] = match

        # parse the new matches.
        clinical_new_id = set()
        new_lu = {}
        i = 0
        for match in cbio.match_iter():

            # simplify.
            clinical_id = match['CLINICAL_ID']
            genomic_id = match['GENOMIC_ID']

            # build set.
            pair = (clinical_id, genomic_id)
            clinical_new_id.add(pair)

            # cache matches.
            match_lu[pair] = match

            # build lookup.
            new_lu[pair] = i
            i += 1

        # find the ones which need to be deleted and delete them.
        to_delete = clinical_old_id - clinical_new_id
        logging.info("rerun_filters: removing: %d" % len(to_delete))
        updated = list()
        for pair in to_delete:

            # extract ids
            match_id = old_lu[pair]
            match = match_lu[pair]

            # find the variant.
            good = list()
            hit = False
            for v in match['VARIANTS']:
                if v != pair[1]:
                    good.append(v)
                else:
                    hit = True

            # update it if necessary.
            if hit:

                # check if will empty this.
                if len(good) == 0:

                    # delete it.
                    match_db.delete_one({'_id': match_id})
                else:

                    # just update it.
                    match_db.update({"_id": match_id}, {"$set": {"VARIANTS": good}})

                    # update the local one to make sure we delete all variants
                    match['VARIANTS'] = good

        # find the intersection and remove them from data frame.
        remove_frame = clinical_new_id.intersection(clinical_old_id)
        bad_list = []
        for pair in remove_frame:

            # lookup index.
            idx = new_lu[pair]
            bad_list.append(idx)

        logging.info("rerun_filters: skipping: %d" % len(bad_list))

        # remove them.
        if cbio.match_df is not None and len(cbio.match_df) > 0:
            cbio.match_df.drop(cbio.match_df.index[bad_list], inplace=True)

        # insert the counts.
        count_matches(cbio, filter_)

        # insert the matches if not temporary.
        insert_matches(cbio, filter_, from_filter=False, dpi=dpi)


def detect_update(cbio, item):
    """ determines if genomic_filter or clinical_filter were changed
        using hash strategy. updates hash if change.

    :param item: the POSTed filter
    """

    # compute hash.
    txt = ""
    if 'genomic_filter' in item:
        txt += json.dumps(item['genomic_filter'])
    if 'clinical_filter' in item:
        txt += json.dumps(item['clinical_filter'])
    hash_new = hashlib.md5(txt).hexdigest()

    # compute status.
    updated = False

    # lookup the full document.
    filter_db = cbio.connection[cbio.mongo_dbname]['filter']
    filter_obj = filter_db.find_one({'_id': item['_id']})

    # look if filter_hash is set.
    if 'filter_hash' not in filter_obj:
        updated = True

    # hash was set, detect change.
    elif hash_new != filter_obj['filter_hash']:
        updated = True

    # update the hash value in db.
    if updated:
        filter_db = cbio.connection[cbio.mongo_dbname]['filter']
        logging.info("updating filter wish hash: %s + %s" % (hash_new, txt))
        filter_db.update_one({'_id': item['_id']}, {'$set': {'filter_hash': hash_new}})

    # return truth.
    return updated


def remove_matches(cbio, item):
    """ removes existing matches based on filter_id

    :param cbio: CBioEngine
    :param item: post-validation dictionary
    """

    logging.info("removing existing matches")

    # delete matches with current filter id.
    match_db = cbio.connection[cbio.mongo_dbname]['match']
    match_db.delete_many({'FILTER_ID': item['_id']})


def count_matches(cbio, item):
    """ calculate the number of matches.
        save it to the object [careful this is post-validation!]
    :param cbio: CBioEngine
    :param item: post-validation dictionary
    """

    # build total date array.
    today = datetime.date.today() + datetime.timedelta(1*365/12)
    all_dates = pd.date_range(datetime.datetime(2013, 7, 1), today, freq='BM')
    all_dates = all_dates.map(lambda x: datetime.datetime(x.year, x.month, 1))
    all_dates = pd.Series(all_dates)

    # determine if empty.
    if cbio.match_df is None or cbio.match_df.shape[0] == 0:

        # handle empty matches.
        item['num_matches'] = 0
        item['num_pairs'] = 0
        item['num_samples'] = 0
        if cbio.clinical_df.shape[0] == 0:
            item['num_clinical'] = 0
        else:
            item['num_clinical'] = cbio.clinical_df[cbio.clinical_df['VITAL_STATUS'] == 'alive'].shape[0]
        item['num_genomic'] = cbio.living_genomic

        # compute empty counts.
        counts = all_dates.value_counts()
        counts = counts - 1
        counts = counts.sort_index()

    else:

        # compute number of filter / patient pairs.
        pair_cnt = cbio.match_df.groupby(['CLINICAL_ID', '_id_y']).size().shape[0]

        # matches are present.
        item['num_matches'] = cbio.match_df.shape[0]
        item['num_pairs'] = pair_cnt
        item['num_samples'] = cbio.match_df['SAMPLE_ID'].unique().shape[0]
        item['num_clinical'] = cbio.clinical_df[cbio.clinical_df['VITAL_STATUS'] == 'alive'].shape[0]
        item['num_genomic'] = cbio.living_genomic

        # extract the actual dates.
        hits = cbio.match_all_df.REPORT_DATE.map(lambda x: datetime.datetime(x.year, x.month, 1) if pd.notnull(x) else x)

        # combine them and remove base counts.
        total_dates = all_dates.append(hits)
        counts = total_dates.value_counts()
        counts = counts - 1
        counts = counts.sort_index()

    # special case for genomic_shape.
    if cbio.genomic_df.shape[0] == 0:
        item['num_genomic_samples'] = 0
    else:
        item['num_genomic_samples'] = cbio.genomic_df['SAMPLE_ID'].unique().shape[0]

    # convert to lists.
    x_axis = list(counts.index)
    y_axis = list(counts)

    # convert x_axis to plot.ly format.
    x_axis = [d.strftime("%y-%m-%d") for d in x_axis]

    # save to object.
    item['enrollment'] = {
        'x_axis': x_axis,
        'y_axis': y_axis
    }


def insert_matches(cbio, item, from_filter=True, dpi=None):

    start_iter = time.time()
    filter_db = database.get_collection('filter')

    pf_pairz = dict()
    filters = dict()
    for silly in cbio.match_iter():

        filter_id = item['_id']
        clinical_id = silly['CLINICAL_ID']
        key = (filter_id, clinical_id)

        if key not in pf_pairz:
            pf_pairz[key] = list()

        if filter_id not in filters:
            filter_obj = filter_db.find_one({'_id': filter_id})
            filters[filter_id] = filter_obj

        pf_pairz[key].append(silly['GENOMIC_ID'])

    user_id = item['USER_ID']
    team_id = item['TEAM_ID']
    filter_status = item['status']
    filter_name = item['label']
    clinical_lu = {}
    genomic_lu = {}

    matches = list()
    for key, val in pf_pairz.items():

        clinical_id = key[1]
        genomic_id = val[0]

        if clinical_id not in clinical_lu:
            clinical_lu[clinical_id] = cbio._c.find_one(clinical_id)

        if genomic_id not in genomic_lu:
            genomic_lu[genomic_id] = cbio._g.find_one(genomic_id)

        # extract clinical information
        clinical_info = [
            'ONCOTREE_PRIMARY_DIAGNOSIS_NAME',
            'ONCOTREE_BIOPSY_SITE_TYPE',
            'REPORT_DATE',
            'VARIANT_CATEGORY',
            'MRN',
            'ORD_PHYSICIAN_EMAIL'
        ]
        clinical_info_vals = [''] * len(clinical_info)
        for idx, c in enumerate(clinical_info):
            if c in clinical_lu[clinical_id]:
                clinical_info_vals[idx] = clinical_lu[clinical_id][c]
            else:
                clinical_info_vals[idx] = ""

        # extract gene symbol
        true_hugo_symbol = None
        if 'TRUE_HUGO_SYMBOL' in genomic_lu[genomic_id]:
            true_hugo_symbol = genomic_lu[genomic_id]['TRUE_HUGO_SYMBOL']

        if true_hugo_symbol is None:

            filter_ = filters[key[0]]
            if 'genomic_filter' in filter_ and 'TRUE_HUGO_SYMBOL' in filter_['genomic_filter']:

                true_hugo_symbol = filter_['genomic_filter']['TRUE_HUGO_SYMBOL']
                if isinstance(true_hugo_symbol, dict):
                    true_hugo_symbol = ', '.join([str(i) for i in true_hugo_symbol.values()[0]])

        if true_hugo_symbol is None:
            logging.error("error in filter logic")

        # extract tier information
        tier = None
        if 'TIER' in genomic_lu[genomic_id]:
            tier = genomic_lu[genomic_id]['TIER']

        match_status = 0
        if from_filter:
            match_status = 1

        if 'protocol_id' in item:
            protocol_id = item['protocol_id']
        else:
            protocol_id = ""

        email_subject = "(%s) ONCO PANEL RESULTS" % protocol_id
        email_body = email_content(protocol_id, genomic_lu[genomic_id], clinical_lu[clinical_id])

        matches.append({
            'USER_ID': user_id,
            'TEAM_ID': team_id,
            'FILTER_STATUS': filter_status,
            'MATCH_STATUS': match_status,
            'FILTER_ID': key[0],
            'CLINICAL_ID': key[1],
            'VARIANTS': val,
            'PATIENT_MRN': clinical_info_vals[clinical_info.index('MRN')],
            'MMID': binascii.b2a_hex(os.urandom(3)).upper(),
            'ONCOTREE_PRIMARY_DIAGNOSIS_NAME': clinical_info_vals[clinical_info.index('ONCOTREE_PRIMARY_DIAGNOSIS_NAME')],
            'ONCOTREE_BIOPSY_SITE_TYPE': clinical_info_vals[clinical_info.index('ONCOTREE_BIOPSY_SITE_TYPE')],
            'TRUE_HUGO_SYMBOL': true_hugo_symbol,
            'VARIANT_CATEGORY': clinical_info_vals[clinical_info.index('VARIANT_CATEGORY')],
            'FILTER_NAME': filter_name,
            'REPORT_DATE': clinical_info_vals[clinical_info.index('REPORT_DATE')],
            "EMAIL_ADDRESS": clinical_info_vals[clinical_info.index('ORD_PHYSICIAN_EMAIL')],
            "EMAIL_BODY": email_body,
            "EMAIL_SUBJECT": email_subject,
            'data_push_id': dpi,
            'TIER': tier
        })

    ttr_iter = time.time() - start_iter
    start_ins = time.time()

    if len(matches) > 0:
        match_db = database.get_collection("match")
        match_db.insert_many(matches)

    ttr_ins = time.time() - start_ins
    logging.info("match: added %d and it took %.2f to fetch, %.2f to insert" % (len(matches), ttr_iter, ttr_ins))


def email_content(protocol_id, genomic, clinical):

    # check for template.
    if not os.path.isfile("%s/templates/templates/%s.html" % (os.path.dirname(os.path.realpath(__file__)), protocol_id)):
        return ""

    # setup variables.
    mrn = clinical['MRN']

    if genomic['VARIANT_CATEGORY'] == 'MUTATION':
        if 'TRUE_PROTEIN_CHANGE' in genomic and genomic['TRUE_PROTEIN_CHANGE'] is not None:
            event = "%s %s mutation" % (genomic['TRUE_HUGO_SYMBOL'], genomic['TRUE_PROTEIN_CHANGE'].replace("p.", ""))
        else:
            event = "%s mutation" % (genomic['TRUE_HUGO_SYMBOL'])

    elif genomic['VARIANT_CATEGORY'] == 'CNV':
        event = "%s %s" % (genomic['TRUE_HUGO_SYMBOL'], genomic['CNV_CALL'].lower())

    else:
        event = "structural re-arrangement"

    # render the template.
    env = Environment(loader=PackageLoader('matchminer', 'templates/templates'))
    template = env.get_template('%s.html' % protocol_id)

    # generate the email.
    return template.render(mrn=mrn, event=event)


def update_match_status(cbio, item):

    # loop over all existing matches
    match_db = database.get_collection('match')

    # check if filter is deleted.
    if item['status'] == 2:

        # delete associated matches.
        logging.info("filter is deleted, deleting associated matches")
        match_db.delete_many({'FILTER_ID': item['_id']})

    elif item['status'] == 0:

        # archive associated matches.
        logging.info("filter is inactivated, deleting associated matches")
        match_db.delete_many({'FILTER_ID': item['_id']})

    else:

        # update matches only.
        match_db.update_many({'FILTER_ID': item['_id']},
                             {
                                 "$set": {
                                     "FILTER_STATUS": item['status'],
                                     "FILTER_NAME": item['label']
                                 },
                             })


def prepare_criteria(item):

    onco_tree = oncotreenx.build_oncotree(settings.DATA_ONCOTREE_FILE)

    c = {}
    clin_txt_1 = ""
    clin_txt_2_gender = ""
    clin_txt_2_age = ""
    if 'clinical_filter' in item:

        clin_tmp = json.dumps(item['clinical_filter'])
        for key, val in REREPLACEMENTS.items():
            clin_tmp = clin_tmp.replace(key, val)

        c = json.loads(clin_tmp)

        if 'GENDER' in item['clinical_filter']:
            clin_txt_2_gender = item['clinical_filter']['GENDER']

        if 'BIRTH_DATE' in item['clinical_filter']:
            op = item['clinical_filter']['BIRTH_DATE'].keys()[0]
            val = item['clinical_filter']['BIRTH_DATE'].values()[0]

            try:
                val = datetime.datetime.strptime(val.replace(" GMT", ""), '%a, %d %b %Y %H:%M:%S')
            except ValueError:
                val = dateutil.parser.parse(val)

            # compute the age.
            today = datetime.date.today()
            tmp = today.year - val.year - ((today.month, today.day) < (val.month, val.day - 1))
            val = tmp

            if op.count("gte") > 0:
                clin_txt_2_age = "< %s" % val
            else:
                clin_txt_2_age = "> %s" % val

        # parse date-times.
        for key in ['BIRTH_DATE', 'REPORT_DATE']:

            if key not in c:
                continue

            # extract the expression value.
            lkey, lval = c[key].keys()[0], c[key].values()[0]

            try:
                c[key][lkey] = datetime.datetime.strptime(lval.replace(" GMT", ""), '%a, %d %b %Y %H:%M:%S')
            except ValueError:
                c[key][lkey] = dateutil.parser.parse(lval)

        # expand oncotree
        if 'ONCOTREE_PRIMARY_DIAGNOSIS_NAME' in item['clinical_filter']:

            txt = item['clinical_filter']['ONCOTREE_PRIMARY_DIAGNOSIS_NAME']

            if txt == "_LIQUID_" or txt == "_SOLID_":

                node1 = oncotreenx.lookup_text(onco_tree, "Lymph")
                node2 = oncotreenx.lookup_text(onco_tree, "Blood")

                nodes1 = list(nx.dfs_tree(onco_tree, node1))
                nodes2 = list(nx.dfs_tree(onco_tree, node2))
                nodes = list(set(nodes1).union(set(nodes2)))

                if txt == "_SOLID_":

                    all_nodes = set(list(onco_tree.nodes()))
                    tmp_nodes = all_nodes - set(nodes)
                    nodes = list(tmp_nodes)

                clin_txt_1 = "%s cancers" % txt.replace("_", "").title()

            else:

                clin_txt_1 = "%s" % txt
                node = oncotreenx.lookup_text(onco_tree, txt)
                if onco_tree.has_node(node):
                    nodes = list(nx.dfs_tree(onco_tree, node))

            nodes_txt = [onco_tree.node[n]['text'] for n in nodes]
            c['ONCOTREE_PRIMARY_DIAGNOSIS_NAME'] = {'$in': nodes_txt}

    g = {}
    gen_txt = []
    if 'genomic_filter' in item:

        gen_tmp = json.dumps(item['genomic_filter'])
        for key, val in REREPLACEMENTS.items():
            gen_tmp = gen_tmp.replace(key, val)

        g = json.loads(gen_tmp)

        # add TRUE_HUGO_SYMBOL value mutational signature filter queries
        if 'TRUE_HUGO_SYMBOL' in g and g['TRUE_HUGO_SYMBOL'] == {'$in': ['']}:
            g['TRUE_HUGO_SYMBOL'] = None

        sv_test = False
        mut_test = False
        cnv_test = False
        if 'VARIANT_CATEGORY' in item['genomic_filter']:
            variant_category = item['genomic_filter']['VARIANT_CATEGORY']
            if isinstance(variant_category, dict):
                for x in variant_category.values():
                    if "SV" in set(x):
                        sv_test = True
                    if "CNV" in set(x):
                        cnv_test = True
                    if "MUTATION" in set(x):
                        mut_test = True

            elif item['genomic_filter']['VARIANT_CATEGORY'] == 'SV':
                sv_test = True

            elif item['genomic_filter']['VARIANT_CATEGORY'] == 'CNV':
                cnv_test = True

            elif item['genomic_filter']['VARIANT_CATEGORY'] == 'MUTATION':
                mut_test = True

        # build text.
        exon_txt = ""
        protein_txt = ""
        if mut_test:
            gen_txt.append("Mutation")

            if 'TRUE_EXON_CHANGE' in item['genomic_filter']:
                exon_txt = item['genomic_filter']['TRUE_EXON_CHANGE']

            if 'TRUE_PROTEIN_CHANGE' in item['genomic_filter']:
                protein_txt = item['genomic_filter']['TRUE_PROTEIN_CHANGE']

        if cnv_test:
            if 'CNV_CALL' in g:
                if isinstance(g['CNV_CALL'], dict):
                    gen_txt += g['CNV_CALL'].values()[0]
                else:
                    gen_txt.append(g['CNV_CALL'])
        if sv_test:
            gen_txt.append("Structural rearrangement")

        if 'MMR_STATUS' in item['genomic_filter']:
            gen_txt.append(item['genomic_filter']['MMR_STATUS'])

        if 'TABACCO_STATUS' in item['genomic_filter']:
            gen_txt.append('Tobacco Mutational Signature')

        if 'TEMOZOLOMIDE_STATUS' in item['genomic_filter']:
            gen_txt.append('Temozolomide Mutational Signature')

        if 'POLE_STATUS' in item['genomic_filter']:
            gen_txt.append('PolE Mutational Signature')

        if 'APOBEC_STATUS' in item['genomic_filter']:
            gen_txt.append('APOBEC Mutational Signature')

        if 'UVA_STATUS' in item['genomic_filter']:
            gen_txt.append('UVA Mutational Signature')

        clauses = []
        if mut_test:

            clause = {
                'VARIANT_CATEGORY': 'MUTATION',
                'TRUE_HUGO_SYMBOL': g['TRUE_HUGO_SYMBOL']
            }

            if 'WILDTYPE' in g:
                clause['WILDTYPE'] = g['WILDTYPE']

            if 'TRUE_PROTEIN_CHANGE' in g:
                clause['TRUE_PROTEIN_CHANGE'] = g['TRUE_PROTEIN_CHANGE']

            clauses.append(clause)

        if cnv_test:

            clause = {
                'VARIANT_CATEGORY': 'CNV',
                'TRUE_HUGO_SYMBOL': g['TRUE_HUGO_SYMBOL'],
            }

            if 'CNV_CALL' in g:
                clause['CNV_CALL'] = g['CNV_CALL']

            if 'WILDTYPE' in g:
                clause['WILDTYPE'] = g['WILDTYPE']

            clauses.append(clause)

        if sv_test:

            true_hugo = item['genomic_filter']['TRUE_HUGO_SYMBOL']

            if isinstance(true_hugo, dict):
                genes = true_hugo.values()[0]
            else:
                genes = [true_hugo]

            to_add = list()
            for gene in genes:
                if gene in synonyms:
                    to_add += synonyms[gene]

            genes = genes + to_add

            sv_clauses = []
            for gene in genes:
                abc = "(.*\W%s\W.*)|(^%s\W.*)|(.*\W%s$)" % (gene, gene, gene)
                sv_clauses.append(re.compile(abc, re.IGNORECASE))

            clause = {
                'STRUCTURAL_VARIANT_COMMENT': {"$in": sv_clauses}
            }
            clauses.append(clause)

        if len(clauses) > 0:
            g = {
                "$or": clauses
            }

        for key in item['genomic_filter']:

            special_clauses = {
                'STRUCTURAL_VARIANT_COMMENT',
                'VARIANT_CATEGORY',
                'TRUE_HUGO_SYMBOL',
                'CNV_CALL',
                'WILDTYPE',
                'TRUE_PROTEIN_CHANGE'
            }
            if key in special_clauses:
                continue

            g[key] = item['genomic_filter'][key]

        get_recursively(g, "GMT")
        if 'TRUE_HUGO_SYMBOL' in item['genomic_filter']:
            if isinstance(item['genomic_filter']['TRUE_HUGO_SYMBOL'], dict):
                genes = item['genomic_filter']['TRUE_HUGO_SYMBOL'].values()[0]
            else:
                genes = [item['genomic_filter']['TRUE_HUGO_SYMBOL']]

            genes = [str(i) for i in genes]
            genes = ', '.join(genes)

            if len(gen_txt) > 1:
                gen_txt = "%s: %s" % (genes, ', '.join(gen_txt))
            else:

                if exon_txt == "" and protein_txt == "":
                    gen_txt = "%s %s" % (genes, ', '.join(gen_txt))
                elif exon_txt != "":
                    gen_txt = "%s exon %s" % (genes, exon_txt)
                else:
                    gen_txt = "%s %s" % (genes, protein_txt)

    return c, g, (gen_txt, [clin_txt_1, clin_txt_2_age, clin_txt_2_gender])
