import datetime
from datetime import date

from matchminer import database, settings
from matchminer.settings import EXCLUDE_FROM_STATISTICS


def add_dashboard_row(status):
    """Updates the dashboard MatchMiner stats table"""

    # get records
    db = database.get_db()
    clinical = list(db['clinical'].find())
    users = list(db['user'].find())
    filters = list(db['filter'].find({'temporary': False, 'status': 1}))

    # allow for users without a "last_auth" entry
    for user in users:
        if 'last_auth' not in user:
            user['last_auth'] = None
        else:
            user['last_auth'] = user['last_auth'].replace(tzinfo=None)

    # calculate MatchMiner stats
    three_months_ago = datetime.datetime.today() - datetime.timedelta(days=90)
    num_samples = len(set(item['SAMPLE_ID'] for item in clinical if 'SAMPLE_ID' in item))
    num_patients = len(set(item['MRN'] for item in clinical if 'MRN' in item))
    active_users = list(item for item in users if item['last_auth'] and item['last_auth'] >= three_months_ago)
    inactive_users = list(item for item in users if not item['last_auth'] or item['last_auth'] < three_months_ago)

    # exclude ksg team members
    active_users = exclude_ksg(active_users)
    inactive_users = exclude_ksg(inactive_users)

    # sort users by activity
    active_users.sort(reverse=True, key=lambda x: x['_id'])
    inactive_users.sort(reverse=True, key=lambda x: x['_id'])

    # update the dashboard
    db['statistics'].update_one({}, {
        '$push': {
            'mm_data_set': [
                status['last_update'].strftime("%Y-%m-%d"),
                num_patients,
                num_samples,
                status['new_clinical'],
                len(active_users),
                len(filters)
            ]
        },
        '$set': {
            'active_filter_data_set': calculate_filter_stats(filters, db),
            'active_user_data_set': [
                [
                    get_user_name(user),
                    get_user_role(user),
                    _determine_login(user, True)
                ]
                for user in active_users
            ],
            'inactive_user_data_set': [
                [
                    get_user_name(user),
                    get_user_role(user),
                    _determine_login(user, True)
                ]
                for user in inactive_users
            ]
        }
    }, upsert=True)

    # convert old dates
    statistics = (db.statistics.find())
    for doc in statistics:
        mm_data_set = convert_old_dates(doc)
        db.statistics.update_one(
            {"_id": doc["_id"]},
            {"$set": {"mm_data_set": mm_data_set}}
        )


def calculate_filter_stats(filters, db):
    """Calculates stats for the dashboard active filter stats table"""

    filter_stats = []
    for filt in filters:
        filter_owner = db['user'].find_one({'_id': filt['USER_ID']})
        matches = list(db['match'].find({'FILTER_ID': filt['_id']}))

        # allow for missing fields
        if 'label' not in filt:
            filt['label'] = ''
        if 'description' not in filt:
            filt['description'] = ''
        if not filter_owner:
            filter_owner = {'first_name': '', 'last_name': ''}
        elif 'first_name' not in filter_owner:
            filter_owner['first_name'] = ''
        elif 'last_name' not in filter_owner:
            filter_owner['last_name'] = ''

        # limit filter description to 80 characters
        if len(filt['description']) > 80:
            filt['description'] = filt['description'][:80] + '...'

        # excluce KSG team members
        user_name = '%s %s' % (filter_owner['first_name'], filter_owner['last_name'])
        if user_name.replace(' ', '_') in settings.EXCLUDE_FROM_STATISTICS:
            continue

        filter_stats.append([
            _determine_activity_level(matches, db),
            user_name,
            _determine_login(filter_owner),
            filt['label'],
            filt['description'],
            len([match for match in matches if match['MATCH_STATUS'] == 0]),
            len([match for match in matches if match['MATCH_STATUS'] == 1]),
            len([match for match in matches if match['MATCH_STATUS'] == 2]),
            len([match for match in matches if match['MATCH_STATUS'] == 5]),
            len([match for match in matches if match['MATCH_STATUS'] == 6]),
            len([match for match in matches if match['MATCH_STATUS'] == 7]),
            len([match for match in matches if match['MATCH_STATUS'] == 3]),
            len([match for match in matches if match['MATCH_STATUS'] == 4])
        ])

    # sort by activity
    filter_stats.sort(key=lambda x: x[1], reverse=True)

    return filter_stats


def _allow_null_dt(dt, time_=False):
    """Handles an exception where the last_auth user field is null"""
    if dt:
        if time_:
            return dt.strftime("%Y-%m-%d %H:%M")
        else:
            return dt.strftime("%Y-%m-%d")
    else:
        return None


def _determine_activity_level(matches, db):
    """Handles instances where the "_updated" field is not set"""
    try:
        activity = db['match'].find_one({'_id': {'$in': [match['_id'] for match in matches]}}, sort=[("_updated", -1)])
        if activity:
            return _allow_null_dt(activity['_updated'])
        else:
            return None
    except KeyError:
        return None


def _determine_login(user, time_=False):
    """Handles instances where the "last_auth" field is not set"""
    try:
        return _allow_null_dt(user['last_auth'], time_)
    except KeyError:
        return None


def get_user_name(user):
    """
    Return the user's name

    :param user: User document
    :return: String of user's name
    """
    return '%s %s' % (user['first_name'], user['last_name'])


def get_user_role(user):
    """
    Return the user's roles, excluding role "user"

    :param user: User document
    :return: String of user's roles
    """
    return ", ".join(list(set(sorted(user['roles'])))).replace("user", "").replace("user,", "")[:-2]


def convert_old_dates(doc):
    """
    Converts old IsoDate formatted dates to string of format YYYY-MM-DD

    :param doc: Old datatable rows for MatchMiner Statistics table
    :return: Same table, but with the "Date of last CAMD Update" reformatted for all rows
    """

    new = []
    for row in doc["mm_data_set"]:
        camd_date = row[0]
        if isinstance(camd_date, date):
            camd_date = camd_date.strftime("%Y-%m-%d")
        new.append([camd_date] + row[1:])

    return new


def exclude_ksg(users):
    """
    Excludes KSG team members from the inclusion in the statistics page

    :param users: List of all users
    :return: List of all users minus KSG team members
    """
    non_ksg_users = []
    for user in users:
        user_name = '%s %s' % (user['first_name'], user['last_name'])
        if user_name.replace(' ', '_') not in EXCLUDE_FROM_STATISTICS:
            non_ksg_users.append(user)

    return non_ksg_users
