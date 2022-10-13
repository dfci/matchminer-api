import os
import sys
import matchminer.data_model
from matchminer.components.gi.data_model import gi_gold_standard_truth

# for API documentation, needs to be enabled
ENFORCE_IF_MATCH = True
OPLOG = True

# collection names.
COLLECTION_CLINICAL = "clinical"
COLLECTION_GENOMIC = "genomic"

# TOKEN TIMEOUT.
TOKEN_TIMEOUT = sys.maxsize

# data outdir.
DATA_DIR = os.path.join(os.path.abspath(os.path.join(__file__ , "../..")), "data")
DATA_DIR_PROD = ""
DATA_CLINICAL_CSV = os.path.join(DATA_DIR, "tcga.clinical.pkl")
DATA_GENOMIC_CSV = os.path.join(DATA_DIR, "tcga.genomic.pkl")
DATA_ONCOTREE_FILE = os.getenv("ONCOTREE_CUSTOM_DIR", "/api/matchminer/data/oncotree_file.txt")

TREATMENT_LIST_AUTO_UPDATE_KEYS = ["arm_suspended", "level_suspended"]
TRIAL_SORT_DICT = {
    'oncology_group': 'group_name',
    'sponsor': 'sponsor_name',
    'protocol_staff': 'npi',
    'drug': 'drug_name',
    'site': 'site_name',
    'management_group': 'management_group_name',
    'program_area': 'program_area_name',
    'disease_site': 'disease_site_code',
    'step': 'step_internal_id',
    'arm': 'arm_internal_id',
    'dose_level': 'level_internal_id',
}

# enable larger returns.
PAGINATION_LIMIT = 100000
PAGINATION_DEFAULT = 100000

# start url with api.
URL_PREFIX = 'api'

# enable debug.
DEBUG = True

# disable XML
XML = False

# return full object after POST
BANDWIDTH_SAVER = False

# cors support.
X_DOMAINS = '*'
X_HEADERS = ['Authorization', 'If-Match', 'Content-Type', 'Pragma', 'Cache-Control', 'If-Modified-Since', 'Expires']

# disable caching.
CACHE_CONTROL = ''
CACHE_EXPIRES = 0

# Enable reads (GET), inserts (POST) and DELETE for resources/collections
# (if you omit this line, the API will default to ['GET'] and provide
# read-only access to the endpoint).
RESOURCE_METHODS = ['GET', 'POST']

# Enable reads (GET), edits (PATCH), replacements (PUT) and deletes of
# individual items  (defaults to read-only item access).
ITEM_METHODS = ['GET', 'PUT', 'DELETE']

## models
user = {
    "schema": matchminer.data_model.user_schema,
    'datasource': {
        'projection': {
            'token': 0,
        }
    },
    "allowed_read_roles": ["admin", "service", "user"],
    "allowed_write_roles": ["admin", "service"],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE']
}

team = {
    "schema": matchminer.data_model.team,
    "allowed_read_roles": ["admin", "service", "user"],
    "allowed_write_roles": ["admin", "service"],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE']
}

rule = {
    'schema': matchminer.data_model.filter_schema,
    'datasource': {
        'projection': {'filter_hash': 0}
    },
    "allowed_read_roles": ["admin", "service", "user"],
    "allowed_write_roles": ["admin", "service", "user"],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE']
}

clinical = {
    'schema': matchminer.data_model.clinical_schema,
    "allowed_read_roles": ["admin", "service", "user"],
    "allowed_write_roles": ["admin", "service"],
    'mongo_indexes': {'FIRST_LAST': [('FIRST_LAST', 1)]},
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE']
}

immunoprofile = {
    'schema': matchminer.data_model.immunoprofile_schema,
    "allowed_read_roles": ["admin", "service", "user"],
    "allowed_write_roles": ["admin", "service"],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE']
}

genomic = {
    'schema': matchminer.data_model.genomic_schema,
    "allowed_read_roles": ["admin", "service", "user"],
    "allowed_write_roles": ["admin", "service"],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE']
}

match = {
    'schema': matchminer.data_model.match_schema,
    "allowed_read_roles": ["admin", "service", "user"],
    "allowed_write_roles": ["admin", "service", "user"],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE']
}

hipaa_transaction = {
    'schema': matchminer.data_model.hipaa_transaction,
    "allowed_read_roles": ["admin"],
    "allowed_write_roles": ["admin"],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE']
}

status = {
    'schema': matchminer.data_model.status_schema,
    'datasource': {
        'default_sort': [('last_updated', -1)]
    },
    "allowed_read_roles": ["admin", "service", "user"],
    "allowed_write_roles": ["admin", "service"],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE']
}

import_log = {
    'schema': matchminer.data_model.import_log_schema,
    "allowed_read_roles": ["admin", "service", "user"],
    "allowed_write_roles": ["admin", "service"],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE']
}

user_log = {
    'schema': matchminer.data_model.user_log_schema,
    "allowed_read_roles": ["admin", "service", "user"],
    "allowed_write_roles": ["admin", "service"],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE']
}

trial = {
    'schema': matchminer.data_model.parent_schema,
    'allow_unknown': False,
    "allowed_read_roles": ["admin", "service", "user", "curator"],
    "allowed_write_roles": ["admin", "curator"],
    "public_item_methods": ['GET'],
    "public_methods": ['GET'],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE']
}
response = {
    'schema': matchminer.data_model.response_schema,
    'allow_unknown': False,
    "allowed_read_roles": ["admin", "service", "curator"],
    "allowed_write_roles": ["admin", "curator"],
    "public_item_methods": ['GET'],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE']
}

email = {
    'schema': matchminer.data_model.email_schema,
    'allow_unknown': False,
    "allowed_read_roles": ["admin", "service"],
    "allowed_write_roles": ["admin", "service"],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE']
}

statistics = {
    'schema': matchminer.data_model.dashboard_schema,
    'allow_unknown': False,
    "allowed_read_roles": ["admin", "service"],
    "allowed_write_roles": ["admin", "service"],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE']
}

public_stats = {
    'schema': matchminer.data_model.public_stats_schema,
    'allow_unknown': False,
    'allowed_read_roles': ["admin", "service", "curator", "user"],
    'allowed_write_roles': ["admin", "service"],
    'public_item_methods': ['GET'],
    'public_methods': ['GET'],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE']
}

trial_match = {
    'schema': matchminer.data_model.trial_match_schema,
    'allow_unknown': False,
    'allowed_read_roles': ["admin", "service", "oncologist", "cti"],
    'allowed_write_roles': ["admin", "service", "oncologist", "cti"],
    'item_methods': ['GET']
}

negative_genomic = {
    'schema': matchminer.data_model.negative_genomic_schema,
    'allow_unknown': False,
    "allowed_read_roles": ["admin", "service", "user"],
    "allowed_write_roles": ["admin", "service"],
    'item_methods': ['GET', 'PUT', 'DELETE']
}

patient_view = {
    'schema': matchminer.data_model.patient_view_schema,
    'allow_unknown': False,
    "allowed_read_roles": ["admin", "service", "user", "oncologist", "cti"],
    "allowed_write_roles": ["admin", "service", "user", "oncologist", "cti"],
    'item_methods': ['GET', 'PUT'],
}

enrollment = {
    'schema': matchminer.data_model.enrollment_schema,
    'allowed_read_roles': ["admin", "service", "user"],
    'allowed_write_roles': ["admin", "service", "user"],
    'item_methods': ['GET']
}

gi = {
    'schema': gi_gold_standard_truth,
    'allowed_read_roles': ["admin", "service", "user"],
    'allowed_write_roles': ["admin", "service", "user"],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE']
}

# schema
DOMAIN = {
    'user': user,
    'team': team,
    'clinical': clinical,
    'genomic': genomic,
    'immunoprofile': immunoprofile,
    'filter': rule,
    'match': match,
    'hipaa': hipaa_transaction,
    'status': status,
    'import_log': import_log,
    'user_log': user_log,
    'trial': trial,
    'response': response,
    'email': email,
    'statistics': statistics,
    'public_stats': public_stats,
    'trial_match': trial_match,
    'negative_genomic': negative_genomic,
    'patient_view': patient_view,
    'enrollment': enrollment,
    'gi': gi,
    'gi_gold_standard_truth': gi.copy()
}

MONGO_QUERY_BLACKLIST = ['$where']
