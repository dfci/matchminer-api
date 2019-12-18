import time
import datetime
from email.utils import formatdate
from bson.objectid import ObjectId

from matchminer import settings
from matchminer.utilities import parse_response
from matchminer.database import get_db
from tests.test_matchminer import TestMinimal
from tests.unit.test_api import demo_resps


class TestResponse(TestMinimal):
    cur_dt = formatdate(time.mktime(datetime.datetime(year=2016, month=1, day=1).timetuple()), localtime=False,
                        usegmt=True)

    fake_patient = {
        '_id': ObjectId(),
        'SAMPLE_ID': 'sample_1',
        'MRN': 'patient_1',
        'ONCOTREE_PRIMARY_DIAGNOSIS': 'BRCA',
        'ORD_PHYSICIAN_NAME': 'MD. John Doe',
        'ORD_PHYSICIAN_EMAIL': 'john_doe@fake.com',
        'FIRST_NAME': 'Fake P',
        'LAST_NAME': 'XYZ',
        'REPORT_DATE': cur_dt
    }

    match_flagged = {
        '_id': ObjectId("57e5680821dc022b0f90b483"),
        'TEAM_ID': 'test',
        'USER_ID': 'test',
        'MATCH_STATUS': 1,
        'FILTER_STATUS': 4,
        'CLINICAL_ID': fake_patient['_id'],
        'FILTER_NAME': 'ERBB2',
        'VARIANTS': [],
        'FILTER_ID': ObjectId("57e5680821dc022b0f90b484"),
        'PATIENT_MRN': 'test_mrn'
    }

    fake_filter = {
        '_id': match_flagged['FILTER_ID'],
        'USER_ID': ObjectId("57e5680821dc022b0f90b484"),
        'label': 'test_label'
    }

    fake_filter_owner = {
        '_id': fake_filter['USER_ID'],
        'first_name': 'Jane',
        'last_name': 'Doe',
        'email': 'janedoe@test.com',
        'token': 'abc123'
    }

    def setUp(self, settings_file=None, url_converters=None):
        super(TestResponse, self).setUp(settings_file=None, url_converters=None)
        self.user_token = None

        # add to database
        self.db = get_db()
        self.db.response.drop()
        self.db['clinical'].insert_one(self.fake_patient)
        self.db['match'].insert_one(self.match_flagged)
        self.db['filter'].insert_one(self.fake_filter)
        self.db['user'].insert_one(self.fake_filter_owner)
        self.db['response'].insert_many(demo_resps)
        self.response_ids = [resp['_id'] for resp in demo_resps]
        self.email_ids = [email['_id'] for email in list(self.db['email'].find())]

    def tearDown(self):
        self.db['clinical'].remove({'_id': self.fake_patient['_id']})
        self.db['match'].remove({'_id': self.match_flagged['_id']})
        self.db['filter'].remove({'_id': self.fake_filter['_id']})
        self.db['response'].drop()
        self.db['email'].remove({'_id': {'$in': self.email_ids}})
        self.db['user'].remove({'_id': self.fake_filter_owner['_id']})

    def test_url_parsing(self):
        # set the url
        url = "/api/response/57d2b05921dc021157786e4f?cacheBuster=1473684720168"

        # test for simple.
        is_resource, item_id = parse_response(url)
        assert is_resource

        # set the url differently.
        url = "/api/response/57d2b05921dc021157786e4f?cacheBuster=1473684720168&no_ml=true"
        is_resource, item_id = parse_response(url)
        assert not is_resource

    def _get_response_id(self, match_status):
        return str(self.db['response'].find_one({'match_status': match_status})['_id'])

    def test_get_response_eligible(self):
        r, status_code = self._get('response/%s' % self._get_response_id('Eligible'))
        self.assert200(status_code)
        self._check_response('Eligible')

    def test_get_response_not_eligible(self):
        r, status_code = self._get('response/%s' % self._get_response_id('Not Eligible'))
        self.assert200(status_code)
        self._check_response('Not Eligible')

    def test_get_response_deferred(self):
        r, status_code = self._get('response/%s' % self._get_response_id('Deferred'))
        self.assert200(status_code)
        self._check_response('Deferred')

    def _check_response(self, response_type):
        resp = self.db['response'].find_one({'_id': ObjectId(self._get_response_id(response_type))})
        assert 'ip_address' in resp
        assert 'time_clicked' in resp

        match = self.db['match'].find_one({'_id': self.match_flagged['_id']})
        assert match['MATCH_STATUS'] == settings.match_status_mapping[response_type]

    def _get(self, request):
        r = self.test_client.get('api/' + request, headers=[('Content-Type', 'application/json')])
        return self.parse_response(r)
