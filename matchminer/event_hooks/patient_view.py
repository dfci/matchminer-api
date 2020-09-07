import datetime
import logging

from flask import current_app as app

from matchminer import database, utilities, settings


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
        user = get_current_user(settings.NO_AUTH, app)

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
