from matchminer import database


def get_public_stats(resp):
    """Returns the number of clinical trials and the number of patients to the UI"""
    db = database.get_db()
    resp['_items'].append({
        'num_clinical_trials': len(list(db['trial'].distinct('protocol_no'))),
        'num_patients': len(list(db['clinical'].distinct("MRN")))
    })
