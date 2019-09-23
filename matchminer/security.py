# -*- coding: utf-8 -*-

"""
    Auth-Token
    ~~~~~~~~~~

    Securing an Eve-powered API with Token based Authentication.
"""
import logging
import time
import uuid
import datetime
from eve.auth import TokenAuth
from flask import current_app as app
from bson.objectid import ObjectId

from matchminer.settings import ONCORE_CURATION_AUTH_TOKEN

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', )


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
        for attempt in xrange(5):
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
