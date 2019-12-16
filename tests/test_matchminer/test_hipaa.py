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
        dt = formatdate(time.mktime(datetime.datetime(year=1995, month=1, day=1).timetuple()), localtime=False, usegmt=True)
        c = {
            "BIRTH_DATE": {"$gte": dt},
        }
        g = {
            "TRUE_HUGO_SYMBOL": "BRCA2"
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

    def test_get_match_embedded(self):

        # insert match.
        self._insert_match()

        # do the query with embedded call.
        qstr = "?embedded=%s" % json.dumps({"CLINICAL_ID": 1})

        # fetch the matches.
        r, status_code = self.get('match', query=qstr)
        self.assert200(status_code)

        # get all logs.
        hipaa_logs = list(self.db['hipaa'].find())

        # assert we get a log for each entry.
        assert len(r['_items']) > 0
        #assert len(r['_items']) == len(hipaa_logs)     # disabled because we hide the deceased matches


    def test_get_match(self):

        # insert match.
        self._insert_match()

        # ensure we can retrieve clinical
        r, status_code = self.get('match')
        self.assert200(status_code)

        # get all logs.
        hipaa_logs = list(self.db['hipaa'].find())

        # assert we get a log for each entry.
        assert len(r['_items']) > 0
        #assert len(r['_items']) == len(hipaa_logs)     # disabled because we hide the deceased matches


    def test_get_match_item(self):

        # insert match.
        self._insert_match()

        # ensure we can retrieve clinical
        match = self.db['match'].find_one()

        # ensure we can retrieve match
        r, status_code = self.get('match/%s' % (str(match['_id'])))
        self.assert200(status_code)

        # get all logs.
        hipaa_logs = list(self.db['hipaa'].find())

        # assert we get a log for each entry.
        assert 1 == len(hipaa_logs)
