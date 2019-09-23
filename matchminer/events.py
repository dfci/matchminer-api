# imports
import time
import json
import logging
import datetime
from bson import ObjectId
from rfc822 import formatdate

from flask import abort, Response, request
from flask import current_app as app

from matchminer.hooks import UtilHooks
from matchminer import database
from matchminer import data_model
from matchminer import miner
from matchminer import settings
from matchminer import utilities
from matchminer.utilities import REPLACEMENTS, get_data_push_id
from trial_search import Summary, Autocomplete

from tcm.engine import CBioEngine
from matchengine.engine import MatchEngine
from matchminer.templates.emails import emails

# logging
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', )


def clean_filter(items):

    # loop over each validated item.
    for item in items:

        if 'clinical_filter' in item:

            # replace clinical.
            clin_tmp = json.dumps(item['clinical_filter'])
            for key, val in REPLACEMENTS.items():
                clin_tmp = clin_tmp.replace(key, val)
            item['clinical_filter'] = json.loads(clin_tmp)

            for key in item['clinical_filter'].keys():
                if item['clinical_filter'][key] is None:
                    del item['clinical_filter'][key]

        if 'genomic_filter' in item:

            # replace genomic
            gen_tmp = json.dumps(item['genomic_filter'])
            for key, val in REPLACEMENTS.items():
                gen_tmp = gen_tmp.replace(key, val)
            item['genomic_filter'] = json.loads(gen_tmp)

            for key in item['genomic_filter'].keys():
                if item['genomic_filter'][key] is None:
                    del item['genomic_filter'][key]


def replace_match(item, original):
    """
    There is a field called _new_match that counts the number of new matches created by a CAMD
    status POST. Set this field here to avoid counting any matches that have been manually
    moved to the new bin by a user.
    """
    if 'MATCH_STATUS' in item and item['MATCH_STATUS'] == 0 and original['MATCH_STATUS'] != 0:
        item['_new_match'] = True

    return item


def find_match(items):
    """ computes matches and saves results.
    called after insertion in DB is complete

    :param items: dict
    """

    db = app.data.driver.db
    cbio = CBioEngine(settings.MONGO_URI,
                      settings.MONGO_DBNAME,
                      data_model.match_schema,
                      muser=settings.MONGO_USERNAME,
                      mpass=settings.MONGO_PASSWORD,
                      collection_clinical=settings.COLLECTION_CLINICAL,
                      collection_genomic=settings.COLLECTION_GENOMIC)

    for item in items:

        c, g, txt = miner.prepare_criteria(item)
        gen_txt, clin_txt = txt
        cancer, age, gender = clin_txt

        c_test = cancer == ""
        g_test = gender == ""
        a_test = age == ""

        if not c_test:
            description = "%s in %s" % (gen_txt, cancer)
        else:
            description = gen_txt

        if not g_test and a_test:
            description = "%s, Gender: %s" % (description, gender)

        elif not g_test and not a_test:
            description = "%s, Gender: %s, Age %s" % (description, gender, age)

        elif g_test and not a_test:
            description = "%s, Age %s" % (description, age)

        if isinstance(description, list) and len(description) == 0:
            description = ''

        query = {"_id": item["_id"]}
        update = {"$set": {"description": description}}
        _ = db.filter.update_one(query, update)
        item['description'] = description

        # only recompute match if there was an update.
        updated = miner.detect_update(cbio, item)
        if updated:
            miner.remove_matches(cbio, item)
            cbio.match(c=c, g=g)
            miner.count_matches(cbio, item)
            dpi = get_data_push_id(db)
            if not item["temporary"]:
                miner.insert_matches(cbio, item, dpi=dpi)

        else:
            # pass along status variable to matches.
            miner.update_match_status(cbio, item)


def align_matches_genomic(a):

    # short circuit.
    if len(a['_items']) == 0:
        return

    # get the user.
    if settings.NO_AUTH:
        logging.info("NO AUTH enabled. align_matches_genomic")
        accounts = app.data.driver.db['user']
        user = accounts.find_one({"last_name": "Doe"})
    else:
        user = app.auth.get_request_auth_value()

    # extract the clinical id.
    clinical_id = a['_items'][0]['CLINICAL_ID']

    # lookup any matches.
    cbio = CBioEngine(settings.MONGO_URI,
                      settings.MONGO_DBNAME,
                      data_model.match_schema,
                      muser=settings.MONGO_USERNAME,
                      mpass=settings.MONGO_PASSWORD,
                      collection_clinical=settings.COLLECTION_CLINICAL,
                      collection_genomic=settings.COLLECTION_GENOMIC)

    match_db = cbio.connection[cbio.mongo_dbname]['match']
    filter_db = cbio.connection[cbio.mongo_dbname]['filter']

    variants = dict()
    for match in match_db.find({"CLINICAL_ID": clinical_id}):
        for variant_id in match['VARIANTS']:
            if variant_id not in variants:
                variants[variant_id] = list()

            variants[variant_id].append(match['FILTER_ID'])

    for item in a['_items']:
        if item['_id'] in variants:
            for filter_id in variants[item['_id']]:

                filter_doc = filter_db.find_one(filter_id)
                if filter_doc is None:
                    continue

                # check status.
                if filter_doc['status'] != 1:
                    continue

                # check ownership.
                if filter_doc['TEAM_ID'] not in set(user['teams']):
                    continue

                # embed this in filter.
                if 'FILTER' not in item:
                    item['FILTER'] = list()

                item['FILTER'].append(filter_doc)

        # merge genetic event with cytoband
        if 'GENETIC_EVENT' in item and 'CYTOBAND' in item and item['GENETIC_EVENT'] is not None:
            item['CYTOBAND'] = '%s %s' % (item['CYTOBAND'], item['GENETIC_EVENT'])


def align_matches_clinical(a):

    # extract the clinical id.
    clinical_id = a['_id']

    # lookup any matches.
    match_db = database.get_collection("match")
    filter_db = database.get_collection("filter")

    # loop through the match and build dictionary.
    matches = set()
    enrolled = set()
    for match in match_db.find({"CLINICAL_ID": clinical_id}):

        # build lookup.
        matches.add(match['FILTER_ID'])

        # check if the match is enrolled.
        if match['MATCH_STATUS'] == 4:
            enrolled.add(match['FILTER_ID'])

    # grab all filters.
    filters = list()
    for filter_id in matches:

        # get filter.
        filter = filter_db.find_one(filter_id)

        # save it to list.
        filters.append(filter)

    # embed in object.
    a['FILTER'] = filters
    a['ENROLLED'] = list(enrolled)


def sort_trial_matches(resource):
    """
    In Matchengine V2, the sort order field is an array which delivers each dimension of the sort as an index.
    This function will sort each protocol's match reasons according to this criteria:

    MMR > Tier 1 > Tier 2 > CNV > Tier 3 > Tier 4 > wild type
    Variant-level  > gene-level
    Exact cancer match > all solid/liquid
    Co-ordinating center: DFCI > others
    Reverse protocol number: high > low

    There is also a field show_in_ui which determines whether a match document
    is viewable in the UI.
    """
    current_rank = 0
    seen_protocol_nos = dict()
    if resource['_items'] and isinstance(resource['_items'][0]['sort_order'], list):
        resource['_items'] = sorted(resource['_items'], key=lambda x: (tuple(x['sort_order'][:-1]) + (1.0 / x['sort_order'][-1],)))
        for item in resource['_items']:
            if item['protocol_no'] not in seen_protocol_nos:
                if any(map(lambda x: x < 0, item['sort_order'])):
                    seen_protocol_nos[item['protocol_no']] = -1
                else:
                    seen_protocol_nos[item['protocol_no']] = current_rank
                    current_rank += 1
            item['sort_order'] = seen_protocol_nos[item['protocol_no']]


def align_other_clinical(a):

    # extract the clinical id.
    clinical_id = a['_id']

    # lookup any matches.
    cbio = CBioEngine(settings.MONGO_URI, settings.MONGO_DBNAME, data_model.match_schema, muser=settings.MONGO_USERNAME, mpass=settings.MONGO_PASSWORD,
                 collection_clinical=settings.COLLECTION_CLINICAL, collection_genomic=settings.COLLECTION_GENOMIC)
    clinical_db = cbio._c


    # look for record with sample MRN.
    related = list(clinical_db.find({"MRN": a['MRN']}))

    # remove self.
    tmp = []
    for clinical in related:

        for nm in ["FIRST_NAME", "LAST_NAME", "FIRST_LAST", "LAST_FIRST"]:
            del clinical[nm]

        if clinical['_id'] == a['_id']:
            continue
        tmp.append(clinical)

    # add them to record.
    a['RELATED'] = tmp

    # remove patient name
    for nm in ["FIRST_NAME", "LAST_NAME", "FIRST_LAST", "LAST_FIRST"]:
        del a[nm]


def align_enrolled(resp):

    # build list of clinical_ids
    clin_ids = set()
    for item in resp['_items']:
        if isinstance(item['CLINICAL_ID'], dict):
            clin_ids.add(item['CLINICAL_ID']['_id'])
        else:
            clin_ids.add(item['CLINICAL_ID'])

    # get only clincal id for matched subset.
    match_db = database.get_collection("match")
    matched_ids = set()
    for match in match_db.find({"MATCH_STATUS": 4, "CLINICAL_ID": {"$in": list(clin_ids)}}, {"CLINICAL_ID": 1}):
        matched_ids.add(match['CLINICAL_ID'])

    # lookup any matches.
    for item in resp['_items']:
        id = None
        if isinstance(item['CLINICAL_ID'], dict):
            id = item['CLINICAL_ID']['_id']
        else:
            id = item['CLINICAL_ID']

        if id in matched_ids:
            item['ENROLLED'] = True
        else:
            item['ENROLLED'] = False


def clean_filter_updated(item, original):

    # copy hash to new item.
    og_obj = app.data.driver.db['filter'].find_one({'_id': item['_id']})
    item['filter_hash'] = og_obj['filter_hash']

    # just call clean filter.
    clean_filter([item])


def update_filter(item, original):

    # just call find_match
    find_match([item])


def strip_metavars(resource, item, original):
    """ strips out all meta variables from a PUT request

    :param resource:
    :param item:
    :param original:
    """

    for key in item.keys():
        if key[0] == "_" and key != "_id":
            del item[key]


def hipaa_logging_resource(resource, response):

    if resource == 'trial' or resource == 'public_stats':
        return

    for item in response['_items']:
        hipaa_logging_item(resource, item)


def hipaa_logging_item(resource, response):

    if resource == 'response':
        return

    # get the user_id.
    db = app.data.driver.db
    if app.auth is None:
        logging.warning('Skipping HIPAA logging')
        return
    user = app.auth.get_request_auth_value()

    # set loggable user_name.
    user_name = user['user_name']

    if user_name == 'cbioone':
        return

    # deal with clinical.
    needs_it = False
    if resource == 'clinical':

        # fetch loggable patient id.
        patient_name = response['MRN']
        needs_it = True

    elif resource == 'match':

        # fetch the clinical_id
        clinical_id = response['CLINICAL_ID']

        # determine if it was resolved.
        if isinstance(clinical_id, dict):
            patient_name = clinical_id['MRN']

        else:
            clinical = db['clinical'].find_one({'_id': ObjectId(clinical_id)})
            patient_name = clinical['MRN']

        needs_it = True

    # determine if we insert.
    if needs_it:

        # dertermine keys.
        phi_list = list()
        for x in response.keys():
            if x[0] == '_':
                continue
            phi_list.append(x)

        # create entry.
        dt = datetime.datetime.now()
        transaction = {
            'user_id': user_name,
            'patient_id': patient_name,
            'phi': phi_list,
            'reason': 'MatchMiner - Clinical Trial matching',
            'timestamp': dt,
            app.config['LAST_UPDATED']: dt,
            app.config['DATE_CREATED']: dt
        }

        # insert it.
        app.data.insert('hipaa', transaction)

def clinical_insert(items):

    # get database lookup.
    clinical_db = app.data.driver.db['clinical']

    # modify each item.
    keepers = list()
    for item in items:

        # make updated names
        item['FIRST_LAST'] = item['FIRST_NAME'] + " " + item['LAST_NAME']
        item['LAST_FIRST'] = item['LAST_NAME'] + " " + item['FIRST_NAME']

        # extract sample id
        sample_id = item['SAMPLE_ID']
        logging.info("Adding clinical data for sample id " + str(sample_id))

        # check for existing sample_id.
        clinical = clinical_db.find_one({'SAMPLE_ID': sample_id})

        # if none then its a new person.
        if clinical is None:
            keepers.append(item)
            continue

        # this is really just a PUT in disguise!
        #app.data.update(item)


def clinical_delete(item):

    # get database lookup.
    genomic_db = app.data.driver.db['genomic']
    match_db = app.data.driver.db['match']

    # delete associated genomic entries.
    genomic_db.delete_many({"CLINICAL_ID": ObjectId(item['_id'])})

    # delete associated matches.
    match_db.delete_many({"CLINICAL_ID": ObjectId(item['_id'])})


def genomic_insert(items):
    # modify each item.
    for item in items:

        # set strings to be object ids
        item['CLINICAL_ID'] = ObjectId(item['CLINICAL_ID'])


def clinical_replace(item, original):

    # call the insert event.
    clinical_insert([item])

    # remove matches for entries that move VITAL_STATUS to deceased
    assess_vital_status(item, original)


def clinical_update(update, original):
    """Remove matches for entries that move VITAL_STATUS to deceased"""
    assess_vital_status(update, original)


def assess_vital_status(update, original):
    """If a patient's VITAL STATUS has been changed to deceased, remove their matches from the database"""

    db = database.get_db()
    if 'VITAL_STATUS' in update and update['VITAL_STATUS'] == 'deceased' and original['VITAL_STATUS'] == 'alive':
        db['match'].remove({'CLINICAL_ID': original['_id']})


def status_insert(items):
    """
    Re runs all filters (created in UI)
    :param items:
    :return:
    """

    # loop over each item.
    for item in items:

        # log this.
        logging.info("recieved pre-status post")

        # this is the unique data push id to be assigned to all matches
        dpi = None
        if 'data_push_id' in item and item['data_push_id']:
            dpi = item['data_push_id']

        # re-run all filters.
        miner.rerun_filters(dpi)

        # adds a row to the MatchMiner Stats dashboard datatable for the new CAMD update
        if not item['silent']:
            add_dashboard_row(item)


def add_dashboard_row(status):
    """Updates the dashboard MatchMiner stats table"""

    # get records
    db = database.get_db()
    clinical = list(db['clinical'].find())
    users = list(db['user'].find())
    filters = list(db['filter'].find({'temporary': False, 'status': 1}))

    # allow for users without a "last_auth" entry
    for user in users:
        if 'last_auth' not in user:
            user['last_auth'] = None
        else:
            user['last_auth'] = user['last_auth'].replace(tzinfo=None)

    # calculate MatchMiner stats
    three_months_ago = datetime.datetime.today() - datetime.timedelta(days=90)
    num_samples = len(set(item['SAMPLE_ID'] for item in clinical if 'SAMPLE_ID' in item))
    num_patients = len(set(item['MRN'] for item in clinical if 'MRN' in item))
    active_users = list(item for item in users if item['last_auth'] and item['last_auth'] >= three_months_ago)
    inactive_users = list(item for item in users if not item['last_auth'] or item['last_auth'] < three_months_ago)

    # exclude ksg team members
    active_users = utilities.exclude_ksg(active_users)
    inactive_users = utilities.exclude_ksg(inactive_users)

    # sort users by activity
    active_users.sort(reverse=True)
    inactive_users.sort(reverse=True)

    # update the dashboard
    db['statistics'].update_one({}, {
        '$push': {
            'mm_data_set': [
                status['last_update'].strftime("%Y-%m-%d"),
                num_patients,
                num_samples,
                status['new_clinical'],
                len(active_users),
                len(filters)
            ]
        },
        '$set': {
            'active_filter_data_set': calculate_filter_stats(filters, db),
            'active_user_data_set': [
                [
                    utilities.get_user_name(user),
                    utilities.get_user_role(user),
                    _determine_login(user, True)
                ]
                for user in active_users
            ],
            'inactive_user_data_set': [
                [
                    utilities.get_user_name(user),
                    utilities.get_user_role(user),
                    _determine_login(user, True)
                ]
                for user in inactive_users
            ]
        }
    }, upsert=True)

    # convert old dates
    statistics = (db.statistics.find())
    for doc in statistics:
        mm_data_set = utilities.convert_old_dates(doc)
        db.statistics.update_one(
            {"_id": doc["_id"]},
            {"$set": {"mm_data_set": mm_data_set}}
        )


def calculate_filter_stats(filters, db):
    """Calculates stats for the dashboard active filter stats table"""

    filter_stats = []
    for filt in filters:
        filter_owner = db['user'].find_one({'_id': filt['USER_ID']})
        matches = list(db['match'].find({'FILTER_ID': filt['_id']}))

        # allow for missing fields
        if 'label' not in filt:
            filt['label'] = ''
        if 'description' not in filt:
            filt['description'] = ''
        if not filter_owner:
            filter_owner = {'first_name': '', 'last_name': ''}
        elif 'first_name' not in filter_owner:
            filter_owner['first_name'] = ''
        elif 'last_name' not in filter_owner:
            filter_owner['last_name'] = ''

        # limit filter description to 80 characters
        if len(filt['description']) > 80:
            filt['description'] = filt['description'][:80] + '...'

        # excluce KSG team members
        user_name = '%s %s' % (filter_owner['first_name'], filter_owner['last_name'])
        if user_name.replace(' ', '_') in settings.EXCLUDE_FROM_STATISTICS:
            continue

        filter_stats.append([
            _determine_activity_level(matches, db),
            user_name,
            _determine_login(filter_owner),
            filt['label'],
            filt['description'],
            len([match for match in matches if match['MATCH_STATUS'] == 0]),
            len([match for match in matches if match['MATCH_STATUS'] == 1]),
            len([match for match in matches if match['MATCH_STATUS'] == 2]),
            len([match for match in matches if match['MATCH_STATUS'] == 5]),
            len([match for match in matches if match['MATCH_STATUS'] == 6]),
            len([match for match in matches if match['MATCH_STATUS'] == 7]),
            len([match for match in matches if match['MATCH_STATUS'] == 3]),
            len([match for match in matches if match['MATCH_STATUS'] == 4])
        ])

    # sort by activity
    filter_stats.sort(key=lambda x: x[1], reverse=True)

    return filter_stats


def _allow_null_dt(dt, time_=False):
    """Handles an exception where the last_auth user field is null"""
    if dt:
        if time_:
            return dt.strftime("%Y-%m-%d %H:%M")
        else:
            return dt.strftime("%Y-%m-%d")
    else:
        return None


def _determine_activity_level(matches, db):
    """Handles instances where the "_updated" field is not set"""
    try:
        activity = db['match'].find_one({'_id': {'$in': [match['_id'] for match in matches]}}, sort=[("_updated", -1)])
        if activity:
            return _allow_null_dt(activity['_updated'])
        else:
            return None
    except KeyError:
        return None


def _determine_login(user, time_=False):
    """Handles instances where the "last_auth" field is not set"""
    try:
        return _allow_null_dt(user['last_auth'], time_)
    except KeyError:
        return None


def flatten_json(y):
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[str(name[:-1])] = str(x)

    flatten(y)
    return out


def insert_data_genomic(data_dict, tree_node, node_id):

    # deal with other genomics
    for key, val in tree_node.items():

        # dont need to compress this.
        if key == "wildtype":
            continue

        # modify to special wildtype facet
        if 'wildtype' in tree_node and key == "hugo_symbol":
            key = "wildtype_%s" % key
            val = "wt %s" % val

        # bootstrap
        if key not in data_dict:
            data_dict[key] = []

        # search for key.
        found = False
        for x in data_dict[key]:
            if x['value'] == val:
                x['id'].append(node_id)
                found = True
                break

        # add value to dictionary.
        if not found:
            data_dict[key].append({'value': val, 'id': [node_id]})


def insert_data_clinical(data_dict, tree_node, node_id):

    # loop over every value.
    for key, val in tree_node.items():

        # bootstrap
        if key not in data_dict:
            data_dict[key] = []

        # search for key
        found = False
        for x in data_dict[key]:
            if x['value'] == val:
                x['id'].append(node_id)
                found = True
                break

        # add value to dictionary.
        if not found:
            data_dict[key].append({'value': val, 'id': [node_id]})


def insert_data_other(trial_tree, node_id, n, other):

    # set valid keys
    valid_keys = {'phase', 'status', 'age'}
    fields = {'site_list': ['site_name', 'coordinating_center'],
              'management_group_list': ['management_group_name', 'is_primary']}
    institute_name = 'Dana-Farber Cancer Institute'
    closed_status = ['Closed to Accrual', 'Suspended', 'Terminated']

    # add other values
    for key, val in trial_tree.node[n].items():

        # skip hidden.
        if key[0] == '_' or key not in valid_keys:
            continue

        # bootstrap
        if key not in other:
            other[key] = []

        # search for key
        found = False
        for x in other[key]:
            if x['value'] == val:
                x['id'].append(node_id)
                found = True
                break

        # add it otherwise.
        if not found:
            other[key].append({'value': val, 'id': [node_id]})

    # populate disease center and Study Site (special because only once)
    for key in fields:
        try:
            val = trial_tree.node[n][key].keys()[0]
            # iterate through the list
            for name in trial_tree.node[n][key][val]:
                # check if primary site or coordinating center
                if name[fields[key][1]] == 'N':
                    continue
                value = name[fields[key][0]]
                other[val] = [{'value': value, 'id': [node_id]}]
        except KeyError:
            pass

    # Get Dana Farber accrual status. Overrides overall status, unless overall status is closed.
    try:
        site_status = ''
        for sites in trial_tree.node[n]['site_list']['site']:
            site_name = sites['site_name']
            if site_name == institute_name:
                site_status = sites['site_status']

        if other['status'] not in closed_status and site_status != '':
            other['status'] = [{'value': site_status, 'id': [node_id]}]
    except KeyError:
        pass

    # populate Drug names
    try:
        if trial_tree.node[n]['drug_list']:
            for drugs in trial_tree.node[n]['drug_list']['drug']:
                if 'drug' not in other:
                    other['drug'] = []
                other['drug'].append({'value': drugs['drug_name'], 'id': node_id})
    except KeyError:
        pass


def trial_replace(item, original):

    logging.info("trial updated %s" % item['protocol_no'])
    trial_insert([item])


def trial_insert(items):

    # get database connection.
    db = database.get_db()

    # loop over each item.
    for item in items:

        # build tree.
        me = MatchEngine(db)
        status, trial_tree = me.create_trial_tree(item, no_validate=True)

        # look at every node.
        genomic = {}
        clinical = {}
        other = {}
        for n in trial_tree.nodes():

            # get parent.
            if 'node_id' not in trial_tree.node[n]:
                continue

            node_id = trial_tree.node[n]['node_id']

            # look for multi-level nodes (right now its only match).
            if 'match_tree' in trial_tree.node[n]:
                # compress categories.
                mt = trial_tree.node[n]['match_tree']
                for x in mt:
                    if mt.node[x]['type'] == 'genomic':
                        insert_data_genomic(genomic, mt.node[x]['value'], node_id)
                    if mt.node[x]['type'] == 'clinical':
                        insert_data_clinical(clinical, mt.node[x]['value'], node_id)

            # add the other nodes.
            insert_data_other(trial_tree, node_id, n, other)

        # create _summary, _suggest, and _elasticsearch fields
        summary = Summary(clinical, genomic, other, trial_tree)
        item['_summary'] = summary.create_summary(item)

        autocomplete = Autocomplete(item)
        item['_suggest'], item['_elasticsearch'], item['_summary']['primary_tumor_types'] = \
            autocomplete.add_autocomplete()

        logging.info("trial inserted " + item['protocol_no'])
    return items


def status_replaced(item, original):

    # check if its a pre-or-post status.
    if item['pre']:
        abort(422, "Not allowed to UPDATE status which isn't pre=False")

    # log this.
    logging.info("received update status")

    # this is the unique data push id to be assigned to all matches
    dpi = None
    if 'data_push_id' in item and item['data_push_id']:
        dpi = item['data_push_id']

    # re-run all filters.
    miner.rerun_filters(dpi)

    # trigger email.
    if not item['silent']:
        miner.email_matches()
    else:
        logging.info("status post was silent, no email sent")


def status_delete(item):

    # log this.
    logging.info("recieved delete status")

    # restore the backup.
    utilities.backup_restore(item['backup_path'])


def team_restricted_item(item):

    # get the requesting user and item team.
    user = app.auth.get_request_auth_value()
    team_id = item['TEAM_ID']

    # check if team_id in user team_set
    valid = False
    if team_id in set(user['teams']):
        valid = True

    # abort this request.
    if not valid:
        abort(404)


def pre_get_restricted(request, lookup):

    # get the requesting user set of teams.
    if app.auth == None:
        # TODO REMOVE THIS HACK
        teams = list(database.get_collection('team').find())
    else:
        teams = set(app.auth.get_request_auth_value()['teams'])

    # parse the query string.
    where_clause = request.args.get("where")
    if where_clause:

        # parse the value.
        clause = json.loads(where_clause)

        # check if a team_id is set.
        query_teams = False
        if 'TEAM_ID' in clause:

            # check if it is legit.
            if isinstance(clause['TEAM_ID'], dict):
                team_list = clause['TEAM_ID'].values()[0]
            else:
                team_list = [clause['TEAM_ID']]

            for team in team_list:
                if ObjectId(team) not in teams:

                    # emit a 404 because someone is cheating.
                    abort(404)

            # mark it as present.
            query_teams = True

        # TEAM_ID isn't present, complain.
        if not query_teams:

            resp = Response(None, 406)
            abort(406, description='Resource requires TEAM_ID to be specified in where clause', response=resp)


def update_response(item):

    if 'allow_update' not in item or not item['allow_update']:
        abort(501)

    bin_key = settings.match_status_mapping
    db = database.get_db()

    # add time_clicked and ip_address to response
    db['response'].update_one(
        {'_id': item['_id']},
        {'$set': {
            'time_clicked': formatdate(time.mktime(datetime.datetime.now().timetuple())),
            'ip_address': _get_ip()
        }}
    )

    # Get match from match table
    match_db = db['match']
    match = match_db.find_one({'_id': item['match_id']})
    patient = db['clinical'].find_one({'_id': match['CLINICAL_ID']})

    # get clinician response
    status = item['match_status']

    # get new status
    new_status = bin_key[status]

    # Update match status
    result = match_db.update_one(
        {"_id": item["match_id"]},
        {"$set": {
            "MATCH_STATUS": new_status,
            "_updated": datetime.datetime.utcnow().replace(microsecond=0)
        }}
    )

    if status == 'Eligible' or status == 'Deferred':
        # get the filter owner
        user_db = db['user']
        filter_owner = user_db.find_one({'_id': item['notification_id']})

        # get filter
        filter_name = match['FILTER_NAME']

        # get the list of matched variant
        variant = []
        genomic_db = db['genomic']
        for v in match['VARIANTS']:
            variant.extend(list(genomic_db.find({'_id': v})))

        email_filter_owner(filter_owner, patient, filter_name, variant, status)

    elif status == 'Not Eligible' or status == 'Deceased':
        email_matchminer(patient, status)


def email_matchminer(patient, status):
    """Emails the matchminer service email account to keep track of physician responses to the email blast"""

    cur_stamp = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")

    html = '''<html><head></head><body>%s</body></html>''' % emails.EMAIL_BLAST_RESPONSE_BODY.format(
        patient['ORD_PHYSICIAN_NAME'],
        patient['FIRST_NAME'],
        patient['LAST_NAME'],
        patient['MRN'],
        status,
        cur_stamp
    )

    # put email object in db
    db = database.get_db()
    email_item = {
        'email_from': settings.EMAIL_AUTHOR_PROTECTED,
        'email_to': settings.EMAIL_AUTHOR_PROTECTED,
        'subject': 'Email Blast Response',
        'body': html,
        'cc': [],
        'sent': False,
        'num_failures': 0,
        'errors': []
    }
    db['email'].insert(email_item)


def _get_ip():
    """Returns the IP address if it can."""
    try:
        return request.remote_addr
    except RuntimeError:
        return 'NoIP'


def get_alterations(variant):
    # get the alteration
    genomic = variant[0]
    if genomic['VARIANT_CATEGORY'] == 'MUTATION':
        if 'TRUE_PROTEIN_CHANGE' in genomic and genomic['TRUE_PROTEIN_CHANGE'] is not None:
            alteration = "%s %s mutation" % (genomic['TRUE_HUGO_SYMBOL'], genomic['TRUE_PROTEIN_CHANGE'].replace("p.", ""))
        else:
            alteration = "%s mutation" % (genomic['TRUE_HUGO_SYMBOL'])

    elif genomic['VARIANT_CATEGORY'] == 'CNV':
        alteration = "%s %s" % (genomic['TRUE_HUGO_SYMBOL'], genomic['CNV_CALL'].lower())

    else:
        alteration = "structural re-arrangement"
    return alteration


def email_filter_owner(user, patient, filter_name, variant, status):

    if variant:
        alteration = get_alterations(variant)
    else:
        alteration = 'unknown'

    cur_stamp = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
    html = _user_email_filter_owner(user, patient, alteration, status, cur_stamp)

    subject = '%s : Patient %s' % (filter_name, status)
    author = settings.EMAIL_AUTHOR_PROTECTED

    # put email object in db
    db = database.get_db()
    email_item = {
        'email_from': author,
        'email_to': user['email'],
        'subject': subject,
        'body': html,
        'cc': settings.EMAIL_TRIAL_CC_LIST,
        'sent': False,
        'num_failures': 0,
        'errors': []
    }
    db['email'].insert(email_item)


def email_user(items):

    # skip unless production.
    if settings.WELCOME_EMAIL != "YES":
        logging.debug("welcome email skipped")
        return

    # loop over each user.
    for user in items:

        # do not email users not approved by Susan
        if user['user_name'] == '':
            continue

        # generate email.
        recipient_email = user['email']

        # create the message.
        cur_date = datetime.date.today().strftime("%B %d, %Y")
        cur_stamp = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")

        # generate text
        html = _user_email_text(user, cur_date, cur_stamp)

        db = database.get_db()
        email_item = {
            'email_from': settings.EMAIL_AUTHOR_PROTECTED,
            'email_to': recipient_email,
            'subject': 'Welcome to MatchMiner - %s' % cur_date,
            'body': html,
            'cc': [],
            'sent': False,
            'num_failures': 0,
            'errors': []
        }
        db['email'].insert(email_item)


def _user_email_text(user, cur_date, cur_stamp):
    html = '''<html><head></head><body>%s</body></html>''' % emails.ACCOUNT_APPROVAL_BODY.format(
        user['first_name'],
        user['last_name'],
        cur_stamp
    )
    return html


def _user_email_filter_owner(user, patient, alteration, status, cur_stamp):
    html = '''<html><head></head><body>%s</body></html>''' % emails.FILTER_ACTIVITY_BODY.format(
        user['first_name'],
        user['last_name'],
        patient['ORD_PHYSICIAN_NAME'],
        patient['FIRST_NAME'],
        patient['LAST_NAME'],
        patient['MRN'],
        alteration,
        status,
        cur_stamp
    )
    return html


def get_public_stats(resp):
    """Returns the number of clinical trials and the number of patients to the UI"""
    db = database.get_db()
    resp['_items'].append({
        'num_clinical_trials': len(list(db['trial'].distinct('protocol_no'))),
        'num_patients': len(list(db['clinical'].distinct("MRN")))
    })


def negative_genomic(items):
    """
    When "negative_genomic" documents are POSTed, all entries without an exon or codon specified will be marked
    entire_gene: True. All others will be marked entire_gene: False.
    """

    for item in items:

        # pertinent and non-pertinent low coverage types always display exon
        if item['coverage_type'] == 'PLC' or item['coverage_type'] == 'NPLC':
            item['show_exon'] = True

        # pertinent negatives display logic proceeds by roi_type ("Region of interest")
        elif item['coverage_type'] == 'PN':

            if 'roi_type' not in item or item['roi_type'] is None:
                continue

            if item['roi_type'] == 'C':
                item['show_codon'] = True

            elif item['roi_type'] == 'E':
                item['show_exon'] = True

            elif item['roi_type'] == 'R':
                item['show_codon'] = True

            elif item['roi_type'] == 'G':
                item['entire_gene'] = True

            elif item['roi_type'] == 'M':
                item['show_codon'] = True


def hide_name(item):
    """Hides patient name"""
    for i, idx in zip(item['_items'][:], range(len(item['_items']))):
        for nm in ["FIRST_NAME", "LAST_NAME", "FIRST_LAST", "LAST_FIRST"]:
            del i[nm]


def patient_view_post(items):
    """
    This function will check the database and either add or update a document
    tracking the current user with the searched for mrn
    """

    now = datetime.datetime.now()
    iter_dict = {'True': 'num_views_details_list', 'False': 'num_views_match_list'}

    db = database.get_db()
    for item in items:

        nav = iter_dict[str(item['from_details'])]
        not_nav = iter_dict[str(not item['from_details'])]
        user = utilities.get_current_user(settings.NO_AUTH, app)

        # from CTI-mode filter matches
        if 'filter_match' in item and item['filter_match'] is True:
            patient_view = db.patient_view.find_one({
                'user_id': user['_id'],
                'mrn': item['mrn'],
                'filter_label': item['filter_label'],
                'filter_protocol_no': item['filter_protocol_no']
            })

            item['view_date'] = now
            item['requires_manual_review'] = True
            if patient_view is not None:
                db.patient_view.remove({'_id': patient_view['_id']})
                item['user_id'] = patient_view['user_id']
                item['user_first_name'] = patient_view['user_first_name']
                item['user_last_name'] = patient_view['user_last_name']
                item['user_email'] = patient_view['user_email']
                item[nav] = patient_view[nav] + 1
                item[not_nav] = patient_view[not_nav]

                if 'user_user_name' not in patient_view:
                    item['user_user_name'] = user['user_name']
                else:
                    item['user_user_name'] = patient_view['user_user_name']

            else:
                item['user_id'] = user['_id']
                item['user_first_name'] = user['first_name']
                item['user_last_name'] = user['last_name']
                item['user_email'] = user['email']
                item['user_user_name'] = user['user_name']
                item[nav] = 1
                item[not_nav] = 0

        else:
            # from patient search
            patient_view = db.patient_view.find_one({
                'user_id': user['_id'],
                'mrn': item['mrn'],
                'protocol_no': item['protocol_no']
            })

            if patient_view is not None:
                db.patient_view.remove({'_id': patient_view['_id']})
                item['user_id'] = patient_view['user_id']
                item['user_first_name'] = patient_view['user_first_name']
                item['user_last_name'] = patient_view['user_last_name']
                item['user_email'] = patient_view['user_email']
                item[nav] = patient_view[nav] + 1
                item[not_nav] = patient_view[not_nav]
                item['view_date'] = now

                if 'user_user_name' not in patient_view:
                    item['user_user_name'] = user['user_name']
                else:
                    item['user_user_name'] = patient_view['user_user_name']

            else:
                item['user_id'] = user['_id']
                item['user_first_name'] = user['first_name']
                item['user_last_name'] = user['last_name']
                item['user_email'] = user['email']
                item['user_user_name'] = user['user_name']
                item[nav] = 1
                item[not_nav] = 0
                item['view_date'] = now

        if 'from_details' in item:
            del item['from_details']
        if 'filter_match' in item:
            del item['filter_match']


def register_hooks(app):

    # add user.
    app.on_inserted_user += email_user

    # hipaa logging hook.
    app.on_fetched_item += hipaa_logging_item
    app.on_fetched_resource += hipaa_logging_resource

    # hook to populate clinical better.
    app.on_insert_clinical += clinical_insert
    app.on_replace_clinical += clinical_replace
    app.on_update_clinical += clinical_update
    app.on_delete_item_clinical += clinical_delete

    app.on_insert_genomic += genomic_insert

    # register the filter hooks.
    if settings.NO_AUTH is not True:
        app.on_fetched_item_filter += team_restricted_item
        app.on_pre_GET_filter += pre_get_restricted

    app.on_insert_filter += clean_filter
    app.on_replace_filter += clean_filter_updated

    # register the match calling hook.
    app.on_fetched_resource_match += align_enrolled
    if settings.NO_AUTH is not True:
        app.on_fetched_item_match += team_restricted_item
        app.on_pre_GET_match += pre_get_restricted

    app.on_inserted_filter += find_match
    app.on_replaced_filter += update_filter
    app.on_replaced_match += replace_match

    # register the match alignment when getting genomic info.
    app.on_fetched_resource_genomic += align_matches_genomic
    app.on_fetched_item_clinical += align_matches_clinical
    app.on_fetched_item_clinical += align_other_clinical

    # trial match get
    app.on_fetched_resource_trial_match += sort_trial_matches

    # register the status update.
    app.on_insert_status += status_insert

    # hook to split the trial resource
    app.on_insert_trial += trial_insert
    app.on_update_trial += trial_replace
    app.on_replace_trial += trial_replace

    # global value normalization utility.
    app.on_insert += UtilHooks.NormalizeHook.entry_insert
    app.on_replace += UtilHooks.NormalizeHook.entry_replace

    # response hooks
    app.on_fetched_item_response += update_response

    # public stats
    app.on_fetched_resource_public_stats += get_public_stats

    # negative genomic coverage insertion
    app.on_insert_negative_genomic += negative_genomic

    # clinical GET
    app.on_fetched_resource_clinical += hide_name

    # patient view POST
    app.on_insert_patient_view += patient_view_post

    # return the app
    return app
