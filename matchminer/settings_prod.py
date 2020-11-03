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

# production data.
DATA_DIR = "/mm_staging"
DATA_CLINICAL_CSV = os.path.join(DATA_DIR, "clinical.pkl")
DATA_GENOMIC_CSV = os.path.join(DATA_DIR, "genomic.pkl")
DATA_ONCOTREE_FILE = os.getenv("ONCOTREE_CUSTOM_DIR", "/api/matchminer/data/oncotree_file.txt")

MONGO_QUERY_BLACKLIST = ['$where']
