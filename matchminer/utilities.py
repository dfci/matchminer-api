import time
import subprocess
import pandas as pd
import random
from pymongo import MongoClient
from bson.objectid import ObjectId
from eve.flaskapp import Eve
import datetime
from rfc822 import formatdate
import base64
from functools import wraps, update_wrapper
from datetime import datetime, date
from flask import Response, request, make_response
import shutil

from matchminer import database
from settings import *

# logging
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', )

# constants.
REPLACEMENTS = {
    '$and': '^and',
    '$or': '^or',
    '$gte': '^gte',
    '$lte': '^lte',
    '$in': '^in',
    '$regex': '^regex'
}
REREPLACEMENTS = {}
for key, val in REPLACEMENTS.items():
    REREPLACEMENTS[val] = key


def normalize_fields(field):
    mapping = {
        'HUGO_SYMBOL': 'TRUE_HUGO_SYMBOL',
        'PROTEIN_CHANGE': 'TRUE_PROTEIN_CHANGE',
        'EXON_NUMBER': 'TRUE_TRANSCRIPT_EXON',
        'ONCOTREE_PRIMARY_DIAGNOSIS': 'ONCOTREE_PRIMARY_DIAGNOSIS_NAME',
        'AGE': 'BIRTH_DATE'
    }
    if field in mapping:
        return mapping[field]
    else:
        return field


def parse_response(url):

    # looks for url
    is_response = False
    item_id = None
    if url.count("/response/") > 0:

        # we have a response.
        is_response = True

        # look for url parameters.
        tokens = url.split("?")
        no_ml = False
        if len(tokens) > 1:
            params = []
            if tokens[-1].count("&") > 0:
                params = tokens[-1].split("&")
            else:
                params.append(tokens[-1])

            # just kidding no redirect wanted
            for p in params:
                if p.count("no_ml=true") > 0:
                    is_response = False

        if is_response:

            # get the object again.
            tokens = url.split("/")
            last_token = tokens[-1]
            if last_token.count("?") > 0:
                item_id = last_token.split("?")[0]
            else:
                item_id = last_token

    return is_response, item_id


def get_recursively(search_dict, field):
    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key of the field
    provided.
    """
    fields_found = []

    for key, value in search_dict.iteritems():

        # try to parse date.
        if isinstance(value, basestring) and value.count(field) > 0:

            # save final.
            fields_found.append(value)

        elif isinstance(value, dict):
            results = get_recursively(value, field)
            for result in results:
                fields_found.append(result)

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    more_results = get_recursively(item, field)
                    for another_result in more_results:
                        fields_found.append(another_result)

    return fields_found


def get_key_recursively(search_dict, field):
    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key of the field
    provided.
    """
    fields_found = []

    # loop over every key, value pair.
    for key, value in search_dict.iteritems():

        # try to parse date.
        if key == field:

            # save final.
            fields_found.append(value)

        elif isinstance(value, dict):
            results = get_key_recursively(value, field)
            for result in results:
                fields_found.append(result)

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    more_results = get_key_recursively(item, field)
                    for another_result in more_results:
                        fields_found.append(another_result)

    return fields_found


def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return update_wrapper(no_cache, view)


def utility_post(ctx, resource, data, token=None):

    # add the defaults
    headers = list()
    headers.append(('Content-Type', 'application/json'))
    if token is not None:
        headers.append(('Authorization', 'Basic ' + str(base64.b64encode(token + ':'))))

    # determine how to insert this.
    if isinstance(ctx, Eve):

        # if list iterate and insert seperatly.
        if isinstance(data, list):

            # debug server start.
            raise NotImplementedError
            #for d in data:
            #    resp = ctx.test_client().post(resource, data=d)

        else:
            resource = 'api/%s' % resource
            val = unicode(json.dumps(data), errors='replace')
            resp = ctx.test_client().post(resource, data=val, headers=headers)

        # parse response.
        try:
            v = json.loads(resp.get_data())
        except:
            v = None

        # return the two parter
        return v, resp.status_code

    else:

        # unit test
        resp, status_code = ctx.post(resource, data=data, headers=headers)

        # display error.
        if status_code != 201:
            logging.error("unable to insert")
            assert False

        # assert it worked.
        ctx.assert201(status_code), resp

        # return two parts.
        return resp, status_code


def clear_db_completely():

    # connect to database.
    #connection = MongoClient(MONGO_HOST, MONGO_PORT)
    connection = MongoClient(MONGO_URI)

    # establish connection.
    if MONGO_USERNAME:
        connection[MONGO_DBNAME].add_user(MONGO_USERNAME, MONGO_PASSWORD)

    # setup the db pointer
    db = connection[MONGO_DBNAME]

    logging.warn("dropping all tables in database")

    # clear the database.
    db.drop_collection("clinical")
    db.drop_collection("genomic")
    db.drop_collection("user")
    db.drop_collection("team")
    db.drop_collection("filter")
    db.drop_collection("match")
    connection.close()


def clear_db_partially():

    logging.warn("dropping all tables in database EXCEPT clinical and genomic")

    # connect to database.
    #connection = MongoClient(MONGO_HOST, MONGO_PORT)
    connection = MongoClient(MONGO_URI)

    # establish connection.
    if MONGO_USERNAME:
        connection[MONGO_DBNAME].add_user(MONGO_USERNAME, MONGO_PASSWORD)

    # setup the db pointer
    db = connection[MONGO_DBNAME]

    # clear the database.
    db.drop_collection("user")
    db.drop_collection("team")
    db.drop_collection("filter")
    db.drop_collection("match")
    connection.close()


def bootstrap(ctx, forced=False):

    # get the current time.
    cur_dt = formatdate(time.mktime(datetime.now().timetuple()))

    # connect to database.
    #connection = MongoClient(MONGO_HOST, MONGO_PORT)
    connection = MongoClient(MONGO_URI)

    # establish connection.
    if MONGO_USERNAME:
        connection[MONGO_DBNAME].add_user(MONGO_USERNAME, MONGO_PASSWORD)

    # setup the db pointer
    db = connection[MONGO_DBNAME]

    # check if the clinical and genomic empty.
    if db[COLLECTION_CLINICAL].count() > 0 or db[COLLECTION_GENOMIC].count() > 0:
        if not forced:
            logging.warn("attempting to bootstrap the database without forcing")
            return

    logging.warn("forcibly resetting the database, may take some time")

    # clear the database.
    clear_db_completely()
    connection.close()

    # initialize user.
    init_user_debug(ctx=ctx)

    # load the clinical_df
    clinical_df = clinical_load(DATA_CLINICAL_CSV)

    # store unique keys for every sample.
    keys = {}

    # insert each clinical entry
    new_clinical = 0
    for entry in clinical_gen(clinical_df, clinical_schema=clinical['schema']):

        # insert into db the clinical data.
        resp, status_code = utility_post(ctx, 'clinical', entry, token='abc123')
        if status_code != 201:
            logging.error("unable to insert")
        assert status_code == 201
        new_clinical += 1

        # get the unique key.
        key = resp['_id']

        # save it for later linking to genomics
        keys[entry['SAMPLE_ID']] = key

    # load the genomic_df.
    genomic_df = genomic_load(DATA_GENOMIC_CSV)

    # insert each genomic entry.
    i = 0
    new_genomic = 0
    for entry in genomics_gen(genomic_df, genomic_schema=genomic['schema']):

        # must have a clinical entry.
        if entry['SAMPLE_ID'] not in keys:
            continue

        # hook entry with clinical_id.
        id = keys[entry['SAMPLE_ID']]
        entry['CLINICAL_ID'] = id

        # insert it into db.
        entry['WILDTYPE'] = bool(entry['WILDTYPE'])
        resp, status_code = utility_post(ctx, 'genomic', entry, token='abc123')
        if status_code != 201:
            logging.error("unable to insert")
        assert status_code == 201

        #if i > 1000:
        #    break
        i += 1
        new_genomic += 1

    # post the status update.
    status = {
        'last_update': cur_dt,
        'new_clinical': new_clinical,
        'updated_clinical': 0,
        'new_genomic': new_genomic,
        'updated_genomic': 0,
        'silent': True
    }
    resp, status_code = utility_post(ctx, 'status', status, token='abc123')
    if status_code != 201:
        logging.error("unable to insert")
    assert status_code == 201


def add_simulated_sv():

    # connect to database.
    #connection = MongoClient(MONGO_HOST, MONGO_PORT)
    connection = MongoClient(MONGO_URI)

    # setup the db pointer
    db = connection[MONGO_DBNAME]

    # fetch all patients.
    patients = list(db.clinical.find())
    pidx = range(len(patients))

    # loop over each synoymm
    svs = list()
    from matchminer.constants import synonyms
    for key in synonyms:
        for val in synonyms[key]:

            # get clinical_id.
            idx = random.choice(pidx)
            clinical_id = str(patients[idx]['_id'])
            sample_id = str(patients[idx]['SAMPLE_ID'])


            # make a SV.
            sv = {
                'CLINICAL_ID': clinical_id,
                'VARIANT_CATEGORY': 'SV',
                'STRUCTURAL_VARIANT_COMMENT': "tmp6654 " + val,
                'WILDTYPE': False,
                'SAMPLE_ID': sample_id
            }
            svs.append(sv)

    # return it.
    connection.close()
    return svs


def init_user_debug(db=None, ctx=None):

    # only activate if necessary.
    if db is None:

        # connect to database.
        #connection = MongoClient(MONGO_HOST, MONGO_PORT)
        connection = MongoClient(MONGO_URI)

        # establish connection.
        if MONGO_USERNAME:
            connection[MONGO_DBNAME].add_user(MONGO_USERNAME, MONGO_PASSWORD)

        # setup the db pointer
        db = connection[MONGO_DBNAME]

    # add testing user.
    user_db = db['user']
    team_db = db['team']

    # add dummy first user.
    user = {
        "_id": ObjectId("4444ecb48a6ba828126f4444"),
        "first_name": 'Jean-luc',
        "last_name": 'Picard',
        "title": "Captain",
        "email": 'jlp@jimmy.harvard.edu',
        "token": 'abc123',
        "roles": ["admin"],
        'teams': []
    }
    user_id = user['_id']
    user_token = user['token']
    user_db.insert_one(user)

    # insert the team first.
    team = {
        "_id": ObjectId("66a52871a8c829842fbe618b"),
        "name": "test team"
    }

    # insert it.
    team_db.insert_one(team)
    team_id = team['_id']

    # add user.
    user = {
        "_id": ObjectId("5697ecb48a6ba828126f8128"),
        "first_name": 'Jean-luc2',
        "last_name": 'Picard2',
        "title": "Captain2",
        "email": 'jlp2@jimmy.harvard.edu',
        "token": 'abc1234',
        "roles": ["user"],
        'teams': []
    }
    user_db.insert_one(user)

    # insert the team first.
    team = {
        "name": "bernd team"
    }

    # insert it.
    r, status = utility_post(ctx, 'team', team, token=user_token)
    ctx.assert201(status)

    # add user.
    user = {
        "_id": ObjectId("5697ecb48a6ba828126f8128"),
        "first_name": 'Jean-luc3',
        "last_name": 'Picard3',
        "title": "Captain3",
        "email": 'jlp3@jimmy.harvard.edu',
        "token": 'abc1234',
        "user_name": "NULL",
        "roles": ["user"],
        'teams': [r['_id']]
    }

    r, status = utility_post(ctx, 'user', user, token=user_token)
    ctx.assert201(status)

    # close db.
    if db is None:
        connection.close()

    # return results.
    return user_id, user_token, team_id


def bootstrap_matches(ctx):

    # clear the database.
    clear_db_partially()

    # add user out of band.
    user_id, user_token, team_id = init_user_debug(ctx=ctx)

    # add simulated structural variants.
    svs = add_simulated_sv()
    for sv in svs:
        r, status = utility_post(ctx, 'genomic', sv, token='abc123')
        ctx.assert201(status)


def parse_resource_field():

    # parse args.
    resource = request.args.get("resource")
    field = request.args.get("field")

    # sanity check.
    if resource is None or field is None:
        data = json.dumps({'error': 'missing parameters'})
        resp = Response(response=data,
            status=400,
            mimetype="application/json")

        return 1, resp

    # ensure resource is in whitelist.
    whitelist = set(["clinical", "genomic"])
    if resource not in whitelist:
        data = json.dumps({'error': 'bad resource: %s' % resource})
        resp = Response(response=data,
            status=400,
            mimetype="application/json")

        return 1, resp

    # don't allow trixsy fields.
    tmp = field.lower()
    cnd1 = tmp.count("_id") > 0
    cnd2 = tmp.count("team")
    cnd3 = tmp.count("user")
    if cnd1 or cnd2 or cnd3:
        data = json.dumps({'error': 'bad field: %s' % field})
        resp = Response(response=data,
            status=400,
            mimetype="application/json")

        return 1, resp

    return 0, (resource, field)


def backup_restore(dir_path):

    # create restore commands.
    cmd_restore = 'mongorestore --host %s --drop --db %s %s/%s' % \
                  (MONGO_HOST, MONGO_DBNAME, dir_path, MONGO_DBNAME)

    # execute it.
    subprocess.call(cmd_restore.split(" "))


def backup_event(scheduler, dir_path, freq, max_cnt, debug):

    logging.info("backup database: %s %s" % (str(time.time()), str(dir_path)))

    # make timestamp.
    cur_stamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    # make directory.
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    out_dir = os.path.join(dir_path, cur_stamp)

    # check if this exists.
    if os.path.isdir(out_dir):
        out_dir = os.path.join(out_dir, random.randint())

    # create the dump commands.
    cmd_backup = 'mongodump --host %s --db %s --out %s' % \
          (MONGO_HOST, MONGO_DBNAME, out_dir)

    # execute them.
    subprocess.call(cmd_backup.split(" "))

    # remove extras.
    active_dirs = [os.path.join(dir_path, x) for x in os.listdir(dir_path)]
    files = sorted(active_dirs, key=os.path.getctime)
    if len(files) >= max_cnt:

        logging.info("remove old backup: %s" % files[0])
        shutil.rmtree(files[0])

    # only schedule next event if necessary.
    if not debug:
        scheduler.enter(freq, 1, backup_event, (scheduler, dir_path, freq, max_cnt, debug))

    # return the directory.
    return out_dir


def insert_users(data, from_file=False):

    # load the data.
    if from_file:
        with open(data, "rb") as fin:
            lines = fin.readlines()

        # build equivalent.
        data = list()
        for line in lines:
            data.append(line.strip().split(","))
            tokens = line.strip().split(",")

    # simplify database.
    user_db = database.get_collection("user")
    team_db = database.get_collection("team")

    # build equivalent.
    for tokens in data[1::]:

        # simplify.
        user = {
            "first_name": tokens[1],
            "last_name": tokens[2],
            "user_name": tokens[3],
            "email": tokens[4],
            "roles": ["user"]
        }

        # query for existing user.
        result = user_db.find_one({"email": tokens[4]})

        # deal with existing user.
        if result is not None:

            # check if there was a status update.
            if tokens[7] == 'NO':
                user_db.update_one({"_id": result['_id']}, {"$set": {"user_name": ""}})

            # skip
            continue

        # create default team
        team_id = team_db.insert({"name": user['first_name'][0] + user['last_name']})

        # create the user account.
        user['teams'] = [team_id]

        # insert the user.
        user_db.insert(user)


def clinical_load(file_path):
    """
    loads the clincal data into a pandas DataFrame. Parsing is done.

    :param file_path: str
    :return: pd.DataFrame
    """

    # load the clinical data.
    #clinical_df = pd.read_csv(file_path, header=0, sep="\t")
    clinical_df = pd.read_pickle(file_path)

    # return the dataframe.
    return clinical_df


def genomic_load(file_path):
    """
    loads the genomic data into a pandas DataFrame. Parsing is done.

    :param file_path: str
    :return: pd.DataFrame
    """

    # load the genomics.
    #genomic_df = pd.read_csv(file_path, header=0, sep='\t', low_memory=False, dtype={'TIER': np.int, 'POSITION': np.int})
    genomic_df = pd.read_pickle(file_path)

    # return it.
    return genomic_df


def get_physicians_names():
    return ["none"]


def clinical_gen(clinical_df, clinical_schema=None):
    """
    generate valid dictionaries from dataframe
    :param clinical_df: pd.DataFrame
    """

    # create validator.
    #if clinical_schema is not None:
    #    v = ConsentValidatorCerberus(clinical_schema)

    # build list of valid columns.
    columns = set(list(clinical_df.columns))

    # cast certain known ones.
    clinical_df['ALT_MRN'] = clinical_df['ALT_MRN'].astype(str)
    clinical_df['MRN'] = clinical_df['MRN'].astype(str)
    clinical_df['POWERPATH_PATIENT_ID'] = clinical_df['POWERPATH_PATIENT_ID'].astype(str)

    clinical_df['DATE_RECEIVED_AT_SEQ_CENTER'] = pd.to_datetime(clinical_df['DATE_RECEIVED_AT_SEQ_CENTER'])
    clinical_df['BIRTH_DATE'] = pd.to_datetime(clinical_df['BIRTH_DATE'])
    clinical_df['REPORT_DATE'] = pd.to_datetime(clinical_df['REPORT_DATE'])

    # loop over each entry.
    for i in range(clinical_df.shape[0]):

        # simplify.
        entry = clinical_df.ix[i]
        # create dictionary.
        tmp = {}
        #for key in clinical_df.columns:
        for key in clinical_schema:

            # sanitcy.
            if key not in columns:
                continue

            # convert timestamps.
            val = clinical_df.ix[i][key]
            if isinstance(val, pd.Timestamp):
                val = formatdate(time.mktime(val.to_pydatetime(warn=False).timetuple()))

            if isinstance(val, str):
                val = unicode(val, errors='replace')

            # convert nan
            if pd.isnull(val):
                val = None

            # save it to dict.
            tmp[key] = val

        # validate it against schema.
        #if clinical_schema is not None:
        #    v.validate(tmp)

        # HACK: add in report version if not there.
        if 'REPORT_VERSION' not in tmp:
            tmp['REPORT_VERSION'] = 1

        # check conset.
        if 'QUESTION1_YN' in tmp:
            cnd1 = tmp['QUESTION1_YN'] == 'Y'
            cnd3 = tmp['QUESTION3_YN'] == 'Y'
            cndc = tmp['CRIS_YN'] == 'Y'

            if not cnd1 or not cnd3 or not cndc:
                continue

        # fix inconsistent fields.
        if 'GENDER' in tmp:
            if tmp['GENDER'].lower() == "female":
                tmp['GENDER'] = "Female"
            elif tmp['GENDER'].lower() == "male":
                tmp['GENDER'] = "Male"

        # yield the dictionary.
        yield tmp


def genomics_gen(genomic_df, genomic_schema=None):
    """
    generate valid dictionaries from dataframe
    :param genomics_df: pd.DataFrame
    """

    # create validator.
    #if genomic_schema is not None:
    #    v = ConsentValidatorCerberus(genomic_schema)

    # convert known columns.
    genomic_df['TRUE_ENTREZ_ID'] = genomic_df['TRUE_ENTREZ_ID'].astype(str)
    genomic_df['BESTEFFECT_ENTREZ_ID'] = genomic_df['BESTEFFECT_ENTREZ_ID'].astype(str)
    genomic_df['CANONICAL_ENTREZ_ID'] = genomic_df['CANONICAL_ENTREZ_ID'].astype(str)

    # names cols.
    cis = zip(range(len(genomic_df.columns)), list(genomic_df.columns))

    # loop over each entry.
    for row in genomic_df.itertuples():

        # create dictionary.
        tmp = {}
        for i, key in cis:

            # skip unknown.
            if key not in genomic_schema:
                continue

            # extract value.
            val = row[i+1]

            # convert nan
            if pd.isnull(val):
                val = None

            # fix bad encoding.
            if isinstance(val, str):
                val = unicode(val, errors='replace')

            # save it to dict.
            tmp[key] = val

        # validate it against schema.
        #if genomic_schema is not None:
        #    v.validate(tmp)

        # yield it.
        yield tmp


def dump_collections(out_dir, settings):

    # create the dump commands.
    cmd_genomic = 'mongodump --host %s --db %s --collection %s --out %s' % \
          (settings.MONGO_URI, settings.MONGO_DBNAME, settings.COLLECTION_GENOMIC, out_dir)
    cmd_clinical = 'mongodump --host %s --db %s --collection %s --out %s' % \
          (settings.MONGO_URI, settings.MONGO_DBNAME, settings.COLLECTION_CLINICAL, out_dir)

    # execute them.
    subprocess.call(cmd_genomic.split(" "))
    subprocess.call(cmd_clinical.split(" "))


def restore_collections(in_dir, settings):

    # create restore commands.
    cmd_restore = 'mongorestore --host rs0/%s:%d --db %s --drop %s/%s' % \
                  (settings.MONGO_HOST, settings.MONGO_PORT, settings.MONGO_DBNAME, in_dir, settings.MONGO_DBNAME)

    logging.info(cmd_restore)

    # execute it.
    subprocess.call(cmd_restore.split(" "))


def set_curated(mtrial):
    """Sets the date of last curation. Determined by POSTs/PUTs through the curation interface."""
    mtrial['curated_on'] = datetime.now().strftime('%B %d, %Y')
    mtrial['last_updated'] = datetime.now().strftime('%B %d, %Y')
    return mtrial


def set_updated(otrial):
    """Sets the last updated date. Determined by Oncore updates."""
    otrial['last_updated'] = datetime.now().strftime('%B %d, %Y')
    return otrial


def get_data_push_id(db):
    """
    Returns the most recent data push id in the database.

    :param db: database connection
    :return: data_push_id string
    """

    dpi = list(db.status.find({}, {'data_push_id': 1}).sort('data_push_id', -1).limit(1))
    if dpi:
        return dpi[0]['data_push_id']
    else:
        return None


def exclude_ksg(users):
    """
    Excludes KSG team members from the inclusion in the statistics page

    :param users: List of all users
    :return: List of all users minus KSG team members
    """
    non_ksg_users = []
    for user in users:
        user_name = '%s %s' % (user['first_name'], user['last_name'])
        if user_name.replace(' ', '_') not in EXCLUDE_FROM_STATISTICS:
            non_ksg_users.append(user)

    return non_ksg_users


def get_user_name(user):
    """
    Return the user's name

    :param user: User document
    :return: String of user's name
    """
    return '%s %s' % (user['first_name'], user['last_name'])


def get_user_role(user):
    """
    Return the user's roles, excluding role "user"

    :param user: User document
    :return: String of user's roles
    """
    return ", ".join(list(set(sorted(user['roles'])))).replace("user", "").replace("user,", "")[:-2]


def convert_old_dates(doc):
    """
    Converts old IsoDate formatted dates to string of format YYYY-MM-DD

    :param doc: Old datatable rows for MatchMiner Statistics table
    :return: Same table, but with the "Date of last CAMD Update" reformatted for all rows
    """

    new = []
    for row in doc["mm_data_set"]:
        camd_date = row[0]
        if isinstance(camd_date, date):
            camd_date = camd_date.strftime("%Y-%m-%d")
        new.append([camd_date] + row[1:])

    return new


def get_current_user(no_auth, app):
    """
    Access the current user accessing the system.

    :param no_auth: Boolean. If true, use a demo user with last name "Doe"
    :param app:
    :return: User account document
    """

    if no_auth:
        logging.info("NO AUTH enabled. get_current_user")
        accounts = app.data.driver.db['user']
        user = accounts.find_one({"last_name": "Doe"})
    else:
        user = app.auth.get_request_auth_value()

    return user
