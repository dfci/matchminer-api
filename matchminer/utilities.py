import datetime
from functools import wraps, update_wrapper
from datetime import datetime
from flask import Response, request, make_response

from matchminer import database
from matchminer.event_hooks.trial import trial_insert

from .settings import *
from mattermostdriver import Driver

# logging
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', )


def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return update_wrapper(no_cache, view)


def parse_resource_field():
    # parse args.
    resource = request.args.get("resource")
    field = request.args.get("field")

    # sanity check.
    if resource is None or field is None:
        data = json.dumps({'error': 'missing parameters'})
        resp = Response(response=data,
                        status=400,
                        mimetype="application/json")

        return 1, resp

    # ensure resource is in whitelist.
    whitelist = set(["clinical", "genomic"])
    if resource not in whitelist:
        data = json.dumps({'error': 'bad resource: %s' % resource})
        resp = Response(response=data,
                        status=400,
                        mimetype="application/json")

        return 1, resp

    # don't allow trixsy fields.
    tmp = field.lower()
    cnd1 = tmp.count("_id") > 0
    cnd2 = tmp.count("team")
    cnd3 = tmp.count("user")
    if cnd1 or cnd2 or cnd3:
        data = json.dumps({'error': 'bad field: %s' % field})
        resp = Response(response=data,
                        status=400,
                        mimetype="application/json")

        return 1, resp

    return 0, (resource, field)


def set_curated(mtrial):
    """Sets the date of last curation. Determined by POSTs/PUTs through the curation interface."""
    mtrial['curated_on'] = datetime.now().strftime('%B %d, %Y')
    mtrial['last_updated'] = datetime.now().strftime('%B %d, %Y')
    return mtrial


def set_updated(otrial):
    """Sets the last updated date. Determined by Oncore updates."""
    otrial['last_updated'] = datetime.now().strftime('%B %d, %Y')
    return otrial


def reannotate_trials():
    db = database.get_db()
    trials = list(db['trial'].find())

    # modify trials to be inserted in bulk later
    trial_insert(trials)

    # re-insert.
    for trial in trials:
        db['trial'].delete_one({'_id': trial['_id']})
        db['trial'].insert_one(trial)

    logging.info("Re-annotating trials complete")
