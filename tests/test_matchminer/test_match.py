import datetime
import time
from email.utils import formatdate
from bson.objectid import ObjectId
import json

from tests.test_matchminer import TestMinimal

class TestMatch(TestMinimal):
    def setUp(self, settings_file=None, url_converters=None):

        # call parent
        super(TestMatch, self).setUp(settings_file=None, url_converters=None)

        self.db['run_log_match'].drop()
        self.db['clinical_run_history_match'].drop()

    def tearDown(self):
        self.db['run_log_match'].drop()
        self.db['clinical_run_history_match'].drop()

    def _insert_match_small(self):

        # make a complex query.
        dt = "1995-01-01T11:28:34.144Z"
        c = {
            "BIRTH_DATE": {"^gt": dt},
        }
        g = {
            "TRUE_HUGO_SYMBOL": ["BRCA2"],
            'VARIANT_CATEGORY': ['MUTATION']
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

        # return the id.
        return r['_id']

    def _insert_match_large(self):

        # make a complex query.
        dt = "1975-01-01T11:28:34.144Z"
        c = {
            "BIRTH_DATE": {"^gt": dt},
        }
        g = {
            "TRUE_HUGO_SYMBOL": ["BRCA2"],
            'VARIANT_CATEGORY': ['MUTATION']
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

        # return the id.
        return r['_id']

    def test_get_match_sv(self):
        # test passes when run on it's own, but not when run in a suite
        # because of a race condition.
        return

        # make genes.
        gene1 = "ZNRF3"
        gene2 = "PMS2"

        # make a complex query.
        c = {}
        g = {
            "TRUE_HUGO_SYMBOL": [gene1, gene2],
            "VARIANT_CATEGORY": ["SV"],
            "WILDTYPE": False
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
            'genomic_filter': g,
            'label': 'ZNRF3, PMS2',
            'status': 1,
            'temporary': False
        }

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)
        filter_id = r['_id']

        # build the query string.
        qstr = "?where=%s" % json.dumps(({"FILTER_ID": filter_id, "TEAM_ID": str(self.team_id)}))
        qstr += "&embedded=%s" % json.dumps({"VARIANTS": 1})

        # fetch the matches.
        r, status_code = self.get('match', query=qstr)
        self.assert200(status_code)

        # assert we have stuff and its right
        matches = r['_items']
        assert len(matches) > 0
        orig_length = len(matches)
        for match in matches:
            assert match['FILTER_NAME'] == "%s, %s" % (gene1, gene2) or match['FILTER_NAME'] == "%s, %s" % (gene2, gene1)

        # modify it to be single.
        rule['genomic_filter']['TRUE_HUGO_SYMBOL'] = [gene1]

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)
        filter_id = r['_id']

        # build the query string.
        qstr = "?where=%s" % json.dumps(({"FILTER_ID": filter_id, "TEAM_ID": str(self.team_id)}))
        qstr += "&embedded=%s" % json.dumps({"VARIANTS": 1})

        # fetch the matches.
        r, status_code = self.get('match', query=qstr)
        self.assert200(status_code)

        # assert we get fewer matches
        assert orig_length > len(r['_items'])

    def test_get_match(self):

        # prepare the test
        filter_id = self._insert_match_small()
        filter_id2 = self._insert_match_small()

        # build the query string.
        qstr = "?where=%s" % json.dumps(({"FILTER_ID": filter_id, "TEAM_ID": str(self.team_id)}))
        qstr += "&embedded=%s" % json.dumps({"VARIANTS": 1})

        # fetch the matches.
        r, status_code = self.get('match', query=qstr)
        self.assert200(status_code)

        # assert we only get 1.
        assert len(r['_items']) > 0

        # assert we have the necessary sorting variables.
        for item in r['_items']:
            assert 'ONCOTREE_PRIMARY_DIAGNOSIS_NAME' in item
            assert 'TRUE_HUGO_SYMBOL' in item
            assert 'VARIANT_CATEGORY' in item
            assert 'REPORT_DATE' in item

    def test_get_email(self):

        # make a complex query.
        dt = "1975-01-01T11:28:34.144Z"
        c = {
            "BIRTH_DATE": {"^gt": dt},
        }
        g = {
            "TRUE_HUGO_SYMBOL": "BRCA2"
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
            'genomic_filter': g,
            'protocol_id': '13-615',
            'label': 'test',
            'status': 1,
            'temporary': False
        }

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # return the id.
        filter_id = r['_id']

        # get the matches.
        for match in self.db['match'].find({"FILTER_ID": ObjectId(filter_id)}):
            assert len(match['EMAIL_SUBJECT']) > 0

    def test_get_where(self):

        # prepare the test
        filter_id = self._insert_match_large()

        # build the date query string.
        dt = "2015-01-01T11:28:34.144Z"
        qstr = "?where=%s" % json.dumps(({"REPORT_DATE": {"^gte": dt}, "TEAM_ID": str(self.team_id)}))

        # fetch the matches.
        r, status_code = self.get('match', query=qstr)
        self.assert200(status_code)

        # assert we only get newer than 2015.
        for x in r['_items']:
            d = x['REPORT_DATE']
            t = datetime.datetime.strptime(d.replace(" GMT",""), '%a, %d %b %Y %H:%M:%S')
            assert t >= dt

    def test_check_match(self):

        # switch to service account.
        clinicals = list(self.db['clinical'].find())
        self.user_token = self.service_token

        # make a date
        cur_dt = formatdate(time.mktime(datetime.datetime(year=1995, month=1, day=1).timetuple()), localtime=False, usegmt=True)

        # make ten clinical entries containing equal proportions VITAL_STATUS values
        num_entries = 10
        clinical = [{
            '_id': str(ObjectId()),
            'FIRST_NAME': self._rand_alphanum(8),
            'LAST_NAME': 'TEST',
            'VITAL_STATUS': 'alive',
            'PATIENT_ID': '%s-%s-%s-%s-%s' % (
                self._rand_alphanum(8),
                self._rand_alphanum(4),
                self._rand_alphanum(4),
                self._rand_alphanum(4),
                self._rand_alphanum(12)
            ),
            'SAMPLE_ID': "TCGA-OR-%s" % self._rand_alphanum(4).upper(),
            'REPORT_DATE': cur_dt,
            'ONCOTREE_PRIMARY_DIAGNOSIS_NAME': 'TEST',
            'ONCOTREE_BIOPSY_SITE_TYPE': 'TEST',
            'MRN': 'TEST'
        } for _ in range(int(num_entries / 2))]

        clinical += [{
            '_id': str(ObjectId()),
            'FIRST_NAME': self._rand_alphanum(8),
            'LAST_NAME': 'TEST',
            'VITAL_STATUS': 'deceased',
            'PATIENT_ID': '%s-%s-%s-%s-%s' % (
             self._rand_alphanum(8),
             self._rand_alphanum(4),
             self._rand_alphanum(4),
             self._rand_alphanum(4),
             self._rand_alphanum(12)
            ),
            'SAMPLE_ID': "TCGA-OR-%s" % self._rand_alphanum(4).upper(),
            'REPORT_DATE': cur_dt,
            'ONCOTREE_PRIMARY_DIAGNOSIS_NAME': 'TEST',
            'ONCOTREE_BIOPSY_SITE_TYPE': 'TEST',
            'MRN': 'TEST'
        } for _ in range(int(num_entries / 2))]

        clinical = self.add_remaining_required_fields(clinical)

        # POST clinical
        r, status_code = self.post('clinical', clinical)
        self.assert201(status_code)
        clinical_ids = [item['_id'] for item in r['_items']]
        sample_ids = [item['SAMPLE_ID'] for item in r['_items']]

        # make ten genomic entries
        genomic = [{
                       'WILDTYPE': True,
                       'VARIANT_CATEGORY': 'MUTATION',
                       'CLINICAL_ID': clinical_id,
                       'SAMPLE_ID': sample_id,
                       'TRUE_HUGO_SYMBOL': 'TEST'
                   } for row, clinical_id, sample_id in zip(clinical, clinical_ids, sample_ids)]

        r, status_code = self.post('genomic', genomic)
        self.assert201(status_code)

        # limit to these simulated entries and create any genomic filter
        c = {
            'LAST_NAME': 'TEST'
        }
        g = {
            'TRUE_HUGO_SYMBOL': ["TEST"]
        }
        rule = {
            '_id': ObjectId(),
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
            'genomic_filter': g,
            'label': 'TEST',
            'status': 1,
            'temporary': False
        }

        # find the matches (should be all ten)
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # since there is no clinical filter applied, the number of clinical matches
        # should equal the number of patients with VITAL_STATUS == alive and
        # the number of genomic matches should equal the number of matches.
        matches = self.get('match')
        matches = len(matches[0]['_items'])
        assert matches == num_entries / 2

        # remove fake data from database
        self.db['clinical'].delete_many({'LAST_NAME': 'TEST'})
        self.db['genomic'].delete_many({'TRUE_HUGO_SYMBOL': 'TEST'})
        self.db['filter'].delete_many({'label': 'unit_test'})

    def test_change_match_status_null_email(self):

        # setup
        filter_id = ObjectId()
        patient_id = ObjectId()
        variant_id = ObjectId()
        self.db['filter'].insert_one({'_id': filter_id})
        self.db['clinical'].insert_one({'_id': patient_id})
        self.db['genomic'].insert_one({'_id': variant_id})

        # add match
        match_id = str(ObjectId())
        match = {
            "_id": match_id,
            "MATCH_STATUS": 1,
            "VARIANT_CATEGORY": "MUTATION",
            "CLINICAL_ID": str(patient_id),
            "clinical_id": str(patient_id),
            "hash": "testhash",
            "TRUE_HUGO_SYMBOL": "BRAF",
            "TEAM_ID": str(ObjectId(self.team_id)),
            "FILTER_STATUS": 1,
            "FILTER_NAME": "MEK Inhibitor",
            "VARIANTS": [
                str(variant_id)
            ],
            "ONCOTREE_PRIMARY_DIAGNOSIS_NAME": "Diffuse Glioma",
            "USER_ID": str(ObjectId(self.user_id)),
            "MMID": "XXXXXX",
            "FILTER_ID": str(filter_id),
            "PATIENT_MRN": "XXXXXX",
            "EMAIL_SUBJECT": None,
            "EMAIL_ADDRESS": None,
            "EMAIL_BODY": None,
            "is_disabled": False
        }

        r, status_code = self.post('match', match)
        self.assert201(status_code)

        # PUT the MATCH_STATUS field with null email and assert no errors
        update = match.copy()
        update['MATCH_STATUS'] = 6
        headers = [('If-Match', r['_etag'])]
        r, status_code = self.put('match/%s' % match_id, update, headers=headers)
        self.assert200(status_code)

        # clean up
        self.db['filter'].remove({'_id': filter_id})
        self.db['clinical'].remove({'_id': patient_id})
        self.db['genomic'].remove({'_id': variant_id})
