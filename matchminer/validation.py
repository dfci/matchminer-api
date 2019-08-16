import re

from eve.io.mongo import Validator as EveValidator
from cerberus import Validator as CerberusValidator
from cerberus1 import Validator
from cerberus1 import schema_registry
from matchminer import data_model
from matchminer.database import get_db


class ConsentValidatorEve(EveValidator):

    def _validate_consented(self, consented, field, value):

        # skip if not necessary
        if not consented:
            return

        # run the consent.
        if not check_consent(self.document):
            self._error(field, "Not consented")

    def __signature_exception(self, item):

        signatures = ['mmr_status',
                      'ms_status',
                      'tobacco_signature',
                      'uva_signature',
                      'temozolomide_signature',
                      'apobec_signature',
                      'pole_signature',
                      'tmb_numerical']

        if isinstance(item, dict):
            for k, v in item.iteritems():
                if k == 'genomic':
                    if v in signatures:
                        item[k]['hugo_symbol'] = 'None'
                        return
                    elif isinstance(v, dict):
                        self.__signature_exception(v)

                elif isinstance(v, dict) or isinstance(v, list):
                    self.__signature_exception(v)

        elif isinstance(item, list):
            for subitem in item:
                self.__signature_exception(subitem)

    def _validate_match(self, match, field, value):

        for item in value:
            self.__signature_exception(item)

        schema_registry.add('yaml_match_schema', data_model.yaml_match_schema)
        schema_registry.add('yaml_genomic_schema', data_model.yaml_genomic_schema)
        schema_registry.add('yaml_clinical_schema', data_model.yaml_clinical_schema)
        v = Validator(data_model.yaml_match_schema)

        v.validate(value[0])

        if len(v.errors) > 0:
            self._error(field, v.errors)

    def _validate_normalized(self, normalized, field, value):
        ''' use normalization dictionary to control values
        return validation error if it isn't a true value
        in the dictionary'''

        # load the mapping
        db = get_db()
        normalize_table = db['normalize'].find_one()

        if not normalize_table:
            return

        for key, val in value.iteritems():
            if (isinstance(val, str) or isinstance(val, unicode)) and val[0] == "!":
                val = val[1:]

            if key == 'oncotree_primary_diagnosis':
                if val not in normalize_table['values']['oncotree_primary_diagnosis'].values():
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


class ConsentValidatorCerberus(CerberusValidator):

    def _validate_consented(self, consented, field, value):

        # skip if not necessary
        if not consented:
            return

        # run the consent.
        if not check_consent(self.document):
            self._error(field, "Not consented")

def check_consent(clinical):

    # check conset.
    if 'CONSENT_17000' in clinical and clinical['CONSENT_17000'].upper() ==  'Y':
        return True
    else:
        if 'QUESTION1_YN' not in clinical:
            return False

        cnd1 = clinical['QUESTION1_YN'] == 'Y'
        cnd3 = clinical['QUESTION3_YN'] == 'Y'
        cndc = clinical['CRIS_YN'] == 'Y'

        if not cnd1 or not cnd3 or not cndc:
            return False

        return True


def check_valid_email_address(address):
    """
    Validates the provided email address.

    Arguments:
        address {str} -- Email address requiring validation.

    Returns:
        {bool} -- Either passes or fails validation.
    """
    valid_address_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    return re.match(valid_address_regex, address)

