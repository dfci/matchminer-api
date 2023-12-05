# -*- coding: utf-8 -*-

"""
    Auth-Token
    ~~~~~~~~~~

    Securing an Eve-powered API with Token based Authentication.
"""
import json
import logging
import time
import uuid
import datetime
from functools import wraps

from bson import ObjectId
from eve.auth import TokenAuth
from flask import current_app as app, Response, request, abort
from bson.objectid import ObjectId

from matchminer import database
from matchminer.settings import ONCORE_CURATION_AUTH_TOKEN, DISABLE_ONCORE_AUTH

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s', )


class TokenAuth(TokenAuth):

    def check_auth(self, token, allowed_roles, resource, method):
        """For the purpose of this example the implementation is as simple as
        possible. A 'real' token should probably contain a hash of the
        username/password combo, which sould then validated against the account
        data stored on the DB.
        """

        # use Eve's own db driver; no additional connections/resources are used
        accounts = app.data.driver.db['user']

        # search for user with right token and allowed roles.
        lookup = {'token': token}
        if allowed_roles:
            lookup['roles'] = {"$in": allowed_roles}

        user = None
        for attempt in range(5):
            try:
                user = accounts.find_one(lookup)
            except Exception as e:
                wait_t = 0.2 * pow(2, attempt)  # exponential back off
                logging.warning("PyMongo auto-reconnecting... %s. Waiting %.1f seconds.", str(e), wait_t)
                time.sleep(wait_t)

        # return none.
        if user is None:
            logging.info("warning failed authentication")
            logging.info("token: %s" % token)
            return user

        # check for role.
        skip_lastuath = False
        if len(set(user['roles']).intersection(set(['service']))) > 0:
            skip_lastuath = True

        # verify it hasn't been toooo long.
        cur_time = datetime.datetime.now()
        cur_time = cur_time.replace(tzinfo=None)
        if not skip_lastuath and 'last_auth' in user:

            # extract last auth.
            last_auth = user['last_auth'].replace(tzinfo=None)

            # find difference.
            diff = cur_time - last_auth
            total_seconds = diff.total_seconds()

            if (float(total_seconds) / 60.0) > app.config['TOKEN_TIMEOUT']:
                # reset token.
                accounts.update_one({'_id': user['_id']}, {'$set': {'token': str(uuid.uuid4())}})

                # don't authorize the request.
                return None

        # set the user of this request.
        self.set_request_auth_value(user)

        # log results
        if user is None:
            logging.info("warning failed authentication")
            logging.info("token: %s" % token)
        else:

            # update with last auth.
            accounts.update_one({'_id': user['_id']}, {'$set': {'last_auth': datetime.datetime.now()}})

        # return results.
        return user


def authorize_custom_request(request):
    """
    Authorize custom request
    """

    accounts = app.data.driver.db['user']
    ta = TokenAuth()
    not_authed = False
    if request.authorization is not None:
        token = request.authorization.username

        # find the user.
        user = accounts.find_one({'token': token})

        # die on this request.
        if user is None:
            not_authed = True
    else:
        not_authed = True

    # deal with bad request.
    return not_authed


def authorize_oncore_curation(request):
    """
    Look up the token of the logged-in user and validate if they are authorized to access
    the Oncore curation platform.

    :param request: {Flask request obj}
    :return: {bool} True if user is not authenticated. False if user is authenticated
    """

    if DISABLE_ONCORE_AUTH:
        logging.info("Curation UI auth disabled")
        return False

    user_id = request.cookies.get('user_id')
    if user_id is None:
        return True

    db = app.data.driver.db
    query = {'_id': ObjectId(user_id)}
    user = db.user.find_one(query)
    if user is None or 'oncore_token' not in user:
        return True

    if str(user['oncore_token']) != str(ONCORE_CURATION_AUTH_TOKEN):
        return True

    return False


def auth_required(view):
    @wraps(view)
    def auth(*args, **kwargs):
        # check authorization
        not_authed = authorize_custom_request(request)
        if not_authed:
            return Response("not authorized route", 401, {'WWW-Authenticate': 'Basic realm="Login!"'})
        return view(*args, **kwargs)
    return auth


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
                team_list = next(iter(clause['TEAM_ID'].values()))
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
