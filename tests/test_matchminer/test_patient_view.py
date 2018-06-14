import json
import time
import datetime as dt
from rfc822 import formatdate
from bson.objectid import ObjectId

from tests.test_matchminer import TestMinimal


class TestPatientView(TestMinimal):

    def setUp(self, settings_file=None, url_converters=None):

        # call parent
        super(TestPatientView, self).setUp(settings_file=None, url_converters=None)

        # switch to service account.
        self.user_token = self.service_token

        now = formatdate(time.mktime(dt.datetime.now().timetuple()))
        self.patient_view = {
            'mrn': 'FAKE-MRN',
            'protocol_no': '00-000',
            'user_id': ObjectId(),
            'user_first_name': 'FAKE',
            'user_last_name': 'FAKE',
            'user_email': 'fake@fake',
            'num_views_match_list': 0,
            'num_views_details_list': 1,
            'view_date': now
        }

        self.keep_this_user_id = ObjectId("599b040d100b7c4f8048fb07")

    def tearDown(self):
        self.db.patient_view.drop()

    def test_get_patient_view(self):
        self.db.patient_view.insert(self.patient_view)
        r, status_code = self.get('patient_view')
        self.assert200(status_code)

        resp = r['_items'][0]
        for field in ['mrn', 'protocol_no', 'user_first_name', 'user_last_name', 'view_date']:
            assert field in resp, '%s | %s' % (field, resp)

        self.db.patient_view.drop()

    def test_post_patient_view(self):

        user = self.db.user.find_one({'first_name': 'SERVICE'})
        self.db.user.remove({'_id': user['_id']})
        user['_id'] = self.keep_this_user_id
        self.db.user.insert(user)

        rule1 = {
            'protocol_no': '00-001',
            'mrn': 'FAKE',
            'from_details': True
        }
        rule2 = {
            'protocol_no': '00-002',
            'mrn': 'FAKE',
            'from_details': True
        }
        r, status_code = self.post('patient_view', [rule1, rule2])
        self.assert201(status_code)

        patient_view = list(self.db.patient_view.find())
        assert len(patient_view) == 2, patient_view
        for patient_view_item in patient_view:
            for field in ['mrn', 'protocol_no', 'user_id', 'user_first_name', 'user_last_name',
                          'user_email', 'num_views_match_list', 'num_views_details_list', 'view_date']:
                assert field in patient_view_item, '%s | %s' % (field, patient_view_item)
            assert patient_view_item['num_views_match_list'] == 0, patient_view_item
            assert patient_view_item['num_views_details_list'] == 1, patient_view_item
            assert 'from_details' not in patient_view_item

        # iterate from_details
        rule = {
            'protocol_no': '00-001',
            'mrn': 'FAKE',
            'from_details': True
        }
        r, status_code = self.post('patient_view', rule)
        self.assert201(status_code)

        patient_view = list(self.db.patient_view.find())
        assert len(patient_view) == 2, patient_view
        for patient_view_item in patient_view:
            for field in ['mrn', 'protocol_no', 'user_id', 'user_first_name', 'user_last_name',
                          'user_email', 'num_views_match_list', 'num_views_details_list', 'view_date']:
                assert field in patient_view_item, '%s | %s' % (field, patient_view_item)

            if patient_view_item['protocol_no'] == '00-001':
                assert patient_view_item['num_views_match_list'] == 0, patient_view_item
                assert patient_view_item['num_views_details_list'] == 2, patient_view_item
            if patient_view_item['protocol_no'] == '00-002':
                assert patient_view_item['num_views_match_list'] == 0, patient_view_item
                assert patient_view_item['num_views_details_list'] == 1, patient_view_item

        # iterate not from_details
        rule = {
            'protocol_no': '00-002',
            'mrn': 'FAKE',
            'from_details': False
        }
        r, status_code = self.post('patient_view', rule)
        self.assert201(status_code)

        patient_view = list(self.db.patient_view.find())
        assert len(patient_view) == 2, patient_view
        for patient_view_item in patient_view:
            for field in ['mrn', 'protocol_no', 'user_id', 'user_first_name', 'user_last_name',
                          'user_email', 'num_views_match_list', 'num_views_details_list', 'view_date']:
                assert field in patient_view_item, '%s | %s' % (field, patient_view_item)

            if patient_view_item['protocol_no'] == '00-001':
                assert patient_view_item['num_views_match_list'] == 0, patient_view_item
                assert patient_view_item['num_views_details_list'] == 2, patient_view_item
            if patient_view_item['protocol_no'] == '00-002':
                assert patient_view_item['num_views_match_list'] == 1, patient_view_item
                assert patient_view_item['num_views_details_list'] == 1, patient_view_item

        # check not from_details only
        self.db.patient_view.drop()
        rule = {
            'protocol_no': '00-002',
            'mrn': 'FAKE',
            'from_details': False
        }
        r, status_code = self.post('patient_view', rule)
        self.assert201(status_code)

        patient_view = list(self.db.patient_view.find())
        assert len(patient_view) == 1, patient_view
        for patient_view_item in patient_view:
            for field in ['mrn', 'protocol_no', 'user_id', 'user_first_name', 'user_last_name',
                          'user_email', 'num_views_match_list', 'num_views_details_list', 'view_date']:
                assert field in patient_view_item, '%s | %s' % (field, patient_view_item)

            assert patient_view_item['num_views_match_list'] == 1, patient_view_item
            assert patient_view_item['num_views_details_list'] == 0, patient_view_item

        # check CTI-mode filter matches
        self.db.patient_view.drop()
        rule = {
            'filter_match': True,
            'from_details': False,
            'mrn': '00-005',
            'filter_label': 'test',
            'filter_protocol_no': 'test123'
        }
        r, status_code = self.post('patient_view', rule)
        self.assert201(status_code)

        patient_view = list(self.db.patient_view.find())
        assert len(patient_view) == 1, patient_view
        assert patient_view[0]['requires_manual_review'] is True
        assert patient_view[0]['filter_label'] == 'test'
        assert patient_view[0]['filter_protocol_no'] == 'test123'
        assert 'filter_match' not in patient_view[0]
