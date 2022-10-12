_author__ = 'zachary'
import unittest
import os
from bson.objectid import ObjectId

from matchminer.database import get_db
from matchminer.miner import _count_matches_by_filter, _count_matches

TEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../', 'data'))

from tests.test_matchminer import TestMinimal

class TestStatus(TestMinimal):

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
        super(TestStatus, self).setUp(settings_file=None, url_converters=None)
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
            list(counts.keys()), filter1, filter)
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
