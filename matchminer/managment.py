'''
This module enables management or modification of the database. It contains scripts which can be used to
correct errors in the database or facilitate migrations.
'''
import os
import logging
import requests
import json

from matchminer import events
from matchminer import miner
from matchminer import database

# logging
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', )



def maintain_filters():
    """
    recalculate text descriptions

    :return:
    """
    logging.info("maintain filters")

    # get database connection.
    db = database.get_db()

    # find all filters status.
    filters = list(db['filter'].find())

    for filter in filters:

        # skip inactive.
        if 'temporary' not in filter:
            continue
        if filter['temporary'] == True:
            continue

        # get the text string.
        try:
            c, g, txt = miner.prepare_criteria(filter)
            gen_txt, clin_txt = txt
            description = []
        except KeyError:
            continue

        # setup clincal portion.
        cancer, age, gender = clin_txt

        c_test = cancer == ""
        g_test = gender == ""
        a_test = age == ""

        # handle cancer sentance.
        if not c_test:
            description = "%s in %s" % (gen_txt, cancer)
        else:
            description = gen_txt

        # handle the rest.
        if not g_test and a_test:
            description = "%s, Gender: %s" % (description, gender)

        elif not g_test and not a_test:
            description = "%s, Gender: %s, Age %s" % (description, gender, age)

        elif g_test and not a_test:
            description = "%s, Age %s" % (description, age)

        # hack fix
        if description == []:
            description = ''

        # update record with this.
        result = db['filter'].update_one({"_id": filter["_id"]}, {"$set": {"description": description}})



def maintain_matches():
    """
    this function does 2 tasks on matches: 1st it determines if any matches belong to a deleted filter and
    also deletes them. 2nd it adds the MRN to existing matches.

    :return:
    """
    logging.info("maintain matches")

    # get database connection.
    db = database.get_db()

    # find all filters status.
    filters = list(db['filter'].find())

    filters_status = {}
    for filter in filters:
        filters_status[filter['_id']] = filter['status']

    # build a patient lu.
    patient_lu = {}

    # loop over each match and delete if its stale.
    to_delete = list()
    for match in db['match'].find():

        # check if the filter is deleted.
        delete = False
        if match['FILTER_ID'] not in filters_status:
            delete = True

        elif filters_status[match['FILTER_ID']] != 1:
            delete = True

        if delete:
            db['match'].remove({"_id": match['_id']})
            to_delete.append(match['_id'])

        # update it if not deleted.
        if not delete:

            # get patient info.
            if match['CLINICAL_ID'] not in patient_lu:
                patient_lu[match['CLINICAL_ID']] = db['clinical'].find_one({"_id": match['CLINICAL_ID']})

            # get MRN.
            patient_mrn = patient_lu[match['CLINICAL_ID']]['MRN']

            # update the record.
            db['match'].update_one({"_id": match['_id']}, {"$set": {"PATIENT_MRN": patient_mrn}})


    # return the count.
    return to_delete


def maintain_users():
    """
    ensure all users have a role

    :return:
    """
    logging.info("maintain users")

    # get database connection.
    db = database.get_db()

    # find all filters status.
    users = list(db['user'].find())

    # check each user.
    for user in users:
        if 'roles' not in user:
            db['user'].update_one({"_id": user['_id']}, {"$set": {"roles": ["user"]}})


def reannotate_trials():
    db = database.get_db()
    trials = list(db['trial'].find())

    # modify trials to be inserted in bulk later
    events.trial_insert(trials)

    # re-insert.
    for trial in trials:
        db['trial'].delete_one({'_id': trial['_id']})
        db['trial'].insert_one(trial)

    logging.info("DONE")


def maintain_elastic():

    # variables from enviroment.
    json_path = os.environ.get('TRIAL_INDEX', None)
    url = os.environ.get('ELASTIC_URL', None)

    # fetch the matching users.
    r = requests.get(url)
    schema = r.json()

    # do-nothing and just delete it.
    r = requests.delete(url)
    result = r.json()

    # insert the actual mapping.
    with open(json_path) as fin:
        trial_index = json.load(fin)

    r = requests.post(url, json=trial_index)
    result = r.json()

    # re-insert all trials.
    reannotate_trials()


def update_oncotree():
    """
    handles updates in the oncotree
    :return:
    """
