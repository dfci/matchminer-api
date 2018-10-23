import os
import yaml
import json
import base64
import logging
import datetime
import StringIO
import requests
from flask_cors import CORS
from functools import wraps, update_wrapper
from flask import Blueprint, Response, make_response, render_template, request, redirect

from matchminer.database import get_db
from matchminer.utilities import set_updated, set_curated
from matchminer.components.oncore.oncore_utilities import OncoreSync
from matchminer.settings import API_TOKEN, API_ADDRESS, ONCORE_ADDRESS
from matchminer.security import authorize_oncore_curation

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s', )

oncore_blueprint = Blueprint('oncore_blueprint', __name__, template_folder="templates")
CORS(oncore_blueprint)


def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return update_wrapper(no_cache, view)


def oncore_auth_required(view):
    @wraps(view)
    def auth(*args, **kwargs):
        # check authorization
        not_authed = authorize_oncore_curation(request)
        if not_authed:
            resp = Response(response="not authorized route",
                            status=401,
                            mimetype="application/json")
            return resp
        return view(*args, **kwargs)
    return auth


def _yamlize(trial, trial_id):

    # turn into yaml
    fout = StringIO.StringIO()
    yaml.dump(yaml.load(json.dumps(trial)), fout, default_flow_style=False)
    output = fout.getvalue()

    # make downloadable response.
    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=%s.yml" % trial_id
    return response


def _render_trials():

    # set headers.
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + str(base64.b64encode(API_TOKEN + ':')),
    }

    # get the trial list from db.
    url = '%s/trial' % API_ADDRESS
    r = requests.get(url, headers=headers)
    trials = r.json()['_items']
    return render_template('curateInterface.html', trials=trials)


def _handle_exc(trial):
    """Field name "diseasesite_code" can come in from the yaml as string or integer but must be stored as a string"""

    for k, v in trial.iteritems():
        if k == 'disease_site_code':
            trial[k] = str(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    item = _handle_exc(item)
        elif isinstance(v, dict):
            trial[k] = _handle_exc(v)

    return trial


@oncore_blueprint.route('/curate', methods=['GET', 'POST'])
@nocache
@oncore_auth_required
def index():

    # set headers.
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + str(base64.b64encode(API_TOKEN + ':')),
    }

    # render the form.
    if request.method == 'GET':

        # render the page
        return _render_trials()

    # render the response
    else:
        # check if the post request has the file part
        if 'file' not in request.files:
            return "no file"
            #return redirect(request.url)

        # ensure file is present.
        file = request.files['file']
        if file.filename == '':
            return "empty filename"

        if file:

            # create trial.
            try:
                # load the trial.
                trial_new = yaml.load(file)

            except yaml.YAMLError as exc:

                # set yaml error.
                r_code = 512
                r_text = exc
                return "%s</br></br>%s" % (r_code, r_text)

            # Deal with "disease_site_code" type exception
            trial_new = _handle_exc(trial_new)

            # create the request.
            qstr = "where=%s" % json.dumps(({"protocol_no": trial_new['protocol_no']}))

            # get the trial list from db.
            url = '%s/trial?%s' % (API_ADDRESS, qstr)
            r = requests.get(url, headers=headers)
            output = r.json()

            # set curated on field
            trial_new = set_curated(trial_new)

            # detected a new trial.
            if len(output['_items']) == 0:

                # post the trial.
                url = '%s/trial' % (API_ADDRESS)
                r = requests.post(url, json=trial_new, headers=headers)
                r_code = r.status_code
                r_text = r.text

            else:

                # get info.
                trial = output['_items'][0]
                trial_id = str(trial['_id'])
                etag = trial['_etag']

                # strip meta
                for key in trial.keys():
                    if key[0] == "_":
                        del trial[key]
                trial['_id'] = trial_id

                # add the defaults
                headers['If-Match'] = etag

                # post the trial.
                url = '%s/trial/%s' % (API_ADDRESS, trial_id)
                r = requests.put(url, json=trial_new, headers=headers)
                r_code = r.status_code
                r_text = json.dumps(r.json(), indent=4)

            # render index if good.
            if r_code > 199 and r_code < 300:
                return _render_trials()

            # render the error
            return "%s</br></br>%s" % (r_code, r_text)


@oncore_blueprint.route('/curate/<trial_id>', methods=['GET'])
@nocache
@oncore_auth_required
def trial_request(trial_id):

    # determine mode.
    mode = request.args.get('delete')
    if mode == '1':
        delete = True
    else:
        delete = False

    # set headers.
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + str(base64.b64encode(API_TOKEN + ':')),
    }

    # create the request.
    qstr = "where=%s" % json.dumps(({"protocol_no": trial_id}))

    # get the trial list from db.
    url = '%s/trial?%s' % (API_ADDRESS, qstr)
    r = requests.get(url, headers=headers)
    output = r.json()

    # sanity check item.
    if len(output['_items']) == 0:
        return "No trial found with id: %s, try uploading from the file" % trial_id

    trial = r.json()['_items'][0]
    mongo_id = trial['_id']
    etag = trial['_etag']

    # add the defaults
    headers['If-Match'] = etag

    # strip meta
    for key in trial.keys():
        if key[0] == "_":
            del trial[key]

    # return the file if we aren't looking to delete it.
    if not delete:
        response = _yamlize(trial, trial_id)

    else:

        # issue delete.
        url = '%s/trial/%s' % (API_ADDRESS, mongo_id)
        r = requests.delete(url, headers=headers)

        if r.status_code < 300:
            return redirect("/curate")

        else:
            return r.text

    return response


@oncore_blueprint.route('/curate/oncore', methods=['POST'])
@nocache
@oncore_auth_required
def oncore():

    # get the protocol number
    protocol_no = request.form["protocol_no"]

    # set headers.
    headers = {
        'Content-Type': 'application/json'
    }

    # get the trial list from db.
    url = '%s?protocolNumber=%s' % (ONCORE_ADDRESS, protocol_no)
    r = requests.get(url, headers=headers)

    # test for resposne.
    if r.status_code >= 300:
        return r.text

    # get the trial and convert to yaml.
    trial = r.json()

    # return the file.
    return _yamlize(trial, protocol_no)


@oncore_blueprint.route('/api/utility/oncore/<string:protocol_no>', methods=['POST'])
def update_from_oncore(protocol_no):
    """
    This processes updates sent directly from oncore. The premise is that a seperate service will
    be polling the OnCore database and passing along the JSON formatted trials to here. This service will
    need to find the equivalent trial (if a new trial is POSTed here it should be ignored) and compute the update
    loging. The logic is divided into two parts:
    1. any non-curated field should be updated in MM seamlessly (such as trial and arm status)
    2. any curated field (such as match) should not be touched, and a change here should notify the curator
    via the email functionality.
    """

    db = get_db()

    # get the trial.
    on_trial = request.get_json(silent=True)

    # assert we have an existing one.
    mm_trial = db['trial'].find_one({"protocol_no": protocol_no})
    if mm_trial is None:
        logging.warning("oncore posted trial that is not in database: %s" % protocol_no)
        return json.dumps({"success": True})

    # USED TO GENERATE TESTING FILES.
    #with open("tests/data/oncore/%s.json" % protocol_no, "w") as fout:
    #    json.dump(oncore_trial, fout)

    # save relavent information for update.
    trial_id = str(mm_trial['_id'])
    etag = mm_trial['_etag']

    # call the comparison.
    cmp = OncoreSync()
    mm_trial, updated, changes = cmp.compare_trials(on_trial, mm_trial)
    cmp.send_email()

    # if it is updated then do the update.
    if updated:

        # strip meta
        for key in mm_trial.keys():
            if key[0] == "_":
                del mm_trial[key]
        mm_trial['_id'] = trial_id

        # set headers.
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Basic ' + str(base64.b64encode(API_TOKEN + ':')),
                   'If-Match': etag}

        # set last updated field
        mm_trial = set_updated(mm_trial)

        # post the trial.
        url = '%s/trial/%s' % (API_ADDRESS, trial_id)
        logging.info('PATCH %s' % url)
        r = requests.patch(url, json=mm_trial, headers=headers)
        r_code = r.status_code
        if 199 < r_code < 300:
            return json.dumps({"success": True})
        else:
            logging.error("error updating trial: %s" % protocol_no)

    # return success
    return json.dumps({"success": True})
