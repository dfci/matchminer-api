import logging
import datetime

from matchminer.settings import EMAIL_AUTHOR_PROTECTED, EMAIL_IMMUNOPROFILE
from flask import current_app as app, abort


def immunoprofile_insert(items):
    doc = items[0]
    db = app.data.driver.db
    clinical_doc = db.clinical.find_one({"SAMPLE_ID": doc['sample_id']})

    if not clinical_doc:
        msg = f"No clinical document found for sample {doc['sample_id']}"
        abort(422, description=msg)

    if 'clinical_id' not in doc:
        doc['clinical_id'] = clinical_doc['_id']

    if doc['email'] and EMAIL_IMMUNOPROFILE:
        if not clinical_doc['ORD_PHYSICIAN_EMAIL']:
            msg = f"Clinical document has no physician email {doc['sample_id']}"
            logging.error(msg)
            abort(422, description=msg)

        body = f"""<html><head></head><body>
        **REMOVED**
        </i></body></html>
        """

        email = {
            'email_from': EMAIL_IMMUNOPROFILE,
            'email_to': clinical_doc['ORD_PHYSICIAN_EMAIL'],
            'subject': f"ImmunoProfile Results - Automated Alert",
            'body': body.replace('\n', ''),
            'cc': "",
            'sent': False,
            'num_failures': 0,
            'errors': []
        }
        db.email.insert(email)
    logging.info(f"Immunoprofile case {clinical_doc['SAMPLE_ID']} imported successfully.")
