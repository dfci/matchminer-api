import os
import logging
import json
import datetime as dt

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', )

SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))


MM_SETTINGS = os.getenv('MM_SETTINGS', 'DEV')
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = os.getenv('MONGO_PORT', 27017)
MONGO_AUTH_SOURCE = os.getenv('MONGO_AUTH_SOURCE', 'admin')
MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'user')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'user')
MONGO_DBNAME = os.getenv('MONGO_DBNAME', 'matchminer')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/matchminer?replicaSet=rs0')
SERVER = os.getenv("SERVER", "")
OPLOG = os.getenv('OPLOG', True)
SSL_PORT = os.getenv('SSL_PORT', 5555)
ACS_URL = os.getenv('ACS_URL', '')
SLS_URL = os.getenv('SLS_URL', '')
SAML_SETTINGS = os.getenv('SAML_SETTINGS', 'settings_dev.json')
NO_AUTH = os.getenv('NO_AUTH', 'False')
WELCOME_EMAIL = os.getenv('WELCOME_EMAIL', 'YES')
API_PORT = os.getenv('API_PORT', 5000)
API_TOKEN = os.getenv('API_TOKEN', 'fb4d6830-d3aa-481b-bcd6-270d69790e11')
API_ADDRESS = os.getenv('API_ADDRESS', 'http://localhost:5555/api')
ONCORE_ADDRESS = os.getenv("ONCORE_ADDRESS", "")
EMAIL_CONFIG = os.getenv('EMAIL_CONFIG', os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                                      '../',
                                                                      'email.config.json')))
EMAIL_SERVER = os.getenv('EMAIL_SERVER', '')
EMAIL_USER = os.getenv('EMAIL_USER', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
EMAIL_AUTHOR = os.getenv('EMAIL_AUTHOR', '')
EMAIL_ACTIVE_PROTECTED = os.getenv('EMAIL_ACTIVE_PROTECTED', False)
EMAIL_SERVER_PROTECTED = os.getenv('EMAIL_SERVER_PROTECTED', '')
EMAIL_USER_PROTECTED = os.getenv('EMAIL_USER_PROTECTED', '')
EMAIL_PASSWORD_PROTECTED = os.getenv('EMAIL_PASSWORD_PROTECTED', '')
EMAIL_AUTHOR_PROTECTED = os.getenv('EMAIL_AUTHOR_PROTECTED', '')
EMAIL_TRIAL_CC_LIST = os.getenv('EMAIL_TRIAL_CC_LIST', '')
EMAIL_TRIAL_CONTACT = os.getenv('EMAIL_TRIAL_CONTACT', '')
EXCLUDE_FROM_STATISTICS = os.getenv('EXCLUDE_FROM_STATISTICS', [])
ONCORE_CURATION_AUTH_TOKEN = os.getenv("ONCORE_CURATION_AUTH_TOKEN", "")
FRONT_END_ADDRESS = os.getenv("ONCORE_CURATION_AUTH_TOKEN", "http://localhost:8001")
EPIC_DECRYPT_TOKEN = os.getenv("EPIC_DECRYPT_TOKEN", "")


TUMOR_TREE = os.path.abspath(os.path.join(os.path.dirname(__file__), './data/tumor_tree.txt'))

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
