import os
import logging
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s', )

SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))

MM_SETTINGS = ""
MONGO_HOST = ""
MONGO_PORT = ""
MONGO_AUTH_SOURCE = ""
MONGO_USERNAME = ""
MONGO_PASSWORD = ""
MONGO_DBNAME = ""
MONGO_URI = ""
SERVER = ""
OPLOG = ""
ACS_URL = ""
SLS_URL = ""
SAML_SETTINGS = ""
NO_AUTH = ""
DISABLE_ONCORE_AUTH = False
WELCOME_EMAIL = ""
API_PORT = ""
API_TOKEN = ""
API_ADDRESS = ""
ONCORE_ADDRESS = ""
EMAIL_CONFIG = os.getenv('EMAIL_CONFIG', str(Path().resolve()) + '/email.config.json')
EMAIL_SERVER = ""
EMAIL_USER = ""
EMAIL_PASSWORD = ""
EMAIL_AUTHOR = ""
EMAIL_ACTIVE_PROTECTED = ""
EMAIL_SERVER_PROTECTED = ""
EMAIL_USER_PROTECTED = ""
EMAIL_PASSWORD_PROTECTED = ""
EMAIL_AUTHOR_PROTECTED = ""
EMAIL_IMMUNOPROFILE = ""
EMAIL_TRIAL_CC_LIST = ""
EMAIL_TRIAL_CONTACT = ""
EXCLUDE_FROM_STATISTICS = ""
ONCORE_CURATION_AUTH_TOKEN = ""
FRONT_END_ADDRESS = ""
EPIC_DECRYPT_TOKEN = ""
MATTERMOST_URL = ""
MATTERMOST_USER = ""
MATTERMOST_PW = ""
MATTERMOST_CHANNEL = ""
MATTERMOST_TEAM = ""
SAML_SECRET = ""
SWAGGER_INFO = {
    'title': 'Matchminer API',
    'version': '1.0',
    'description': 'Documentation of Matchminer\'s API',
    'contact': {
        'name': 'James Lindsay',
    },
    'license': {
        'name': 'MIT',
        'url': 'https://github.com/pyeve/eve-swagger/blob/master/LICENSE',
    },
    'schemes': ['http', 'https'],
}

# elasticsearch configs
ES_URL = ""
ES_INDEX = ""
ES_USER = ""
ES_PASSWORD = ""
ES_URI = ""
ES_MAPPING = os.path.abspath(os.path.join(os.path.dirname(__file__), '../elasticsearch/mapping.json'))
ES_SETTINGS = os.path.abspath(os.path.join(os.path.dirname(__file__), '../elasticsearch/settings.json'))


TUMOR_TREE = os.path.abspath(os.path.join(os.path.dirname(__file__), './data/tumor_tree.txt'))


# connect to secrets
file_path = os.getenv("SECRETS_JSON", None)

if file_path is None:
    logging.error("ENVAR SECRETS_JSON not set")

# pull values.
if file_path is not None:
    with open(file_path) as fin:
        vars_ = json.load(fin)
        for name, value in vars_.items():
            globals()[name] = value


if EMAIL_ACTIVE_PROTECTED == "True":
    EMAIL_ACTIVE_PROTECTED = True

# modify variables if necessary.
if NO_AUTH != "False":
    NO_AUTH = True
else:
    NO_AUTH = False

if MM_SETTINGS == "PROD":
    from matchminer.settings_prod import *
else:
    from matchminer.settings_dev import *

logging.warning("settings: %s" % MM_SETTINGS)
logging.warning("settings: %s" % MONGO_URI)

match_status_mapping = {
    'New': 0,
    'Pending': 1,
    'Flagged': 2,
    'Not Eligible': 3,
    'Enrolled': 4,
    'Contacted': 5,
    'Eligible': 6,
    'Deferred': 7,
    'Deceased': 3
}

