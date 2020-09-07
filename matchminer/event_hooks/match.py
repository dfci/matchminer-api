from matchminer import database


def align_enrolled(resp):
    """
    Add enrollment information to match documents
    :param resp:
    :return:
    """

    # build list of clinical_ids
    clin_ids = set()
    for item in resp['_items']:
        if isinstance(item['CLINICAL_ID'], dict):
            clin_ids.add(item['CLINICAL_ID']['_id'])
        else:
            clin_ids.add(item['CLINICAL_ID'])

    # get only clincal id for matched subset.
    match_db = database.get_collection("match")
    matched_ids = set()
    for match in match_db.find({"MATCH_STATUS": 4, "CLINICAL_ID": {"$in": list(clin_ids)}}, {"CLINICAL_ID": 1}):
        matched_ids.add(match['CLINICAL_ID'])


def add_filter_run_id(item, original):
    """
    The Eve API does not allow keys to be prefixed with an underscore. It will return
    a 20X response, but not add to the DB.

    When rebinning matches in the UI, manually add back the _me_id field.
    :param item:
    :param original:
    :return:
    """
    if '_me_id' not in item:
        match = list(database.get_collection('match').find({'_id': item['_id']}, {'_me_id': 1}))
        if '_me_id' in match[0]:
            item['_me_id'] = match[0]['_me_id']
