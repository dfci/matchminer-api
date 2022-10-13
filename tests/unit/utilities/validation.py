import unittest
import os
import eve
import bson

from matchminer.settings import SETTINGS_DIR
from matchminer.security import TokenAuth
from matchminer.validation import ConsentValidatorEve
from matchminer.database import get_db

TEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../', 'data'))
SCAF_DIR = os.path.join(TEST_DIR, 'scaffolds')
BSON_FILE = os.path.join(SCAF_DIR, "normalize.bson")


class TrialValidation(unittest.TestCase):

    db = None

    def setUp(self):

        # prepare the app
        settings_file = os.path.join(SETTINGS_DIR, 'settings.py')
        self.app = eve.Eve(settings=settings_file,
                            url_converters = None,
                            auth = TokenAuth,
                            validator = ConsentValidatorEve)

        # load normalization.
        with open(BSON_FILE, 'rb') as fin:
            mappings = list(bson.decode_iter(fin.read()))

        # add normalization.
        self.db = get_db()
        for mapping in mappings:
            self.db['normalize'].drop()
            self.db['normalize'].insert(mapping)

        # create the validator.
        resource_def = self.app.config['DOMAIN']['trial']
        schema = resource_def['schema']

        #print self.app.config['SOURCES']
        with self.app.app_context():
            self.v = self.app.validator(schema=schema, resource='trial')

    def tearDown(self):
        self.db['normalize'].drop()
