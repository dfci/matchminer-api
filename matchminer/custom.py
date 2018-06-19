import os
import uuid
import datetime
from flask import Blueprint, current_app as app
from flask import Response, request, render_template, redirect, session, make_response
from flask_cors import CORS
from urlparse import urlparse
from bson import ObjectId

from onelogin.saml2.auth import OneLogin_Saml2_Auth
import simplejson as json
import oncotreenx

from matchminer import database
from matchminer import settings
from matchminer import data_model
from matchminer.utilities import parse_resource_field, nocache, set_updated, run_matchengine
from matchminer.security import TokenAuth, authorize_custom_request
from matchminer.services.filter import Filter
from matchminer.services.match import Match
from matchminer.templates.emails.emails import EAP_INQUIRY_BODY
from matchminer.validation import check_valid_email_address
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import binascii

import logging

# logging
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', )

API_ADDRESS = os.getenv('API_ADDRESS', None)
API_TOKEN = os.getenv('API_TOKEN', None)

blueprint = Blueprint('', __name__, template_folder="templates/templates")
CORS(blueprint)


def _count_matches(matches, match_db):

    # extract counts
    counts = {
        "new": 0,
        "new_matches": 0,
        "pending": 0,
        "flagged": 0,
        'not_eligible': 0,
        'enrolled': 0,
        'contacted': 0,
        'eligible': 0,
        'deferred': 0
    }

    for match in matches:
        if match['FILTER_STATUS'] == 1:
            if match['MATCH_STATUS'] == 0:
                counts['new'] += 1

                if '_new_match' not in match or match['_new_match'] is False:
                    counts['new_matches'] += 1
                    match_db.update_one({'_id': match['_id']}, {'$set': {'_new_match': True}})

            elif match['MATCH_STATUS'] == 1:
                counts['pending'] += 1
            elif match['MATCH_STATUS'] == 2:
                counts['flagged'] += 1
            elif match['MATCH_STATUS'] == 3:
                counts['not_eligible'] += 1
            elif match['MATCH_STATUS'] == 4:
                counts['enrolled'] += 1
            elif match['MATCH_STATUS'] == 5:
                counts['contacted'] += 1
            elif match['MATCH_STATUS'] == 6:
                counts['eligible'] += 1
            elif match['MATCH_STATUS'] == 7:
                counts['deferred'] += 1
    return counts


def _count_matches_by_filter(matches, filters):

    # extract counts
    counts = {
        "new": 0,
        "pending": 0,
        "flagged": 0,
        'not_eligible': 0,
        'enrolled': 0,
        'contacted': 0,
        'eligible': 0,
        'deferred': 0
    }

    # separate matches by filter id
    filter_dict = {}
    for filt in filters:
        filter_dict[str(filt['_id'])] = counts.copy()

    for match in matches:

        if str(match['FILTER_ID']) not in filter_dict:
            continue

        if match['FILTER_STATUS'] == 1:
            if match['MATCH_STATUS'] == 0:
                filter_dict[str(match['FILTER_ID'])]['new'] += 1
            elif match['MATCH_STATUS'] == 1:
                filter_dict[str(match['FILTER_ID'])]['pending'] += 1
            elif match['MATCH_STATUS'] == 2:
                filter_dict[str(match['FILTER_ID'])]['flagged'] += 1
            elif match['MATCH_STATUS'] == 3:
                filter_dict[str(match['FILTER_ID'])]['not_eligible'] += 1
            elif match['MATCH_STATUS'] == 4:
                filter_dict[str(match['FILTER_ID'])]['enrolled'] += 1
            elif match['MATCH_STATUS'] == 5:
                filter_dict[str(match['FILTER_ID'])]['contacted'] += 1
            elif match['MATCH_STATUS'] == 6:
                filter_dict[str(match['FILTER_ID'])]['eligible'] += 1
            elif match['MATCH_STATUS'] == 7:
                filter_dict[str(match['FILTER_ID'])]['deferred'] += 1

    return filter_dict


@blueprint.route('/api/utility/matchengine', methods=['GET'])
def run_matchengine_route():
    """Launches the MatchEngine on the entire database"""

    # limit access to service account only
    auth = request.authorization
    if not auth:
        return json.dumps({"error": "no authorization supplied"})

    accounts = app.data.driver.db.user
    user = accounts.find_one({'token': auth.username})
    if not user:
        return json.dumps({"error": "not authorized"})

    # Match Engine #
    run_matchengine()

    return json.dumps({"success": True})


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
        for field, val in clinical.iteritems():
            if not isinstance(field, float) and not isinstance(field, int):
                try:
                    clinical[field] = str(val)
                except UnicodeEncodeError:
                    continue

    return json.dumps(clinical_ll)


@blueprint.route('/api/gi_patient_view', methods=['POST'])
@nocache
def gi_patient_view():
    """
    Inserts a GI patient_view document directly to the database.
    """

    # authorize request.
    not_authed = authorize_custom_request(request)
    if not_authed:
        resp = Response(response="not authorized route",
                        status=401,
                        mimetype="application/json")
        return resp

    # create document
    data = request.get_json()
    all_protocol_nos = data['all_protocol_nos']
    mrn = data['mrn']
    documents = []
    for protocol_no in all_protocol_nos:
        document = {
            'requires_manual_review': False,
            'user_user_name': 'gi-automation',
            'user_first_name': 'gi-automation',
            'user_last_name': 'gi-automation',
            'mrn': mrn,
            'view_date': datetime.datetime.now(),
            'protocol_no': protocol_no
        }
        documents.append(document)

    # insert into mongodb
    patient_view_conn = app.data.driver.db['patient_view']
    patient_view_conn.insert(documents)

    return json.dumps({"success": True}), 201


@blueprint.route('/api/eap_email', methods=['POST'])
@nocache
def eap_email():
    """
    Validates an email address, and, if passes, inserts an email object
    into the database.
    """

    # skip authorization
    data = request.get_json()
    email_address = data['email_address']

    # email address validation
    if not check_valid_email_address(email_address):
        return json.dumps({"success": False}), 403

    # create object
    subject = '[EAP] - New Inquiry from %s' % email_address
    body = '''<html><head></head><body>%s</body></html>''' % EAP_INQUIRY_BODY.format(email_address)
    email = {
        'email_from': settings.EMAIL_AUTHOR_PROTECTED,
        'email_to': settings.EMAIL_AUTHOR_PROTECTED,
        'subject': subject,
        'body': body,
        'cc': [],
        'sent': False,
        'num_failures': 0,
        'errors': []
    }

    # insert into mongodb
    email_conn = app.data.driver.db['email']
    email_conn.insert(email)

    return json.dumps({"success": True}), 201


@blueprint.route('/epic', methods=['POST'])
@nocache
def dispatch_epic():
    """
    Process request from EPIC, redirect to patient page.
    :return:
    """
    # data = request.get_json()
    # patientData = pad(data['data'], 128, 'pkcs7')
    # mrn = data['PatientID.SiteMRN']
    # print('===db===')
    # trial_match = app.data.driver.db['clinical'].find_one({'MRN': mrn})
    #
    # print('==========================================')
    # print(trial_match)
    # print('==========================================')
    # print(trial_match['_id'])
    #
    # cipher = AES.new('73FB225DE1361CA4A1232244EC4EA55A', AES.MODE_CBC, '0000000000000000')
    # testEncrypt = cipher.encrypt(pad('Field1|Field2|Field3|DSGGNCRASTKMSOXMR', 128))
    #
    # cipher2 = AES.new('73FB225DE1361CA4A1232244EC4EA55A', AES.MODE_CBC, '0000000000000000')
    # testDecrypt = unpad(cipher2.decrypt(testEncrypt), 128)
    #
    # print('==========================================')
    # print(binascii.hexlify(testEncrypt))
    # print('==========================================')
    # print(testDecrypt)
    # print('==========================================')
    return redirect('%s/#/dashboard/patients/%s?epic=true' % ('https://matchminer.dfci.harvard.edu:8443', '5ad4e83945a18d001835798f'), code=302)


@blueprint.route('/epic_ctrial', methods=['POST'])
@nocache
def dispatch_epic_clinical_trial():
    """
    Process request from EPIC, redirect to clinical trial page.
    :return:
    """

    return redirect('https://matchminer.dfci.harvard.edu:8443/#/clinicaltrials?epic=true', code=302)


@blueprint.route('/api/utility/count_match', methods=['GET'])
@nocache
def count_query():

    # no auth version.
    accounts = app.data.driver.db['user']
    if settings.NO_AUTH:

        # get the user_id
        user_id = str(request.args.get("user_id"))

        # deal with bad parameters.
        bad = False
        if user_id is not None:

            # find it.
            if user_id is not None:
                try:
                    user = accounts.find_one({"_id": ObjectId(user_id)})
                except:
                    user = accounts.find_one({"last_name": "Doe"})

            # deal with bad values.
            else:
                user = accounts.find_one({"last_name": "Doe"})

        else:
            bad = True

        # emit error.
        if bad:
            resp = Response(response="bad parameter for no-auth mode",
            status=401,
            mimetype="application/json")
            return resp

    else:
        # authorize request.
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
        if not_authed:
            resp = Response(response="not authorized route",
            status=401,
            mimetype="application/json")
            return resp

    # look for a team
    team_id = request.args.get("team_id")

    # extract counts
    db = database.get_db()
    m = Match(db)
    f = Filter(db)
    if team_id is None:
        matches = list()
        filters = list()
        for team_id in user['teams']:

            match_query = {'TEAM_ID': ObjectId(team_id)}
            match_proj = {'FILTER_ID': 1, 'MATCH_STATUS': 1, 'FILTER_STATUS': 1}
            matches += m.get_matches(query=match_query, proj=match_proj)

            filter_proj = {'_id': 1}
            filters += f.get_filter(proj=filter_proj, TEAM_ID=ObjectId(team_id))
    else:

        match_query = {'TEAM_ID': ObjectId(team_id)}
        match_proj = {'FILTER_ID': 1, 'MATCH_STATUS': 1, 'FILTER_STATUS': 1}
        matches = m.get_matches(query=match_query, proj=match_proj)

        filter_proj = {'_id': 1}
        filters = f.get_trial_watch_filter(proj=filter_proj, TEAM_ID=ObjectId(team_id))

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

        # loop over every-node and do text match.
        #results = set([onco_tree.node[n]['text'] for n in onco_tree.nodes()])
        #results.remove("root")
        #results = list(results)

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


@blueprint.route('/api/utility/autocomplete', methods=['GET'])
@nocache
def autocomplete_query():

    # parse parameters
    status, val = parse_resource_field()

    # parse the value.
    value = request.args.get("value")
    gene = request.args.get("gene")

    # bad args.
    if status == 1:
        return val

    # good args.
    resource, field = val

    # get the type.
    if resource == "genomic":
        schema = data_model.genomic_schema[field]['type']

    else:
        schema = data_model.clinical_schema[field]['type']

    # special cases.
    if resource == 'clinical' and field == 'ONCOTREE_PRIMARY_DIAGNOSIS_NAME':

        # make oncotree.
        onco_tree = oncotreenx.build_oncotree(settings.DATA_ONCOTREE_FILE)

        # loop over every-node and do text match.
        hit_set = set()
        for n in onco_tree.nodes():

            a = onco_tree.node[n]['text'].lower().decode('utf-8')
            b = value.lower()
            if a.count(b) > 0:

                # get predecessors and ancestors
                hit_set.add(n)
                hit_set = hit_set.union(set(onco_tree.predecessors(n)))
                hit_set = hit_set.union(set(onco_tree.successors(n)))

        # remove root.
        if 'root' in hit_set:
            hit_set.remove('root')

        # convert to full text.
        results = [onco_tree.node[n]['text'] for n in hit_set]

    else:

        # only support string and integer.
        if schema not in set(['string', 'integer']):
            data = json.dumps({'error': 'unsupported field type: %s' % schema})
            resp = Response(response=data,
                status=400,
                mimetype="application/json")
            return resp

        # handle string.
        db = app.data.driver.db
        if schema == "string":

            # finalize search term.
            term = '.*%s.*' % value

            # first make query.
            if gene is None:
                query = db[resource].find({
                    field: {'$regex': term, '$options': '-i'}
                })
            else:
                query = db[resource].find({"$and": [
                    {field: {'$regex': term, '$options': '-i'}},
                    {"$or": [
                        {'TRUE_HUGO_SYMBOL': gene},
                        {'CNV_HUGO_SYMBOL': gene},
                    ]}
                ]})


        else:

            # finalize the search term.
            term = "/^%s.*/.test(this.%s)" % (value, field)

            # first make the query
            if gene is None:
                query = db[resource].find({"$and": [
                    {'$where': term},
                ]})

            else:
                query = db[resource].find({"$and": [
                    {'$where': term},
                    {"$or": [
                        {'TRUE_HUGO_SYMBOL': gene},
                        {'CNV_HUGO_SYMBOL': gene},
                    ]}
                ]})

        # extract distinct from query
        results = query.distinct(field)

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


@blueprint.route('/api/docs/<string:page>', methods=['GET'])
@nocache
def hello(page=None):
    if page == "match":
        return render_template('match.html')
    else:
        return render_template('index.html')


def init_saml_auth(req):

    # load based on production information.
    saml_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'saml'))
    saml_file = os.path.join(saml_dir, settings.SAML_SETTINGS)

    json_data_file = open(saml_file, 'r')
    settings_data = json.load(json_data_file)
    json_data_file.close()

    # create auth object with required settings.
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
        response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0')
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
            #user_name = auth.get_nameid()
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
            print "user is not found in database"
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
                # response = Response(response="not authorized",
                #    status=308,
                #    mimetype="application/json")
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
            attributes = session['samlUserdata'].items()

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
