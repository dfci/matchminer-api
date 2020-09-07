import logging
import datetime

from matchminer.settings import EMAIL_AUTHOR_PROTECTED
from flask import current_app as app, abort


def immunoprofile_insert(items):
    doc = items[0]
    db = app.data.driver.db
    clinical_doc = db.clinical.find_one({"SAMPLE_ID": doc['sample_id']})

    if not clinical_doc:
        msg = f"No clinical document found for sample {doc['sample_id']}"
        abort(422, description=msg)

    if not clinical_doc['ORD_PHYSICIAN_EMAIL']:
        msg = f"Clinical document has no physician email {doc['sample_id']}"
        logging.error(msg)
        abort(422, description=msg)

    if 'clinical_id' not in doc:
        doc['clinical_id'] = clinical_doc['_id']

    body = f"""<html><head></head><body>
    Dear {clinical_doc['ORD_PHYSICIAN_NAME']}, <br/><br/>
    
    This email is to inform you that the ImmunoProfile test that you ordered for the following patient is now complete. 
    Your ability to view a specific patient’s result is based on that patient’s consent to share results with their 
    physician. <br/><br/>

    To access the results in MatchMiner, please click the link below (or copy and paste the website address in your 
    browser and hit enter) and use your Partners credentials to log in. Results can also be viewed by visiting 
    MatchMiner while viewing the patient below in Epic (instructions to access MatchMiner within Epic can be found in 
    the MatchMiner FAQ: <a href="https://matchminer.dfci.harvard.edu/#/faq">
    https://matchminer.dfci.harvard.edu/#/faq</a><br/><br/>
    
    Access link: <a href="https://matchminer.dfci.harvard.edu/#/dashboard/patients/{clinical_doc['_id']}">https://matchminer.dfci.harvard.edu/#/dashboard/patients/{clinical_doc['_id']}</a> <br/><br/>

    Patient name: {clinical_doc['FIRST_NAME']} {clinical_doc['LAST_NAME']} <br/>
    DFCI MRN: {clinical_doc['MRN']} <br/>
    Report Date: {clinical_doc['REPORT_DATE'].strftime('%B %d, %Y')} <br/><br/>

    Thank you, <br/>
    The ImmunoProfile Team <br/><br/>

    Note: If you do not have access to MatchMiner, please follow these instructions to apply for Oncologist access: 
    <a href="https://matchminer.dfci.harvard.edu/#/apply-for-access">https://matchminer.dfci.harvard.edu/#/apply-for-access</a> <br/><br/>

    <i>The information in this e-mail is intended only for the person to whom it is addressed. If you believe this 
    e-mail was sent to you in error and the e-mail contains patient information, please contact the Partners Compliance 
    HelpLine at http://www.partners.org/complianceline . If the e-mail was sent to you in error but does not contain 
    patient information, please forward to MatchMiner <matchminer@dfci.harvard.edu> and properly dispose of the e-mail.
    </i></body></html>
    """

    email = {
        'email_from': "immunoprofile@ds.dfci.harvard.edu",
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
