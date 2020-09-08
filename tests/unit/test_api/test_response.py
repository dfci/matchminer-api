_author__ = 'priti'
import unittest
import os
import datetime
import time
from email.utils import formatdate
from bson.objectid import ObjectId
from matchminer.event_hooks.genomic import get_alterations
from matchminer.database import get_db

TEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../', 'data'))


class TestResponseValidation(unittest.TestCase):

    cur_dt = formatdate(time.mktime(datetime.datetime(year=2016, month=1, day=1).timetuple()), localtime=False, usegmt=True)
    exp_dt = formatdate(time.mktime(datetime.datetime(year=2020, month=1, day=1).timetuple()), localtime=False, usegmt=True)

    fake_patient = {
        '_id': ObjectId(),
        'SAMPLE_ID': 'sample_1',
        'MRN': 'patient_1',
        'ONCOTREE_PRIMARY_DIAGNOSIS': 'BRCA',
        'ORD_PHYSICIAN_NAME': 'MD. John Doe',
        'ORD_PHYSICIAN_EMAIL': 'john_doe@test.com [fake]',
        'FIRST_NAME': 'Fake P',
        'LAST_NAME': 'XYZ',
        'REPORT_DATE': cur_dt
    }

    fake_patient2 = fake_patient.copy()
    fake_patient2['_id'] = ObjectId()

    match_contacted = {
        '_id': ObjectId(),
        'TEAM_ID': 'test',
        'USER_ID': 'test',
        'MATCH_STATUS': 5,
        'FILTER_STATUS': 4,
        'CLINICAL_ID': fake_patient['_id'],
        'FILTER_NAME': 'ERBB2',
        'VARIANTS': []
    }

    match_flagged = {
        '_id': ObjectId(),
        'TEAM_ID': 'test',
        'USER_ID': 'test',
        'MATCH_STATUS': 1,
        'FILTER_STATUS': 4,
        'CLINICAL_ID': fake_patient2['_id'],
        'FILTER_NAME': 'ERBB2',
        'VARIANTS': [],
        'FILTER_ID': ObjectId("5783939e630db3002ac3125c"),
        'PATIENT_MRN': 'test_mrn'
    }

    resp_nostatus = {
        'match_id': match_contacted['_id'],
        'notification_id': ObjectId(),
        'time_clicked': cur_dt,
        'expiry_dt': exp_dt,
        'ip_address': '000.00.00.00',
        'allow_update': True,
        'return_url': ''
    }

    fake_filter = {
        '_id': match_flagged['FILTER_ID'],
        'USER_ID': resp_nostatus['notification_id'],
        'label': 'test_label'
    }

    fake_filter_owner = {
        '_id': fake_filter['USER_ID'],
        'first_name': 'Jane',
        'last_name': 'Doe',
        'email': 'janedoe@test.com'
    }

    response_ids = None
    email_ids = None

    def setUp(self):

        # set up fake db
        self.db = get_db()
        self.db['response'].drop()
        self.db['clinical'].insert_many([self.fake_patient, self.fake_patient2])
        self.db['match'].insert_many([self.match_contacted, self.match_flagged])
        self.db['filter'].insert_one(self.fake_filter)
        self.db['user'].insert_one(self.fake_filter_owner)

    def tearDown(self):
        self.db['match'].remove({'_id': {'$in': [self.match_contacted['_id'], self.match_flagged['_id']]}})
        self.db['clinical'].remove({'_id': {'$in': [self.fake_patient['_id'], self.fake_patient2['_id']]}})
        self.db['filter'].remove({'_id': self.fake_filter['_id']})
        self.db['user'].remove({'_id': self.fake_filter_owner['_id']})

        if self.response_ids:
            self.db['response'].remove({'_id': {'$in': self.response_ids}})

        if self.email_ids:
            self.db['email'].remove({'_id': {'$in': self.email_ids}})

    def test_get_alteration(self):

        variant = [{'TRUE_HUGO_SYMBOL': 'BRAF', 'TRUE_PROTEIN_CHANGE': 'p.V600E', 'VARIANT_CATEGORY': 'MUTATION'}]
        alteration = get_alterations(variant)
        assert alteration == 'BRAF V600E mutation'

        variant[0]['TRUE_PROTEIN_CHANGE'] = None
        alteration = get_alterations(variant)
        assert alteration == 'BRAF mutation'

        variant = [{'TRUE_HUGO_SYMBOL': 'BRAF', 'CNV_CALL': '', 'VARIANT_CATEGORY': 'CNV'}]
        alteration = get_alterations(variant)
        assert alteration == 'BRAF '

        variant[0]['VARIANT_CATEGORY'] = 'other'
        alteration = get_alterations(variant)
        assert alteration == 'structural re-arrangement'

    def __get_match(self):
        return self.db['match'].find_one({'_id': self.match_contacted['_id']})






