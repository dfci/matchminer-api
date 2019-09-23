# set values from development.
from matchminer.settings_dev import *

# start url with api.
URL_PREFIX = 'api'

# enable operations log.
OPLOG = True

# enable debug.
DEBUG = True

# TOKEN TIMEOUT.
TOKEN_TIMEOUT = 60

# SAML_FILE.
SAML_SETTINGS = 'settings_prod.json'

# production data.
DATA_DIR = "/mm_staging"
DATA_CLINICAL_CSV = os.path.join(DATA_DIR, "clinical.pkl")
DATA_GENOMIC_CSV = os.path.join(DATA_DIR, "genomic.pkl")
DATA_ONCOTREE_FILE = os.path.join(DATA_DIR, "oncotree_file.txt")

# backup directory.
BACKUP_HOURLY_DIR = os.path.join(BACKUP_DIR, "hourly")
BACKUP_HOURLY_FREQ = 3600
BACKUP_HOURLY_MAX = 24
BACKUP_DAILY_DIR = os.path.join(BACKUP_DIR, "daily")
BACKUP_DAILY_FREQ = 86400
BACKUP_DAILY_MAX = 7
BACKUP_WEEKLY_DIR = os.path.join(BACKUP_DIR, "weekly")
BACKUP_WEEKLY_FREQ = 604800
BACKUP_WEEKLY_MAX = 8
BACKUP_STATUS_DIR = os.path.join(BACKUP_DIR, "status")

MONGO_QUERY_BLACKLIST = ['$where']
