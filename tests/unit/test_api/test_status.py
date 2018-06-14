_author__ = 'zachary'
import unittest
import os
from bson.objectid import ObjectId

from matchminer.database import get_db
from matchminer.custom import _count_matches, _count_matches_by_filter
from matchminer.events import replace_match
from matchminer.miner import email_matches

TEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../', 'data'))


class TestStatus(unittest.TestCase):

    match = {
        "_id": ObjectId(),
        "MATCH_STATUS": 0,
        "VARIANT_CATEGORY": "MUTATION",
        "CLINICAL_ID": ObjectId(),
        "TRUE_HUGO_SYMBOL": "BRAF",
        "TEAM_ID": ObjectId(),
        "FILTER_STATUS": 1,
        "FILTER_NAME": "MEK Inhibitor",
        "VARIANTS": [
            ObjectId()
        ],
        "ONCOTREE_PRIMARY_DIAGNOSIS_NAME": "Diffuse Glioma",
        "USER_ID": ObjectId(),
        "MMID": "D47CE1",
        "FILTER_ID": ObjectId(),
        "PATIENT_MRN": "XXXXXX",
        "EMAIL_SUBJECT": "",
        "EMAIL_ADDRESS": "test@test.test",
        "EMAIL_BODY": "",
    }

    status = {
        "_id": ObjectId(),
        "updated_genomic": 0,
        "new_genomic": 0,
        "silent": False,
        "new_clinical": 0,
        "updated_clinical": 0,
    }

    def setUp(self):

        self.db = get_db()
        self.db['status'].drop()
        self.db['match'].drop()
        self.db['match'].insert_one(self.match)

    def tearDown(self):
        self.db['match'].drop()

    def test_count_matches(self):

        user = {'_id': ObjectId(), 'teams': [self.match['TEAM_ID']]}

        # one new matches
        counts = _count_matches(list(self.db['match'].find({'_id': ObjectId(self.match['_id'])})), self.db['match'])
        assert counts['new_matches'] == 1
        assert self._new_match() is True

        # should be updated
        counts = _count_matches(list(self.db['match'].find({'_id': ObjectId(self.match['_id'])})), self.db['match'])
        assert counts['new_matches'] == 0
        assert self._new_match() is True

        # check ther other condition that will evaluate to a new match
        self.db['match'].update({'_id': self.match['_id']}, {'$set': {'_new_match': False}})

        counts = _count_matches(list(self.db['match'].find({'_id': ObjectId(self.match['_id'])})), self.db['match'])
        assert counts['new_matches'] == 1
        assert self._new_match() is True

        counts = _count_matches(list(self.db['match'].find({'_id': ObjectId(self.match['_id'])})), self.db['match'])
        assert counts['new_matches'] == 0
        assert self._new_match() is True

    def test_match_put_hook(self):

        # add a match to the pending bin
        match = self.db['match'].find_one()
        pending_match = match.copy()
        pending_match['_id'] = ObjectId()
        pending_match['MATCH_STATUS'] = 1
        self.db['match'].insert(pending_match)

        # call match PUT hook and make an update unrelated to the MATCH_STATUS
        update = pending_match.copy()
        update['EMAIL_ADDRESS'] = ''
        new_match = replace_match(update, pending_match)
        assert new_match['MATCH_STATUS'] == 1
        assert '_new_match' not in new_match

        # call match PUT hook and move the match to the new bin
        update['MATCH_STATUS'] = 0
        new_match = replace_match(update, pending_match)
        assert new_match['MATCH_STATUS'] == 0
        assert '_new_match' in new_match and new_match['_new_match']

    def test_email_matches(self):

        self.db['email'].drop()

        # add a team with two users
        team = {'_id': ObjectId(), 'first_name': 'Multiple_team_members_test'}
        users = [
            {'_id': ObjectId(), 'first_name': 'user1', 'last_name': 'user1', 'user_name': 'u1',
             'roles': ['user'], 'teams': [team['_id']], 'email': 'test@test.com'},
            {'_id': ObjectId(), 'first_name': 'user2', 'last_name': 'user2', 'user_name': 'u2',
             'roles': ['user'], 'teams': [team['_id']], 'email': 'test2@test.com'}
        ]
        self.db['team'].insert_one(team)
        self.db['user'].insert_many(users)

        # add five old matches into the new bin
        matches = []
        for _ in range(5):
            tmp_match = self.match.copy()
            del tmp_match['_id']
            tmp_match['TEAM_ID'] = team['_id']
            tmp_match['USER_ID'] = users[0]['_id']
            tmp_match['_new_match'] = True
            matches.append(tmp_match)
        self.db['match'].insert_many(matches)

        # add five new matches into the new bin
        matches = []
        for _ in range(5):
            tmp_match = self.match.copy()
            del tmp_match['_id']
            tmp_match['TEAM_ID'] = team['_id']
            tmp_match['USER_ID'] = users[0]['_id']
            matches.append(tmp_match)
        self.db['match'].insert_many(matches)

        # call the email count function
        email_matches()

        # check the database
        matches = list(self.db['match'].find({'TEAM_ID': team['_id']}))
        for match in matches:
            assert '_new_match' in match and match['_new_match']
            assert match['MATCH_STATUS'] == 0

        emails = list(self.db['email'].find())
        assert len(emails) == 2
        for email in emails:
            assert int(email['body'].split('identified ')[1].split(' new')[0]) == 5

    def test_count_matches_by_filter(self):

        # add two filters and matches in each bin for both filters
        team_id = ObjectId()
        filter1 = ObjectId()
        filter2 = ObjectId()
        self.db.filter.insert_many([
            {'_id': filter1, 'TEAM_ID': team_id, 'status': 1, 'temporary': False},
            {'_id': filter2, 'TEAM_ID': team_id, 'status': 1, 'temporary': False}
        ])
        matches = [{'MATCH_STATUS': i, 'FILTER_STATUS': 1, 'TEAM_ID': team_id, 'FILTER_ID': filter1}
                   for i in [0, 1, 2, 3, 4, 5, 6, 7]]
        matches += [{'MATCH_STATUS': i, 'FILTER_STATUS': 1, 'TEAM_ID': team_id, 'FILTER_ID': filter1}
                    for i in [0, 1, 2, 3, 4, 5, 6, 7]]
        matches += [{'MATCH_STATUS': i, 'FILTER_STATUS': 1, 'TEAM_ID': team_id, 'FILTER_ID': filter2}
                    for i in [0, 1, 2, 3, 4, 5, 6, 7]]
        self.db.match.insert_many(matches)

        # count number of matches in each bin for both filters
        counts = _count_matches_by_filter(
            list(self.db['match'].find({'TEAM_ID': team_id})),
            list(self.db['filter'].find({'TEAM_ID': team_id, 'status': 1, 'temporary': False}))
        )

        # check the number of matches for each filter
        assert sorted(counts.keys()) == sorted([str(filter1), str(filter2)]), '%s\n%s\b%s' % (
            counts.keys(), filter1, filter)
        assert counts[str(filter1)] == {
            "new": 2,
            "pending": 2,
            "flagged": 2,
            'not_eligible': 2,
            'enrolled': 2,
            'contacted': 2,
            'eligible': 2,
            'deferred': 2
        }, counts
        assert counts[str(filter2)] == {
            "new": 1,
            "pending": 1,
            "flagged": 1,
            'not_eligible': 1,
            'enrolled': 1,
            'contacted': 1,
            'eligible': 1,
            'deferred': 1
        }, counts

    def _new_match(self):
        return self.db['match'].find_one({'_id': self.match['_id']})['_new_match']
