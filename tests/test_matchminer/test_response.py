import time
import datetime
from email.utils import formatdate
from bson.objectid import ObjectId

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

    def _get_response_id(self, match_status):
        return str(self.db['response'].find_one({'match_status': match_status})['_id'])

    def _get(self, request):
        r = self.test_client.get('api/' + request, headers=[('Content-Type', 'application/json')])
        return self.parse_response(r)
