# import
import os
import pprint
import json
from email.utils import formatdate
import time
import datetime

from tests.test_matchminer import TestMinimal

class TestHipaa(TestMinimal):

    def test_timeout(self):

        # fudge it.
        self.app.config['TOKEN_TIMEOUT'] = .02

        # ensure we can retrieve clinical
        r, status_code = self.get('clinical')
        self.assert200(status_code)

        # wait more time.
        time.sleep(2.5)

        # ensure we can't retrieve clinical
        r, status_code = self.get('clinical')
        assert status_code == 401


    def test_get_clinical(self):

        # ensure we can retrieve clinical
        r, status_code = self.get('clinical')
        self.assert200(status_code)

        # get all logs.
        hipaa_logs = list(self.db['hipaa'].find())

        # assert we get a log for each entry.
        assert len(r['_items']) == len(hipaa_logs)


    def test_get_clinical_item(self):

        # get an id.
        clinical = self.db['clinical'].find_one()

        # perform item query.
        r, status_code = self.get('clinical/%s' % str(clinical['_id']))
        self.assert200(status_code)

        # get all logs.
        hipaa_logs = list(self.db['hipaa'].find())

        # assert we get a log for each entry.
        assert 1 == len(hipaa_logs)

        # assert we get clinical id right.
        assert hipaa_logs[0]['patient_id'] == clinical['MRN']

    def _insert_match(self):

        # make a complex query.
        dt = "1900-02-03T11:28:34.144Z"
        c = {
            "BIRTH_DATE": {"^gt": dt},
        }
        g = {
            "TRUE_HUGO_SYMBOL": ["EGFR"]
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
            'genomic_filter': g,
            'label': 'test',
            'status': 1,
            'temporary': False
        }

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

    def test_get_match_item(self):

        # insert match.
        self._insert_match()

        # ensure we can retrieve clinical
        match = list(self.db['match'].find())[0]

        # ensure we can retrieve match
        r, status_code = self.get('match/%s' % (str(match['_id'])))
        self.assert200(status_code)

        # get all logs.
        hipaa_logs = list(self.db['hipaa'].find())

        # assert we get a log for each entry.
        assert 1 == len(hipaa_logs)
