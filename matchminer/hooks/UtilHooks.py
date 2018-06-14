from matchminer.hooks import BaseHook
from matchminer.database import get_db

class NormalizeHook(BaseHook):

    @staticmethod
    def _recursive_check(search_dict, mapping):
        """
        Takes a dict with nested lists and dicts,
        and searches all dicts for a key of the field
        provided.
        """

        # loop over every key, value pair.
        for key, value in search_dict.iteritems():

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
                NormalizeHook._recursive_check(value, mapping)

            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        NormalizeHook._recursive_check(item, mapping)

    @staticmethod
    def entry_insert(resource, items):

        # get all records from db
        db = get_db()
        records = db['normalize'].find_one({"key": resource})
        if records is None:
            return
        mapping = records['values']

        # check all keys.
        for item in items:
            NormalizeHook._recursive_check(item, mapping)


    @staticmethod
    def entry_replace(resource, item, original):

        # get all records from db
        db = get_db()
        records = db['normalize'].find_one({"key": resource})
        if records is None:
            return
        mapping = records['values']

        # check all keys.
        NormalizeHook._recursive_check(item, mapping)
