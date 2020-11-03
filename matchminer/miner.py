import logging
import datetime
import copy

import pandas as pd
from dateutil.relativedelta import relativedelta

from matchminer.templates.emails import emails
from matchminer import settings, database
from matchengine.internals.engine import MatchEngine

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s', )


def rerun_filters(filters=None, do_update=True, datapush_id=None):
    """
    Update all filters, or individual filters accepted as an array of ids
    :param filters: Array of filter IDs or None to run all filters
    :param do_update: When finding matches for temporary filters do not update db
    :param datapush_id: When all filters are rerun as part of the oncopanel datapush,
    flag new matches as 'new' and not 'pending', add datapush ID to matches
    """

    with MatchEngine(
            plugin_dir='./filters_config/plugins',
            protocol_nos=filters,
            match_on_closed=False,
            config='./filters_config/filters_config.json',
            db_name=settings.MONGO_DBNAME,
            match_document_creator_class="DFCIFilterMatchDocumentCreator",
            report_all_clinical_reasons=True,
            trial_match_collection="match",
            chunk_size=5000
    ) as me:
        me.get_matches_for_all_trials()
        if do_update:
            me.update_all_matches()

        run_id = me.run_id.hex
        update = {"data_push_id": datapush_id}

        # set match status to "new" only when running filters as part of
        # new data ingestion
        if datapush_id:
            update["MATCH_STATUS"] = 0

        database.get_collection("match").update_many({"_me_id": run_id}, {"$set": update})
    return me.matches, run_id


def _email_text(user, cur_stamp, new_filter_match_counts):
    """
    Generate email text for notifiying new users about new matches.

    Include per filter match counts.
    :param user:
    :param cur_stamp:
    :param new_filter_match_counts:
    :return:
    """
    matches_per_filter_html = ""
    num_matches_total = 0
    for filter_id in new_filter_match_counts:
        filter = new_filter_match_counts[filter_id]
        num_matches_total += int(filter['num_matches'])
        matches_per_filter_html += f"<tr><td>{filter['num_matches']}</td><td>{filter['label']}</td><td>{filter['protocol_id']}</td></tr>"

    html = emails.FILTER_MATCH_BODY.format(
        user['first_name'],
        user['last_name'],
        num_matches_total,
        len(new_filter_match_counts),
        matches_per_filter_html,
        cur_stamp
    )

    return html.replace('\n', '')


def email_matches(run_id=None):
    """
    Email users about new filter matches
    :param run_id: Array. The ID of the latest matchengine run. If no ID is passed, lookup
    latest from db
    :return:
    """
    logging.info("Searching for users to notify about new filter matches...")
    db = database.get_db()

    # Get latest filter run_id if none is passed
    if run_id is None:
        run_id = list(db.run_log_match.find({}, {'run_id': 1}).sort('_id', -1).limit(1))[0]['run_id']

    if isinstance(run_id, str):
        run_id = [run_id]

    logging.info(f"Filter engine run_id: {' ,'.join(run_id)}")
    team_query = {
        "_me_id": {"$in": run_id},
        "is_disabled": False,
        "FILTER_STATUS": 1,
    }
    teams = list(db.match.find(team_query, {"TEAM_ID": 1}).distinct("TEAM_ID"))
    for team_id in teams:
        filters_new_matches_query = {"TEAM_ID": team_id, "is_disabled": False, "FILTER_STATUS": 1}
        filters_with_new_matches = list(db.match.find(filters_new_matches_query, {"FILTER_ID": 1}).distinct("FILTER_ID"))
        new_filters_match_counts = _get_new_filters_match_counts(team_id, filters_with_new_matches, run_id[0])

        team_members = list(db.user.find({'teams': {'$elemMatch': {'$in': [team_id]}}}))
        for user in team_members:
            if 'silent' in user and user['silent']:
                continue

            cur_date = datetime.date.today().strftime("%B %d, %Y")
            cur_stamp = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
            html = _email_text(user, cur_stamp, new_filters_match_counts)
            logging.info(f"Generated email for {user['email']}")

            email_item = {
                'email_from': settings.EMAIL_AUTHOR_PROTECTED,
                'email_to': user['email'],
                'subject': 'New Patient Matches - %s' % cur_date,
                'body': html,
                'cc': [],
                'sent': False,
                'num_failures': 0,
                'errors': [],
                '_created': datetime.datetime.now(),
                '_me_id': run_id
            }
            db.email.insert(email_item)
    logging.info("DONE")


def _get_new_filters_match_counts(team_id, filters_with_new_matches, run_id):
    """
    Aggregate new filter match counts by team

    :param team_id: Team with associated filters
    :param filters_with_new_matches: List of filter IDs associated with single team
    :return:
    """
    db = database.get_db()
    new_filter_match_counts = {}
    for filter_id in filters_with_new_matches:
        matches_query = {
            "TEAM_ID": team_id,
            "FILTER_ID": filter_id,
            "is_disabled": False,
            "_me_id": run_id
        }
        num_matches = len(list(db.match.find(matches_query, {"_id": 1})))

        if num_matches < 1:
            continue
        else:
            filter_ = list(db.filter.find({'_id': filter_id}))[0]
            new_filter_match_counts[filter_id] = {
                "num_matches": num_matches,
                "description": filter_['description'],
                "label": filter_['label'],
                "protocol_id": filter_['protocol_id']
            }
    return new_filter_match_counts


def transform_filter_to_CTML(items, save=False):
    """
    Transform filters clinical & genomic key objects into CTML.

    This is a placeholder function which is present in order to ensure backwards compatibility
    with UI filter generation.

    Eventually, this function should be removed as CTML ideally would be generated
    correctly in the frontend and saved/sent directly to the filter engine for matching,

    :param save: When calling function explicitly (not part of eve built-in hook), e
    explicitly update filter in db. Usually eve does this automatically
    :param items: List of filters
    :return:
    """

    for item in items:
        # MMR_STATUS should always be on the genomic filter
        if 'clinical_filter' in item and 'MMR_STATUS' in item['clinical_filter']:
            item['genomic_filter']['MMR_STATUS'] = item['clinical_filter']['MMR_STATUS']
            del item['clinical_filter']['MMR_STATUS']

        item['match'] = []
        or_clauses = []
        genomic_and = {}
        if 'genomic_filter' in item:
            genomic_filter = item['genomic_filter']

            multis = []
            for k, v in genomic_filter.items():
                # Skip wildtypes, null values & empty lists
                if k in ['WILDTYPE'] or v is None or (isinstance(v, list) and len(v) == 0):
                    continue

                # Old filters used a custom encoding where keys were nested inside an '^in' key.
                # New filters do not do this anymore, but in case any are leftover,
                # catch and remove.
                elif isinstance(v, dict):
                    if '^in' in v:
                        genomic_and[k] = v['^in']
                        genomic_filter[k] = v['^in']

                    operator = ""
                    op_sign = ""
                    if '^lt' in v and v['^lt'] is not None:
                        operator = '^lt'
                        op_sign = '<'

                    if '^gt' in v and v['^gt'] is not None:
                        operator = '^gt'
                        op_sign = '>'

                    if operator != "" and k == 'ALLELE_FRACTION':
                        if isinstance(v[operator], str) and '.' not in v[operator]:
                            v[operator] = float(v[operator]) / 100
                        genomic_and[k] = op_sign + str(v[operator])

                elif isinstance(v, list) and len(v) == 1:
                    if v[0] is not None and v[0] != "":
                        genomic_and[k] = v[0]

                # multi criteria should be used to create OR criteria later
                elif isinstance(v, list) and len(v) > 1:
                    multis.append(k)
                    pass
                else:
                    genomic_and[k] = v

            # If a user has selected multiple criteria, generate all possible
            # OR CTML nodes. Filter out error clauses later.
            # A user may select multiple genes, variant categories, or multiples
            # of both categories.
            if len(multis) == 1:
                for val in genomic_filter[multis[0]]:
                    or_clause = copy.deepcopy(genomic_and)
                    or_clause[multis[0]] = val
                    or_clauses.append({"genomic": or_clause})
            elif len(multis) == 2:
                for val in genomic_filter[multis[0]]:
                    for i_val in genomic_filter[multis[1]]:
                        or_clause = copy.deepcopy(genomic_and)
                        or_clause[multis[0]] = val
                        or_clause[multis[1]] = i_val
                        or_clauses.append({"genomic": or_clause})
            elif len(multis) == 3:
                for val in genomic_filter[multis[0]]:
                    for i_val in genomic_filter[multis[1]]:
                        for i_i_val in genomic_filter[multis[2]]:
                            or_clause = copy.deepcopy(genomic_and)
                            or_clause[multis[0]] = val
                            or_clause[multis[1]] = i_val
                            or_clause[multis[2]] = i_i_val
                            or_clauses.append({"genomic": or_clause})

        # remove CNV_CALL's when VARIANT_CATEGORY is MUTATION or SV
        for or_clause in or_clauses:
            or_node = or_clause['genomic']
            if 'VARIANT_CATEGORY' in or_node and 'CNV_CALL' in or_node and \
                    (or_node['VARIANT_CATEGORY'] == 'MUTATION' or or_node['VARIANT_CATEGORY'] == 'SV'):
                del or_node['CNV_CALL']

        # remove duplicate nodes
        cleaned_or_clauses = []
        for i in range(len(or_clauses)):
            if or_clauses[i] not in or_clauses[i + 1:]:
                cleaned_or_clauses.append(or_clauses[i])

        clinical_and = {}
        if 'clinical_filter' in item:
            clinical_and = {}
            for (k, v) in item['clinical_filter'].items():
                if v is not None:
                    if k == 'BIRTH_DATE':
                        # TODO remove once filter backfill is complete
                        if 'AGE_NUMERICAL' in item['clinical_filter']:
                            continue
                        operator, integer = transform_date_to_range(v)
                        clinical_and['AGE_NUMERICAL'] = f"{operator}{str(integer)}"
                    elif k == 'AGE_NUMERICAL':
                        operator, difference = transform_age_to_CTML(v)
                        clinical_and[k] = f"{operator}{difference}"
                    else:
                        clinical_and[k] = v

        and_clause = {"and": []}
        and_clause['and'].append({"clinical": clinical_and})

        if genomic_and:
            and_clause['and'].append({"genomic": genomic_and})

        if cleaned_or_clauses:
            and_clause["and"].append({"or": cleaned_or_clauses})

            # If new OR clauses have been generated, remove
            # extra AND clause as it is already included on all OR clauses
            del and_clause['and'][1]

        item['match'] = [and_clause]
        item['description'] = get_filter_description(item)

        if save:
            database.get_collection("filter").replace_one({"_id": item['_id']}, item)


def transform_age_to_CTML(filter_date_obj):
    """
    Transform date object as delivered by UI into valid CTML
    :param filter_date_obj:
    :return:
    """
    operator_map = {
        "^lt": "<",
        "^lte": "<",
        "^gt": ">",
        "^gte": ">="
    }
    operator_raw = list(filter_date_obj.keys())[0]
    operator = operator_map[operator_raw]
    return operator, int(filter_date_obj[operator_raw])


def transform_date_to_range(filter_date_obj):
    """
    Transform a static date into an age operation e.g. 2002-04-18 => >18
    #TODO remove function after filter backfill is completed and all filters upgraded to use AGE_NUMERICAL
    :param filter_date_obj:
    :return:
    """
    current_date = datetime.date.today()
    operator = list(filter_date_obj.keys())[0]
    filter_date = datetime.datetime.strptime(filter_date_obj[operator], '%Y-%m-%dT%H:%M:%S.%fZ')
    year_difference = relativedelta(current_date, filter_date).years
    month_difference = relativedelta(current_date, filter_date).months / 12
    day_difference = relativedelta(current_date, filter_date).days / 30.44 / 12
    difference = int(round(float(year_difference + month_difference + day_difference), 2))

    # ^gt and ^lt should not exist
    operator_map = {
        "^lt": ">",
        "^lte": ">=",
        "^gt": "<",
        "^gte": "<"
    }
    operator = operator_map[operator]
    return operator, difference


def get_filter_description(item):
    """
    Populate description column on filters list page in UI
    :param item:
    :return:
    """
    clinical_filter = item['clinical_filter'] if 'clinical_filter' in item else {}
    genomic_filter = item['genomic_filter'] if 'genomic_filter' in item else {}

    # genomic criteria
    mutational_burden = genomic_filter.get("MMR_STATUS", "")
    exon = f"exon {genomic_filter.get('TRUE_TRANSCRIPT_EXON', '')}" if genomic_filter.get("TRUE_TRANSCRIPT_EXON",
                                                                                          "") else ""
    protein_changes = genomic_filter.get("TRUE_PROTEIN_CHANGE", "")
    if isinstance(protein_changes, list):
        protein_changes = ", ".join(protein_changes)
    mutation_type = genomic_filter.get("VARIANT_CATEGORY", "")
    allele_fraction = genomic_filter.get("ALLELE_FRACTION", None)
    if isinstance(mutation_type, list) and len(mutation_type) > 0:
        mutation_type = ", ".join(mutation_type)
        if 'MUTATION' in mutation_type.upper():
            mutation_type = mutation_type.replace('MUTATION', "Mutation")
        if 'SV' in mutation_type.upper():
            mutation_type = mutation_type.replace('SV', "Structural rearrangement")
        if 'CNV' in mutation_type.upper():
            cnv_calls = ", ".join(genomic_filter.get("CNV_CALL", ""))
            mutation_type = mutation_type.replace('CNV', cnv_calls)
        if 'SIGNATURE' in mutation_type.upper():
            sigs = ['POLE_STATUS', 'TEMOZOLOMIDE_STATUS', 'APOBEC_STATUS', 'TABACCO_STATUS', 'UVA_STATUS']
            for sig in sigs:
                if sig in genomic_filter:
                    if sig == 'TEMOZOLOMIDE_STATUS':
                        mutation_type = sig.replace('_STATUS', '').title()
                    elif sig == 'TABACCO_STATUS':
                        mutation_type = 'Tobacco'
                    elif sig == 'POLE_STATUS':
                        mutation_type = 'PolE'
                    else:
                        mutation_type = sig
                    mutation_type = mutation_type.replace('_STATUS', '') + ' Signature'

    gene = genomic_filter.get("TRUE_HUGO_SYMBOL", "")
    if isinstance(gene, list):
        if len(gene) == 1:
            gene = gene[0]
        elif len(gene) > 1:
            gene = ', '.join(genomic_filter.get("TRUE_HUGO_SYMBOL", [])) + ':'

    # clinical criteria
    cancer = clinical_filter.get("ONCOTREE_PRIMARY_DIAGNOSIS_NAME", "")
    gender = clinical_filter.get("GENDER", "")
    if cancer == "_SOLID_":
        cancer = "Solid cancers"
    elif cancer == "_LIQUID_":
        cancer = "Liquid cancers"
    birth_date = clinical_filter.get("BIRTH_DATE", None) #TODO remove once filter backfill is compelted
    age = clinical_filter.get("AGE_NUMERICAL", None)
    if birth_date and age is None:
        operator, integer = transform_date_to_range(birth_date) #TODO remove once filter backfill is compelted
    if age:
        operator, integer = transform_age_to_CTML(age)

    description = ""
    if gene or 'Signature' in mutation_type:
        description = gene
        if protein_changes:
            description = f"{gene} {protein_changes}"
        if exon:
            description = f"{gene} {protein_changes} {exon}"
        if mutation_type:
            description = f"{description} {mutation_type}"

    if mutational_burden:
        description = mutational_burden
    if cancer:
        description = f"{description} in {cancer}"
    if gender:
        if description:
            description = f"{description}, Gender: {gender}"
        else:
            description = f"Gender: {gender}"

    if (age or birth_date) and operator and integer: #TODO remove once filter backfill is compelted
        description = f"{description}, Age {operator} {int(float(integer))}"

    if allele_fraction is not None:
        operator_desc = ""
        operator = list(allele_fraction.keys())[0]
        if operator == '^gt':
            operator_desc = ">"
        elif operator == '^lt':
            operator_desc = '<'
        allele_val = allele_fraction[operator]
        if allele_val is not None:
            description = f"{description}, Allele Fraction: {operator_desc} {int(allele_val * 100)}%"

    return description.replace('  ', ' ').strip()


def find_filter_matches(items):
    db = database.get_db()
    for item in items:
        do_update = False if item['temporary'] else True
        num_matches, run_id = rerun_filters(filters=[item['_id']], do_update=do_update, datapush_id=None)
        enrollments = get_enrollment(num_matches[item['_id']])
        item['num_samples'] = len(num_matches[item['_id']])
        item['enrollment'] = enrollments

        # don't persist temporary filters
        if item['status'] == 2 and item['temporary'] == True:
            db.filter.remove({"_id": item['_id']})


def get_enrollment(matches):
    """
    Get enrollment counts by month.
    :param matches:
    :return:
    """
    # Generate date list from first of the month
    today = datetime.date.today() + datetime.timedelta(1 * 365 / 12)
    all_dates = pd.date_range(datetime.datetime(2013, 7, 1), today, freq='BM')
    all_dates = all_dates.map(lambda x: datetime.datetime(x.year, x.month, 1))
    all_dates = pd.Series(all_dates)

    # Get report dates with days reset to first of the month
    report_dates = []
    for sample_id in matches:
        for match in matches[sample_id]:
            if 'REPORT_DATE' in match and match['REPORT_DATE'] is not None:
                tmp_date = pd.Series(datetime.datetime(match['REPORT_DATE'].year, match['REPORT_DATE'].month, 1))
                all_dates = all_dates.append(tmp_date)

    # combine them and remove base counts.
    total_dates = all_dates.append(report_dates)
    counts = total_dates.value_counts()
    counts = counts - 1
    counts = counts.sort_index()

    # convert to lists.
    x_axis = list(counts.index)
    y_axis = list(counts)

    x_axis = [d.strftime("%y-%m-%d") for d in x_axis]

    return {
        "x_axis": x_axis,
        "y_axis": y_axis
    }


def start_filter_run(silent=False, datapush_id=None):
    """
    Wrapper function which calls rerun filters.
    Creates a record in active_process collection to make sure multiple filter
    matching runs are not created simultaneously.

    :param silent: Whether to send emails or not
    :param datapush_id: ID to append to output matches if relevant
    :return:
    """
    db = database.get_db()
    db.active_processes.insert({"filters_running": True})
    filters = list(db.filter.find({"temporary": False, "status": {"$in": [0, 1]}}))
    transform_filter_to_CTML(filters, save=True)
    _, run_id = rerun_filters(datapush_id=datapush_id)
    db.active_processes.drop()

    if not silent:
        email_matches(run_id)

    return run_id


def update_filter_pre(item, original):
    """
    When filter is updated via PUT request, update filter "match" clause
    :param item:
    :param original:
    :return:
    """
    transform_filter_to_CTML([item])


def update_filter_post(item, original):
    """
    After filter is updated with new "match" clause, re-find filter matches
    :param item:
    :param original:
    :return:
    """
    # status 3 means filter is deleted
    if item['status'] != 3:
        find_filter_matches([item])
    else:
        update_query = {
            '$set': {
                'is_disabled': True,
                'FILTER_STATUS': 3,
                '_updated': datetime.datetime.now()
            }
        }
        database.get_collection('match').update_many({'FILTER_ID': item['_id']}, update_query)


def _count_matches_by_filter(matches, filters):
    # extract counts
    counts = {
        "new": 0,
        "pending": 0,
        "flagged": 0,
        'not_eligible': 0,
        'enrolled': 0,
        'contacted': 0,
        'eligible': 0,
        'deferred': 0
    }

    # separate matches by filter id
    filter_dict = {}
    for filt in filters:
        filter_dict[str(filt['_id'])] = counts.copy()

    for match in matches:

        if str(match['FILTER_ID']) not in filter_dict:
            continue

        if match['FILTER_STATUS'] == 1:
            if match['MATCH_STATUS'] == 0:
                filter_dict[str(match['FILTER_ID'])]['new'] += 1
            elif match['MATCH_STATUS'] == 1:
                filter_dict[str(match['FILTER_ID'])]['pending'] += 1
            elif match['MATCH_STATUS'] == 2:
                filter_dict[str(match['FILTER_ID'])]['flagged'] += 1
            elif match['MATCH_STATUS'] == 3:
                filter_dict[str(match['FILTER_ID'])]['not_eligible'] += 1
            elif match['MATCH_STATUS'] == 4:
                filter_dict[str(match['FILTER_ID'])]['enrolled'] += 1
            elif match['MATCH_STATUS'] == 5:
                filter_dict[str(match['FILTER_ID'])]['contacted'] += 1
            elif match['MATCH_STATUS'] == 6:
                filter_dict[str(match['FILTER_ID'])]['eligible'] += 1
            elif match['MATCH_STATUS'] == 7:
                filter_dict[str(match['FILTER_ID'])]['deferred'] += 1

    return filter_dict


def _count_matches(matches, match_db):

    # extract counts
    counts = {
        "new": 0,
        "new_matches": 0,
        "pending": 0,
        "flagged": 0,
        'not_eligible': 0,
        'enrolled': 0,
        'contacted': 0,
        'eligible': 0,
        'deferred': 0
    }

    for match in matches:
        if match['FILTER_STATUS'] == 1:
            if match['MATCH_STATUS'] == 0:
                counts['new'] += 1

                if '_new_match' not in match or match['_new_match'] is False:
                    counts['new_matches'] += 1
                    match_db.update_one({'_id': match['_id']}, {'$set': {'_new_match': True}})

            elif match['MATCH_STATUS'] == 1:
                counts['pending'] += 1
            elif match['MATCH_STATUS'] == 2:
                counts['flagged'] += 1
            elif match['MATCH_STATUS'] == 3:
                counts['not_eligible'] += 1
            elif match['MATCH_STATUS'] == 4:
                counts['enrolled'] += 1
            elif match['MATCH_STATUS'] == 5:
                counts['contacted'] += 1
            elif match['MATCH_STATUS'] == 6:
                counts['eligible'] += 1
            elif match['MATCH_STATUS'] == 7:
                counts['deferred'] += 1
    return counts
