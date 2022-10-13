"""Copyright 2016 Dana-Farber Cancer Institute"""

import os

from cerberus1 import Validator
from cerberus1 import schema_registry
from matchminer.matchengine_v1 import schema as sch
from matchminer.matchengine_v1.utilities import get_db

class ConsentValidatorCerberus(Validator):

    def __init__(self, schema, *args, **kwargs):
        super(ConsentValidatorCerberus, self).__init__(schema, *args, **kwargs)
        self.schema = schema
        MONGO_URI = os.getenv("MONGO_URI")
        self.db = get_db(MONGO_URI)

    def _validate_consented(self, consented, field, value):

        # skip if not necessary
        if not consented:
            return

        # run the consent.
        if not check_consent(self.document):
            self._error(field, "Not consented")

    def _validate_match(self, match, field, value):
        schema_registry.add('yaml_match_schema', sch.yaml_match_schema)
        schema_registry.add('yaml_genomic_schema', sch.yaml_genomic_schema)
        schema_registry.add('yaml_clinical_schema', sch.yaml_clinical_schema)
        v = Validator(sch.yaml_match_schema)

        v.validate(value[0])

        if len(v.errors) > 0:
            self._error(field, v.errors)

    def _validate_normalized(self, normalized, field, value):
        ''' use normalization dictionary to control values
        return validation error if it isn't a true value
        in the dictionary'''

        # load the mapping
        normalize_table = self.db['normalize'].find_one()

        if not normalize_table:
            return

        for key, val in list(value.items()):
            if (isinstance(val, str) or isinstance(val, str)) and val[0] == "!":
                val = val[1:]

            if key == 'oncotree_primary_diagnosis':
                if val not in list(normalize_table['values']['oncotree_primary_diagnosis'].values()):
                    self._error(field, "%s is not a valid value for oncotree_primary_diagnosis" % val)

            elif key == 'hugo_symbol':
                if 'hugo_symbol' in normalize_table['values'] and val not in normalize_table['values']['hugo_symbol']:
                    self._error(422, "%s is not a valid hugo symbol" % val)

            elif isinstance(val, dict):
                self._validate_normalized(normalized, field, val)

            elif isinstance(val, list):
                for subitem in val:
                    if isinstance(subitem, dict):
                        self._validate_normalized(normalized, field, subitem)

    def _validate_unique(self, unique, field, value):
        """Rejects validation if the database already contains the given value in the given field"""
        ids = self.db.trial.find().distinct(field)
        if value in ids:
            # TODO get the error handler to work with self._error
            raise ValueError("%s is not a unique protocol id" % str(value))


def check_consent(clinical):

    # check conset.
    if 'QUESTION1_YN' not in clinical:
        return False

    cnd1 = clinical['QUESTION1_YN'] == 'Y'
    cnd3 = clinical['QUESTION3_YN'] == 'Y'
    cndc = clinical['CRIS_YN'] == 'Y'

    if not cnd1 or not cnd3 or not cndc:
        return False

    return True

