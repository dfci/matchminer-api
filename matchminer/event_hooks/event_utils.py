import json

import flask
from flask import abort, Response

from matchminer.database import get_db


def dry_flag(resource_name, items):
    """
    If ?dry=true is passed as URL param, abort insert request and return success.
    If a request has made it to this function it has already passed validation.
    """
    if flask.request.args.get('dry', None):
        msg = {
            "success": True,
            "inserted": False,
            "message": "Dry param detected. Document(s) has passed cereberus validation."
        }
        return abort(Response(response=json.dumps(msg), status=200))


def _recursive_check(search_dict, mapping):
    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key of the field
    provided.
    """

    # loop over every key, value pair.
    for key, value in search_dict.items():

        # look for field in dictionary.
        if key in mapping:

            # build mapping
            vals = [value]
            check_vals = vals[:]

            if value and value[0] == "!":
                check_vals.append(value[1:])

            # check for them and replace.
            for original_val, val in zip(vals, check_vals):
                if val in mapping[key]:
                    search_dict[key] = mapping[key][original_val]

        elif isinstance(value, dict):
            _recursive_check(value, mapping)

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _recursive_check(item, mapping)


def entry_insert(resource, items):
    # TODO move logic into UI.

    # get all records from db
    db = get_db()
    records = db['normalize'].find_one({"key": resource})
    if records is None:
        return
    mapping = records['values']

    # check all keys.
    for item in items:
        _recursive_check(item, mapping)


def entry_replace(resource, item, original):
    # TODO move logic into UI.

    # get all records from db
    db = get_db()
    records = db['normalize'].find_one({"key": resource})
    if records is None:
        return
    mapping = records['values']

    # check all keys.
    _recursive_check(item, mapping)
