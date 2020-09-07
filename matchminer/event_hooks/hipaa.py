import datetime
import logging

from bson import ObjectId
from flask import current_app as app


def hipaa_logging_item(resource, response):
    if resource == 'response' or app.auth is None:
        return

    db = app.data.driver.db
    user = app.auth.get_request_auth_value()
    user_name = user['user_name']

    # don't log service account
    if user_name == 'cbioone':
        return

    # deal with clinical.
    needs_logging = False
    if resource == 'clinical':
        needs_logging = True

        # fetch loggable patient id.
        patient_mrn = response['MRN']

    elif resource == 'match':
        needs_logging = True

        # fetch the clinical_id
        clinical_id = response['CLINICAL_ID']

        # determine if it was resolved.
        if isinstance(clinical_id, dict):
            patient_mrn = clinical_id['MRN']

        else:
            clinical = db['clinical'].find_one({'_id': ObjectId(clinical_id)})
            patient_mrn = clinical['MRN']

    if needs_logging:
        phi_list = list()
        for x in response.keys():
            if x[0] == '_':
                continue
            phi_list.append(x)

        # create entry.
        dt = datetime.datetime.now()
        transaction = {
            'user_id': user_name,
            'patient_id': patient_mrn,
            'phi': phi_list,
            'reason': 'MatchMiner - Clinical Trial matching',
            'timestamp': dt,
            app.config['LAST_UPDATED']: dt,
            app.config['DATE_CREATED']: dt
        }

        # insert it.
        app.data.insert('hipaa', transaction)


def hipaa_logging_resource(resource, response):

    if resource == 'trial' or resource == 'public_stats':
        return

    for item in response['_items']:
        hipaa_logging_item(resource, item)
