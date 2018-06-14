# import
from bson import ObjectId

from matchminer import miner
from matchminer import managment
from tests.test_matchminer import TestMinimal

class TestManagment(TestMinimal):

    def test_maintain_filters(self):

        # create matches.
        filter_id_1 = self._insert_filter()
        filter_id_2 = self._insert_filter()

        # clear the descriptions.
        filter_cnt = self.db['filter'].find().count()
        self.db['filter'].update_many({}, {"$set": {"description": ""}})

        # re-calculation description.
        managment.maintain_filters()

        # assert they are not empty.
        filters = list(self.db['filter'].find())
        assert len(filters) == filter_cnt
        for f in filters:
            assert len(f['description']) > 1


    def test_maintain_matches(self):

        # create matches.
        filter_id_1 = self._insert_filter()
        filter_id_2 = self._insert_filter()

        # mark them as new and delete PATIENT_MRN if exists
        self.db['match'].update_many({}, {"$set": {"MATCH_STATUS": 0}, "$unset": {"PATIENT_MRN": ""}})

        # assert we have 2 filters and 2 matches.
        user = self.db['user'].find_one({"_id": ObjectId(self.user_id)})
        match_db = self.db['match']
        filter_db = self.db['filter']
        num_filters, num_matches = miner._email_counts(ObjectId(self.team_id), match_db, filter_db)
        assert num_filters == 2
        assert num_matches == 4

        # manually delete filter.
        self.db['filter'].update_one({"_id": ObjectId(filter_id_1)}, {"$set": {"status": 2}})

        # this should delete the matches.
        managment.maintain_matches()

        # assert we only have 1 filter left.
        num_filters, num_matches = miner._email_counts(ObjectId(self.team_id), match_db, filter_db)
        assert num_filters == 1

        # assert all matches have patient_mrn.
        for match in self.db['match'].find():
            assert 'PATIENT_MRN' in match

        # manually delete all filters
        self.db['filter'].update_many({}, {"$set": {"status": 2}})

        # this should delete the matches.
        managment.maintain_matches()

        # assert we have 0 filters and matches.
        num_filters, num_matches = miner._email_counts(ObjectId(self.team_id), match_db, filter_db)
        assert num_filters == 0
        assert num_matches == 0


