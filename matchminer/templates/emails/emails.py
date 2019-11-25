import sys
import os
import json
import logging

from matchminer.settings import EMAIL_CONFIG

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', )

FILTER_MATCH_BODY = ""
EMAIL_BLAST_RESPONSE_BODY = ""
ACCOUNT_APPROVAL_BODY = ""
FILTER_ACTIVITY_BODY = ""
EAP_INQUIRY_BODY = ""

with open(EMAIL_CONFIG) as fin:
    vars_ = json.load(fin)
    for name, value in vars_.items():
        setattr(sys.modules[__name__], name, value)
