import os
import logging
import json
import datetime as dt

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', )

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
WELCOME_EMAIL = ""
API_PORT = ""
API_TOKEN = ""
API_ADDRESS = ""
ONCORE_ADDRESS = ""
EMAIL_CONFIG = os.getenv('EMAIL_CONFIG', os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                                      '../',
                                                                      'email.config.json')))
EMAIL_SERVER = ""
EMAIL_USER = ""
EMAIL_PASSWORD = ""
EMAIL_AUTHOR = ""
EMAIL_ACTIVE_PROTECTED = ""
EMAIL_SERVER_PROTECTED = ""
EMAIL_USER_PROTECTED = ""
EMAIL_PASSWORD_PROTECTED = ""
EMAIL_AUTHOR_PROTECTED = ""
EMAIL_TRIAL_CC_LIST = ""
EMAIL_TRIAL_CONTACT = ""
EXCLUDE_FROM_STATISTICS = ""
ONCORE_CURATION_AUTH_TOKEN = ""
FRONT_END_ADDRESS = ""
EPIC_DECRYPT_TOKEN = ""


TUMOR_TREE = os.path.abspath(os.path.join(os.path.dirname(__file__), './data/tumor_tree.txt'))


# connect to secrets
file_path = os.getenv("SECRETS_JSON", None)

if file_path is None:
    logging.error("ENVAR SECRETS_JSON not set")

# pull values.
if file_path is not None:
    with open(file_path) as fin:
        vars_ = json.load(fin)
        for name, value in vars_.iteritems():
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

logging.warn("settings: %s" % MM_SETTINGS)
logging.warn("settings: %s" % MONGO_URI)

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
enrollment_date_filter = dt.datetime(year=2016, month=8, day=1)
