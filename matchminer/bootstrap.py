import base64
import datetime
import json
import logging
import time
from email.utils import formatdate

import pandas as pd
from bson import ObjectId
from eve import Eve
from pymongo import MongoClient

from matchminer.settings import MONGO_URI, MONGO_USERNAME, MONGO_DBNAME, MONGO_PASSWORD
from matchminer.settings_dev import COLLECTION_CLINICAL, COLLECTION_GENOMIC, DATA_CLINICAL_CSV, clinical, \
    DATA_GENOMIC_CSV, genomic


def bootstrap(ctx, forced=False):
    # get the current time.
    cur_dt = formatdate(time.mktime(datetime.now().timetuple()))

    # connect to database.
    connection = MongoClient(MONGO_URI)

    # establish connection.
    if MONGO_USERNAME:
        connection[MONGO_DBNAME].add_user(MONGO_USERNAME, MONGO_PASSWORD)

    # setup the db pointer
    db = connection[MONGO_DBNAME]

    # check if the clinical and genomic empty.
    if db[COLLECTION_CLINICAL].count() > 0 or db[COLLECTION_GENOMIC].count() > 0:
        if not forced:
            logging.warning("attempting to bootstrap the database without forcing")
            return

    logging.warning("forcibly resetting the database, may take some time")

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


def clear_db_completely():
    # connect to database.
    connection = MongoClient(MONGO_URI)

    # establish connection.
    if MONGO_USERNAME:
        connection[MONGO_DBNAME].add_user(MONGO_USERNAME, MONGO_PASSWORD)

    # setup the db pointer
    db = connection[MONGO_DBNAME]

    logging.warning("dropping all tables in database")

    # clear the database.
    db.drop_collection("clinical")
    db.drop_collection("genomic")
    db.drop_collection("user")
    db.drop_collection("team")
    db.drop_collection("filter")
    db.drop_collection("match")
    db.drop_collection("normalize")
    db.drop_collection("email")
    db.drop_collection("run_log_match")
    db.drop_collection("clinical_run_history_match")
    db.drop_collection("active_processes")
    connection.close()


def init_user_debug(db=None, ctx=None):
    # only activate if necessary.
    if db is None:

        # connect to database.
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
        "_id": ObjectId("5697ecb48a6ba828126f8129"),
        "first_name": 'Jean-luc3',
        "last_name": 'Picard3',
        "title": "Captain3",
        "email": 'jlp3@jimmy.harvard.edu',
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


def utility_post(ctx, resource, data, token=None):
    # add the defaults
    headers = list()
    headers.append(('Content-Type', 'application/json'))
    if token is not None:
        headers.append(('Authorization', 'Basic ' + base64.b64encode(f'{token}:'.encode('utf-8')).decode()))

    # determine how to insert this.
    if isinstance(ctx, Eve):

        # if list iterate and insert seperatly.
        if isinstance(data, list):

            # debug server start.
            raise NotImplementedError
            # for d in data:
            #    resp = ctx.test_client().post(resource, data=d)

        else:
            resource = 'api/%s' % resource
            val = str(json.dumps(data), errors='replace')
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


def genomics_gen(genomic_df, genomic_schema=None):
    """
    generate valid dictionaries from dataframe
    :param genomics_df: pd.DataFrame
    """

    # convert known columns.
    genomic_df['TRUE_ENTREZ_ID'] = genomic_df['TRUE_ENTREZ_ID'].astype(str)
    genomic_df['BESTEFFECT_ENTREZ_ID'] = genomic_df['BESTEFFECT_ENTREZ_ID'].astype(str)
    genomic_df['CANONICAL_ENTREZ_ID'] = genomic_df['CANONICAL_ENTREZ_ID'].astype(str)

    # names cols.
    cis = list(zip(list(range(len(genomic_df.columns))), list(genomic_df.columns)))

    # loop over each entry.
    for row in genomic_df.itertuples():

        tmp = {}
        for i, key in cis:

            if key not in genomic_schema:
                continue

            val = row[i + 1]

            if pd.isnull(val):
                val = None

            tmp[key] = val

        yield tmp


def clinical_gen(clinical_df, clinical_schema=None):
    """
    generate valid dictionaries from dataframe
    :param clinical_df: pd.DataFrame
    """

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

        entry = clinical_df.ix[i]
        tmp = {}

        for key in clinical_schema:

            # sanitcy.
            if key not in columns:
                continue

            val = clinical_df.ix[i][key]
            if isinstance(val, pd.Timestamp):
                val = formatdate(time.mktime(val.to_pydatetime(warn=False).timetuple()))

            if pd.isnull(val):
                val = None

            tmp[key] = val

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


def clinical_load(file_path):
    """
    loads the clincal data into a pandas DataFrame. Parsing is done.

    :param file_path: str
    :return: pd.DataFrame
    """

    clinical_df = pd.read_pickle(file_path)
    return clinical_df


def genomic_load(file_path):
    """
    loads the genomic data into a pandas DataFrame. Parsing is done.

    :param file_path: str
    :return: pd.DataFrame
    """

    # load the genomics.
    genomic_df = pd.read_pickle(file_path)

    # return it.
    return genomic_df
