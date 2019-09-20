import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import time
import sched
import logging
import xml.etree.ElementTree as ET
import base64
from bson import ObjectId
import requests
import random

# logging
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', )

GOOGLE_CRED = os.getenv('GOOGLE_CRED', None)
GOOGLE_KEY = os.getenv('GOOGLE_KEY', None)
API_ADDRESS = os.getenv('API_ADDRESS', None)
API_TOKEN = os.getenv('API_TOKEN', None)

def _missing():

    abort = False
    if GOOGLE_CRED is None:
        abort = True
    if GOOGLE_KEY is None:
        abort = True
    if API_ADDRESS is None:
        abort = True
    if API_TOKEN is None:
        abort = True

    return abort


def _gen_user_query(email):
    return "where=%s" % json.dumps({"email": {"$regex": email, "$options": 'i'}})


def _test_get(email, test):

    # create test url.
    url = 'user?%s' % _gen_user_query(email)

    # make the query.
    r, status_code = test.get(url)

    # return items.
    logging.info("test GET")
    return r['_items']


def _real_get(email):

    # add the defaults
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + str(base64.b64encode(API_TOKEN + ':'))
    }

    # build the query string and actual URL.
    url = '%s/user?%s' % (API_ADDRESS, _gen_user_query(email))

    # fetch the matching users.
    r = requests.get(url, headers=headers)
    items = r.json()['_items']

    # return the list.
    logging.info("real GET")
    return items


def _test_insert_user(user, test):

    # create team.
    team = {
        "name": "%s%s" % (user['first_name'][0], user['last_name'])
    }

    # create team.
    url = 'team'
    r, status_code = test.post(url, data=team)
    team_id = r['_id']

    # update user and insert.
    user['teams'] = [team_id]

    # insert user.
    url = "user"
    logging.info("test INSERT")
    r, status_code = test.post(url, data=user)


def _real_insert_user(user):

    # add the defaults
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + str(base64.b64encode(API_TOKEN + ':'))
    }

    # create team.
    team = {
        "name": "%s%s" % (user['first_name'][0], user['last_name'])
    }

    # create team.
    url = '%s/team' % API_ADDRESS
    r = requests.post(url, json=team, headers=headers)
    team_id = r.json()['_id']

    # update user and insert.
    user['teams'] = [team_id]

    # insert user.
    url = "%s/user" % API_ADDRESS
    logging.info("real INSERT")
    r = requests.post(url, json=user, headers=headers)


def _test_update_user(user, test):

    # update it.
    url = "user/%s" % user['_id']
    headers = [('If-Match', user['_etag'])]

    # delete the user name and trip extras.
    user['user_name'] = ''
    for x in list(user.keys()):
        if x[0] == '_':
            del user[x]

    # insert user.
    logging.info("test PUT")
    r, status_code = test.put(url, data=user, headers=headers)


def _real_update_user(user):

    # update it.
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + str(base64.b64encode(API_TOKEN + ':')),
        'If-Match': user['_etag']
    }
    url = "%s/user/%s" % (API_ADDRESS, user['_id'])

    # delete the user name and trip extras.
    user['user_name'] = ''
    for x in list(user.keys()):
        if x[0] == '_':
            del user[x]

    # insert user.
    logging.info("real PUT")
    r, status_code = requests.put(url, json=user, headers=headers)


def account_pipeline(scheduler, freq, test):

    # need enviromental variables.
    if _missing():
        logging.error("missing enviromental variables for account service")
        return

    # establish connection.
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CRED, scope)
    gc = gspread.authorize(credentials)

    # open spreadsheet of interest.
    sps = gc.open_by_key(GOOGLE_KEY)
    sht = sps.sheet1

    # iterate over each record.
    for record in sht.get_all_records():

        # create user template.
        user = {
            "title": "",
            "first_name": record['First Name'],
            "last_name": record['Last Name'],
            "user_name": record['Partners ID'],
            "email": record['Institutional Email Address'],
            "roles": ["user"]
        }

        # get the user.
        if test == -1:
            items = _real_get(user['email'])
        else:
            items = _test_get(user['email'], test)

        # new user.
        if len(items) == 0:

            # add user.
            if test == -1:
                _real_insert_user(user)
            else:
                _test_insert_user(user, test)

        else:

            # check for a dis-approved user.
            update = False
            if record['Approved by Susan'] == 'NO' and items[0]['user_name'] != '':

                # remove the status.
                user['user_name'] = ''
                update = True

            # check for an inactive user made active.
            if record['Approved by Susan'] == 'YES' and items[0]['user_name'] == '':

                # add the status.
                update = True

            # TODO: check for an expired user.

            # make the request.
            if update:

                if test == -1:
                    _real_update_user(user)
                else:
                    _test_update_user(user, test)

    # debug service.
    if test == -1:

        # re-run
        logging.info("scheduling self")
        scheduler.enter(freq, 1, account_pipeline, (scheduler, freq, test))