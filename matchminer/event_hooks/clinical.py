import datetime
import logging

from bson import ObjectId
from flask import current_app as app

from matchminer import database


def hide_name(item):
    """Hides patient name"""
    for i, idx in zip(item['_items'][:], range(len(item['_items']))):
        for nm in ["FIRST_NAME", "LAST_NAME", "FIRST_LAST", "LAST_FIRST"]:
            if nm in i:
                del i[nm]


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
        update = {'is_disabled': True, "_updated": datetime.datetime.now()}
        db['match'].update_many({'CLINICAL_ID': original['_id']}, {'$set': update })


def clinical_delete(item):

    # get database lookup.
    genomic_db = app.data.driver.db['genomic']
    match_db = app.data.driver.db['match']
    trial_match_db = app.data.driver.db['trial_match']

    # delete associated genomic entries.
    genomic_db.delete_many({"CLINICAL_ID": ObjectId(item['_id'])})

    # delete associated matches.
    match_db.delete_many({"CLINICAL_ID": ObjectId(item['_id'])})

    # delete associated trial matches.
    trial_match_db.delete_many({"clinical_id": ObjectId(item['_id'])})


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


def align_other_clinical(a):

    # extract the clinical id.
    clinical_id = a['_id']

    # lookup any matches.
    clinical_db = database.get_collection('clinical')

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
