from matchminer import database


def add_filter_run_id(item, original):
    """
    The Eve API does not allow keys to be prefixed with an underscore. It will return
    a 20X response, but not add to the DB.

    When rebinning matches in the UI, manually add back the _me_id field.

    Remove _created field as eve automatically sets it to 1970 since it is not
    present.
    :param item:
    :param original:
    :return:
    """
    if '_me_id' not in item:
        match = list(database.get_collection('match').find({'_id': item['_id']}, {'_me_id': 1}))
        item.pop('_created')
        if '_me_id' in match[0]:
            item['_me_id'] = match[0]['_me_id']
