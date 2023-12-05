import os
import uuid
import datetime
import base64
import threading

from flask import Blueprint, current_app as app
from flask import Response, request, render_template, redirect, session, make_response
from flask_cors import CORS
from urllib.parse import urlparse
from bson import ObjectId

import simplejson as json
import oncotreenx
from requests import post, get
from requests.auth import HTTPBasicAuth

from matchminer import settings, database
from matchminer import data_model
import matchminer.miner
from matchminer.elasticsearch import reset_elasticsearch
from matchminer.miner import _count_matches_by_filter
from matchminer.settings import *
from matchminer.utilities import parse_resource_field, nocache, reannotate_trials
from matchminer.security import auth_required
import logging

import matchengine.internals.engine
# logging
from wincrypto import CryptCreateHash, CryptDeriveKey, CryptHashData, CryptDecrypt, CryptEncrypt
from wincrypto.constants import CALG_SHA1, CALG_AES_128

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s', )

blueprint = Blueprint('', __name__, template_folder="templates/templates")
CORS(blueprint)


@blueprint.route('/api/es/<path:path>', methods=['POST', 'GET'])
def proxy(path):
    """
    Proxy all Elasticsearch requests
    """
    try:
        r = None
        url = f"{ES_URL}/{path}"
        headers = dict(request.headers)
        headers.pop('Host')
        if request.method == 'POST':
            data = json.dumps(request.get_json())

            if settings.NO_AUTH:
                r = post(url=url,
                         data=data,
                         headers=headers)
            else:
                r = post(url=url,
                         auth=HTTPBasicAuth(ES_USER, ES_PASSWORD),
                         data=data,
                         headers=headers)

        elif request.method == 'GET':
            if settings.NO_AUTH:
                r = get(url=url,
                        headers=headers)
            else:
                r = get(url=url,
                        auth=HTTPBasicAuth(ES_USER, ES_PASSWORD),
                        headers=headers)

        return Response(
           response=json.dumps(r.json()),
           status=r.status_code,
           mimetype="application/json"
        )
    except Exception as e:
        msg = 'Error while fetching data from elasticsearch'
        logging.error(msg)
        raise


@blueprint.route('/api/info', methods=['GET'])
def api_info():
    info = {
        "server": SERVER,
        "mongo_db": MONGO_DBNAME
    }
    return json.dumps(info), 200


@blueprint.route('/api/vip_clinical', methods=['GET'])
def get_vip_clinical():
    """Returns a clinical document with patient name information"""

    db = app.data.driver.db

    # limit access to service account only
    auth = request.authorization
    if not auth:
        return json.dumps({"error": "no authorization supplied"})

    accounts = db.user
    user = accounts.find_one({'token': auth.username})
    if not user:
        return json.dumps({"error": "not authorized"})

    query = {}
    params = request.args.get('where', None)
    if params is not None:
        query = json.loads(request.args.get('where'))

    if 'get_new_patients_only' in query:
        query['_created'] = {'$gte': datetime.datetime.strptime(query['data_push_id'], '%Y-%m-%d %X')}
        del query['get_new_patients_only']

    clinical_ll = list(db.clinical.find(query))
    for clinical in clinical_ll:
        for field, val in clinical.items():
            if not isinstance(field, float) and not isinstance(field, int):
                try:
                    clinical[field] = str(val)
                except UnicodeEncodeError:
                    continue

    return json.dumps(clinical_ll)


@blueprint.route('/api/utility/send_emails', methods=['POST'])
@nocache
@auth_required
def send_emails(run_id=None):
    if request.data:
        data = request.get_json()
        run_id = data['run_id'] if 'run_id' in data else None

    if isinstance(run_id, str):
        run_id = [run_id]

    matchminer.miner.email_matches(run_id)
    return json.dumps({"success": True}), 201


@blueprint.route('/api/rerun_filters', methods=['POST'])
@auth_required
def rerun_filters_endpoint(silent=False):
    """
    Trigger filter run.
    Run in a separate thread to return response & not run multiple full filter runs simultaneously.
    :param silent: Suppress email notification. Will generate emails by default
    :return:
    """

    db = database.get_db()
    logging.info("rerun filters started")

    # Allow default values to be overridden in POST data params
    datapush_id = None
    silent = False
    if request.data:
        data = request.get_json()
        datapush_id = data.get('data_push_id', None)
        silent = data.get('silent', None)

    is_currently_running = list(db.active_processes.find())
    if len(is_currently_running) > 0:
        msg = "Filters already running"
        response = {msg: True}
    else:
        msg = f"Full filters run started. Datapush id: {str(datapush_id)}. Silent: {str(silent)}"
        response = {msg: True}
        thread = threading.Thread(target=matchminer.miner.start_filter_run, daemon=True, args=[silent, datapush_id])
        thread.start()

    logging.info(msg)
    resp = Response(response=json.dumps(response),
                    status=200,
                    mimetype="application/json")

    return resp


@blueprint.route('/api/is_matchengine_running', methods=['GET'])
def is_engine_running():
    db = database.get_db()

    running_processes = list(db.active_processes.find())
    is_running = True if len(running_processes) > 0 else False

    logging.info(f"/api/is_matchengine_running {str(is_running)}")
    resp = Response(response=json.dumps({"is_running": is_running}),
                    status=200,
                    mimetype="application/json")
    return resp


@blueprint.route('/api/reannotate_trials', methods=['POST'])
@nocache
@auth_required
def reannotate_trials_api():
    """
    Deletes and re-adds all trials.
    Regenerates all _summary, _elasticsearch and _suggest fields.
    :return:
    """
    reannotate_trials()
    resp = Response(response=json.dumps({"success": True}),
                    status=200,
                    mimetype="application/json")
    return resp

@blueprint.route('/api/run_matchengine', methods=['POST'])
@nocache
@auth_required
def run_matchengine():
    """
    Runs MatchEngine to rebuild trial matches.
    NOTE: DO NOT use this in production; use matchengine-runner instead.
    :return:
    """
    with matchengine.internals.engine.MatchEngine(
        match_on_deceased=False,
        match_on_closed=True,
        db_name="matchminer") as me_prod:
        me_prod.get_matches_for_all_trials()
        me_prod.update_all_matches()

    reset_elasticsearch()
    resp = Response(response=json.dumps({"success": True}),
                    status=200,
                    mimetype="application/json")
    return resp

@blueprint.route('/api/reset_elasticsearch', methods=['POST'])
@nocache
@auth_required
def reset_elasticsearch_endpoint():
    """
    Deletes and recreates elasticsearch index. Reloads settings and mappings
    :return:
    """
    reset_elasticsearch()
    resp = Response(response=json.dumps({"success": True}),
                    status=200,
                    mimetype="application/json")
    return resp


@blueprint.route('/api/gi_patient_view', methods=['POST'])
@nocache
@auth_required
def gi_patient_view():
    """
    Inserts a GI patient_view document directly to the database.
    """

    # create document
    data = request.get_json()
    all_protocol_nos = data['all_protocol_nos']
    mrn = data['mrn']

    # use the given view date if supplied in the POST body
    if 'use_view_date' in data:
        view_date = datetime.datetime.strptime(data['use_view_date'], '%Y-%m-%d %X')
    else:
        view_date = datetime.datetime.now()

    documents = []
    for protocol_no in all_protocol_nos:
        document = {
            'requires_manual_review': True,
            'user_user_name': 'gi-automation',
            'user_first_name': 'gi-automation',
            'user_last_name': 'gi-automation',
            'mrn': mrn,
            'view_date': view_date,
            'protocol_no': protocol_no
        }
        documents.append(document)

    # insert into mongodb
    if len(documents) > 0:
        patient_view_conn = app.data.driver.db['patient_view']
        patient_view_conn.insert(documents)

    return json.dumps({"success": True}), 201


def generate_encryption_key_epic(shared_secret):
    """
    Create hashed key based on CryptDeriveKey from Microsoft Desktop Cryptography package.
    :param shared_secret:
    :return:
    """
    sha1_hasher = CryptCreateHash(CALG_SHA1)
    CryptHashData(sha1_hasher, shared_secret.encode('utf-8'))
    aes_key = CryptDeriveKey(sha1_hasher, CALG_AES_128)
    return aes_key


def encrypt_epic(aes_key, unencrypted_data):
    """
    NOTE: This function is used for testing and to ensure that the encryption mechanism used in MM matches the encryption schema used in EPIC.
    :param aes_key: <AES_128> An object created in the WinCrypto Library.
    :param unencrypted_data: <str> Whatever text you would like to encrypt
    :return:
    """

    encrypted = CryptEncrypt(aes_key, unencrypted_data.encode('utf-8'))

    # Display in human readable format
    encrypted_readable = base64.b64encode(encrypted).decode('utf-8')
    return encrypted_readable


def decrypt_epic(aes_key, encrypted_data):
    """
    Decrypt string encrypted with AES128 ciphering algorithm using custom wincrypt hash key
    :param aes_key: <AES_128> Object created by WinCrypto Library
    :param encrypted_data: Raw string data
    :return:
    """
    # Decode encrypted string
    decoded = base64.b64decode(encrypted_data)

    # Decrypt decoded string
    decoded_readable = CryptDecrypt(aes_key, decoded).decode('utf-8')
    return decoded_readable


def build_redirect_url_epic(user, trial_match):
    """
    When redirecting to a patient for integration with EPIC, set appropriate tokens, headers, and cookies
    :param user:
    :param trial_match:
    :return:
    """
    db = database.get_db()

    # Set token. Must match token set in cookie
    token = str(uuid.uuid4())
    db['user'].update_one({'_id': user['_id']}, {
        '$set': {'token': token, 'last_auth': datetime.datetime.now()}
    })

    # Build redirect URL
    patient_id = str(trial_match["_id"])
    url = FRONT_END_ADDRESS + 'dashboard/patients/' + patient_id + '?epic=true'
    redirect_to_patient = redirect(url)
    logging.info('[EPIC] redirect to URL: ' + url)

    # Build response headers
    response = app.make_response(redirect_to_patient)
    response.headers.add('Authorization', 'Basic' + base64.b64encode(f'{token}:'.encode('utf-8')).decode())
    response.headers.add('Last-Modified', datetime.datetime.now())
    response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0')
    response.headers.add('Pragma', 'no-cache')
    response.headers.add('Content-Type', 'application/json')
    response.headers.add('Location', url)

    # Set cookies
    response.set_cookie('user_id', value=str(user['_id']), expires=0)
    response.set_cookie('team_id', value=str(user['teams'][0]), expires=0)
    response.set_cookie('token', value=token, expires=0)
    return response


@blueprint.route('/epic', methods=['POST', 'GET'])
@nocache
def dispatch_epic():
    """
    Process request from EPIC, redirect to patient page.
    :return:
    """
    if request.method == 'GET':
        return 'Method unsupported'

    db = database.get_db()
    logging.info('[EPIC] request origin: ' + str(request.remote_addr))

    # Get patient data off request body
    encrypted_patient_data = str(request.form['data'])

    # Generate valid encryption key
    aes_key = generate_encryption_key_epic(EPIC_DECRYPT_TOKEN)

    # Decrypt encrypted string
    decrypted = decrypt_epic(aes_key, encrypted_patient_data)

    # JSON format data
    epic_data = json.loads(decrypted)
    logging.info('[EPIC] ' + str(epic_data))

    # Get user
    user = db['user'].find_one({'user_name': str(epic_data['UserNID']).lower()})

    log = {k.replace('.', '_'): v for k, v in epic_data.items()}
    log['accessed_at'] = datetime.datetime.now()
    log['exists_in_mm'] = True
    log['is_BWH_MRN'] = False

    # Redirect to error page if user is not authorized
    if user is None:
        logging.error('[EPIC] Error: No user found in db. UserID: ' + epic_data['UserNID'])
        error_url = FRONT_END_ADDRESS + 'epic-auth-error'
        redirect_to_patient = redirect(error_url)
        response = app.make_response(redirect_to_patient)
        response.headers.add('Location', error_url)
        db.epic_log.insert(log)
        return response

    # Get patient MRN
    mrn = epic_data['PatientID.SiteMRN']

    # Find patient
    patient = db['clinical'].find_one({'MRN': mrn})

    # check BWH MRN
    if patient is None:
        logging.error('[EPIC] [BWH] No DFCI MRN present on request: Looking up using BWH MRN... ')
        log['exists_in_mm'] = False
        patient = db['clinical'].find_one({'ALT_MRN': mrn})

        if patient is not None:
            log['is_BWH_MRN'] = True
        else:
            # If still no patient redirect to error page
            msg = '[EPIC] Error: No clinical document found matching MRN: %s' % mrn
            log['is_BWH_MRN'] = False
            logging.error(msg)

            email_item = {
                'email_from': EMAIL_AUTHOR_PROTECTED,
                'email_to': EMAIL_AUTHOR_PROTECTED,
                'subject': "[EPIC] MRN Error",
                'body': msg,
                'cc': [],
                'sent': False,
                'num_failures': 0,
                'errors': []
            }
            db.email.insert(email_item)

            # build url and redirect to error page
            error_url = FRONT_END_ADDRESS + 'epic-mrn-error'
            redirect_to_patient = redirect(error_url)
            response = app.make_response(redirect_to_patient)
            response.headers.add('Location', error_url)
            db.epic_log.insert(log)
            return response

    db.epic_log.insert(log)
    response = build_redirect_url_epic(user, patient)
    return response


@blueprint.route('/epic_ctrial', methods=['POST', 'GET'])
@nocache
def dispatch_epic_clinical_trial():
    """
    Process request from EPIC, redirect to clinical trial page.
    :return:
    """
    if request.method == 'GET':
        return 'Method unsupported'

    url = FRONT_END_ADDRESS + 'clinicaltrials?epic=true'
    redirect_to_search = redirect(url)
    logging.info('[EPIC] redirect to search URL: ' + url)

    # Build response headers
    response = app.make_response(redirect_to_search)
    response.headers.add('Location', url)

    # Set cookies
    response.set_cookie('epic', value='true', expires=0)
    return response


@blueprint.route('/api/utility/count_match', methods=['GET'])
@nocache
@auth_required
def count_query():
    # no auth version.
    accounts = app.data.driver.db['user']
    team_id = request.args.get("team_id")
    token = request.authorization.username

    # find the user.
    user = accounts.find_one({'token': token})

    # extract counts
    db = database.get_db()
    if team_id is None:
        matches = list()
        filters = list()
        for team_id in user['teams']:
            match_query = {'TEAM_ID': ObjectId(team_id), "is_disabled": False}
            match_proj = {'FILTER_ID': 1, 'MATCH_STATUS': 1, 'FILTER_STATUS': 1}
            matches += list(db.match.find(match_query, match_proj))

            filter_proj = {'_id': 1}
            filter_query = {'status': 1, 'temporary': False, 'TEAM_ID': team_id}
            filters += list(db.filter.find(filter_query, filter_proj))
    else:

        match_query = {'TEAM_ID': ObjectId(team_id), "is_disabled": False}
        match_proj = {'FILTER_ID': 1, 'MATCH_STATUS': 1, 'FILTER_STATUS': 1}
        matches = list(db.match.find(match_query, match_proj))

        filter_proj = {'_id': 1}
        filter_query = {'status': 1, 'temporary': False, 'TEAM_ID': team_id}
        filters = list(db.filter.find(filter_query, filter_proj))

    counts = _count_matches_by_filter(matches, filters)

    # encode response.
    data = json.dumps(counts)
    resp = Response(response=data,
                    status=200,
                    mimetype="application/json")

    return resp


@blueprint.route('/api/utility/unique', methods=['GET'])
@nocache
def unique_query():
    # parse parameters
    status, val = parse_resource_field()

    # bad args.
    if status == 1:
        return val

    # good args.
    resource, field = val

    # special case for oncotree.
    if resource == 'clinical' and field == 'ONCOTREE_PRIMARY_DIAGNOSIS_NAME':

        # make oncotree.
        onco_tree = oncotreenx.build_oncotree(settings.DATA_ONCOTREE_FILE)

        # turn into
        results = list()
        for n in onco_tree.nodes():
            tmp = {
                'text': onco_tree.node[n]['text'],
                'code': n
            }
            results.append(tmp)

    else:

        # search for this field.
        db = app.data.driver.db
        results = db[resource].distinct(field)

        # remove non.
        tmp = set(results)
        if None in tmp:
            tmp.remove(None)
            results = list(tmp)

    # encode response.
    data = json.dumps({'resource': resource, 'field': field, 'values': results})
    resp = Response(response=data,
                    status=200,
                    mimetype="application/json")

    return resp


@blueprint.route('/api/delete_genomic_by_sample', methods=['GET'])
@nocache
@auth_required
def delete_genomic_by_sample():
    sample_id = request.args.get("SAMPLE_ID")

    if sample_id is not None:
        database.get_collection('genomic').delete_many({"SAMPLE_ID": sample_id})

    # encode response.
    resp = Response(response={"success": True},
                    status=200,
                    mimetype="application/json")

    return resp


@blueprint.route('/api/utility/autocomplete', methods=['GET'])
@nocache
def autocomplete_query():
    db = app.data.driver.db

    # parse parameters
    status, val = parse_resource_field()

    # parse the value.
    gene = request.args.get("gene")

    # bad args.
    if status == 1:
        return val

    resource, field = val
    results = list(db.genomic.aggregate([
        {"$match": {"TRUE_HUGO_SYMBOL": gene, field: {"$ne": None}}},
        {"$group": {"_id": "$TRUE_HUGO_SYMBOL", field: {"$addToSet": f"${field}"}}},
    ]))

    if len(results) > 0 and field in results[0]:
        results = results[0][field]
    else:
        results = []

    # encode response.
    data = json.dumps({'resource': resource, 'field': field, 'values': results})
    resp = Response(response=data,
                    status=200,
                    mimetype="application/json")

    return resp


@blueprint.route('/api/utility/get_panel', methods=['GET'])
@nocache
def get_panel():
    db = app.data.driver.db
    panel_arg = request.args.get("panel")
    panel = list(db.panel.find({"name": panel_arg}))

    if len(panel) > 0:
        panel = panel[0]
    else:
        panel = {}

    data = json.dumps({"panel": panel['panel']})
    resp = Response(response=data,
                    status=200,
                    mimetype="application/json")

    return resp

def init_saml_auth(req):
    # load based on production information.
    saml_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'saml'))
    saml_file = os.path.join(saml_dir, settings.SAML_SETTINGS)

    json_data_file = open(saml_file, 'r')
    settings_data = json.load(json_data_file)
    json_data_file.close()

    # create auth object with required settings.
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    auth = OneLogin_Saml2_Auth(req, settings_data)

    # return it
    return auth, settings_data


def prepare_flask_request(request):
    # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
    url_data = urlparse(request.url)
    return {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.host,
        'server_port': url_data.port,
        'script_name': request.path,
        'get_data': request.args.copy(),
        'post_data': request.form.copy()
    }


@blueprint.route('/', methods=['GET', 'POST'])
@nocache
def saml(page=None):
    if settings.NO_AUTH:
        return json.dumps({"API up": True})

    req = prepare_flask_request(request)
    auth, settings_data = init_saml_auth(req)
    errors = []
    not_auth_warn = False
    success_slo = False
    attributes = False
    paint_logout = False

    if 'sso' in request.args:
        logging.info("sso request")
        session.clear()
        url = auth.login(force_authn=True)

        redirect_to_index = redirect(url)
        response = app.make_response(redirect_to_index)
        response.headers.add('Last-Modified', datetime.datetime.now())
        response.headers.add('Cache-Control',
                             'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0')
        response.headers.add('Pragma', 'no-cache')
        response.headers.add('Expires', '-1')

        response.set_cookie('MMTOKEN', value='', expires=0)
        response.set_cookie('SignOnDefault', value='', expires=0)
        response.set_cookie('PHSPSPWEB2-80-PORTAL-PSJSESSIONID', value='', expires=0)
        response.set_cookie('PS_LOGINLIST', value='', expires=0)
        response.set_cookie('PS_TOKEN', value='', expires=0)
        response.set_cookie('PS_TOKENEXPIRE', value='', expires=0)
        response.set_cookie('session', value='', expires=0)
        return response

    elif 'sso2' in request.args:
        logging.info("sso2 request")
        return_to = '%sattrs/' % request.host_url
        return redirect(auth.login(return_to))

    elif 'slo' in request.args:
        logging.info("slo request")

        name_id = None
        session_index = None
        if 'samlNameId' in session:
            name_id = session['samlNameId']
        if 'samlSessionIndex' in session:
            session_index = session['samlSessionIndex']

        # invalidate token.
        db = app.data.driver.db
        if settings.MM_SETTINGS == "DEV":

            # configure for one login.
            user = db['user'].find_one({'email': name_id})

        else:

            # configure for production.
            user_name = name_id
            user = db['user'].find_one({'user_name': user_name})

        # clear the session.
        session.clear()

        # setup re-direction.
        redirect_url = settings.SLS_URL
        redirect_to_index = redirect(redirect_url)
        response = app.make_response(redirect_to_index)
        response.set_cookie('user_id', value="", expires=0)
        response.set_cookie('team_id', value="", expires=0)
        response.set_cookie('token', value="", expires=0)

        # redirect to error if user not present.
        if user is None:
            print("user is not found in database")
            return response

        # disable the login.
        result = db['user'].update_one({'_id': user['_id']}, {'$set': {
            'token': str(uuid.uuid4()),
            'last_auth': datetime.datetime.now()
        }})

        # redirect to the slo at idp
        return response

    # user has authenticated.
    elif 'acs' in request.args:

        logging.info("acs request")
        auth.process_response()
        errors = auth.get_errors()
        not_auth_warn = not auth.is_authenticated()

        # make sure there are no login errors.
        if len(errors) == 0:

            # determine how to identify user.
            db = app.data.driver.db
            key = ""
            if settings.MM_SETTINGS == "DEV":

                # configure for one login.
                user_email = auth.get_attributes()['User.email'][0]
                user = db['user'].find_one({'email': user_email})
                key = user_email

            else:

                # configure for production.
                user_name = auth.get_nameid()
                user = db['user'].find_one({'user_name': user_name})
                key = user_name

            # redirect to error if user not present.
            if user is None:
                logging.info("user not found: %s" % key)
                redirect_to_index = redirect("/?not_auth=1")
                response = app.make_response(redirect_to_index)
                response.set_cookie('user_id', value='', expires=0)
                response.set_cookie('team_id', value='', expires=0)
                response.set_cookie('token', value='', expires=0)
                response.set_cookie('not_auth', value='1', expires=0)
                return response

            # build session.
            session['samlUserdata'] = auth.get_attributes()
            session['samlNameId'] = auth.get_nameid()
            session['samlSessionIndex'] = auth.get_session_index()
            token = auth.get_session_index()

            # get the team.
            team_id = user['teams'][0]

            # set token.
            result = db['user'].update_one({'_id': user['_id']}, {
                '$set': {'token': token, 'last_auth': datetime.datetime.now()}
            })

            # set redirect url.
            redirect_url = settings.ACS_URL

            logging.info("redirecting %s" % redirect_url)
            redirect_to_index = redirect(redirect_url)
            response = app.make_response(redirect_to_index)
            response.set_cookie('user_id', value=str(user['_id']))
            response.set_cookie('team_id', value=str(team_id))
            response.set_cookie('token', value=str(token))
            return response

        else:
            logging.info("acs failed: %s %s" % (str(errors), str(not_auth_warn)))

            redirect_to_index = redirect("/")
            response = app.make_response(redirect_to_index)
            return response

    elif 'sls' in request.args:
        logging.info("sls request")

        dscb = lambda: session.clear()
        url = auth.process_slo(keep_local_session=False, delete_session_cb=dscb)
        errors = auth.get_errors()
        if len(errors) == 0:
            if url is not None:
                return redirect(url)
            else:
                success_slo = True

        # clear the session.
        session.clear()

        # set redirect url.
        redirect_url = settings.SLS_URL

        logging.info("redirecting: %s" % redirect_url)
        redirect_to_index = redirect(redirect_url)
        response = app.make_response(redirect_to_index)
        response.set_cookie('user_id', value="", expires=0)
        response.set_cookie('team_id', value="", expires=0)
        response.set_cookie('token', value="", expires=0)
        return response

    # serve up the root page.
    return app.send_static_file('index.html')


@blueprint.route('/saml/attrs/', methods=['GET'])
def attrs():
    paint_logout = False
    attributes = False

    if 'samlUserdata' in session:
        paint_logout = True
        if len(session['samlUserdata']) > 0:
            attributes = list(session['samlUserdata'].items())

    return render_template('attrs.html', paint_logout=paint_logout,
                           attributes=attributes)


@blueprint.route('/saml/metadata/', methods=['GET'])
def metadata():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    settings = auth.get_settings()
    metadata = settings.get_sp_metadata()
    errors = settings.validate_metadata(metadata)

    if len(errors) == 0:
        resp = make_response(metadata, 200)
        resp.headers['Content-Type'] = 'text/xml'
    else:
        resp = make_response(errors.join(', '), 500)
    return resp
