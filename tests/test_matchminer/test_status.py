# import
import os
import pprint
import json
import time
import datetime
from email.utils import formatdate
from bson import ObjectId

from matchminer import miner, settings
from tests.test_matchminer import TestMinimal


class TestStatus(TestMinimal):

    def setUp(self, settings_file=None, url_converters=None):

        # call parent
        super(TestStatus, self).setUp(settings_file=None, url_converters=None)

        # switch to service account.
        self.tmp_token = self.user_token
        self.user_token = self.service_token

    def tearDown(self):
        self.db['run_log_match'].drop()
        self.db['clinical_run_history_match'].drop()

    # make an entry.
    now = '2017-01-01 05:00:00'
    cur_dt = formatdate(time.mktime(datetime.datetime(year=1995, month=1, day=1).timetuple()), localtime=False,
                        usegmt=True)
    clin = {
        "PCT_TARGET_BASE": 0.6764308658975878,
        "LAST_NAME": "Mcginnis[Fake]",
        "TUMOR_PURITY_PERCENT": 0.6273209625954723,
        "ONCOTREE_PRIMARY_DIAGNOSIS": "PHC",
        "ONCOTREE_BIOPSY_SITE": "ADRENAL_GLAND",
        "FIRST_NAME": "Michael",
        "PATIENT_ID": "b3164f7b-c826-4e08-9ee6-8ff96d29b913",
        "DATE_RECEIVED_AT_SEQ_CENTER": cur_dt,
        "SAMPLE_ID": "TCGA-OR-TEST1",
        "ONCOTREE_BIOPSY_SITE_TYPE": "Metastatic",
        "TOTAL_READS": 123,
        "ONCOTREE_PRIMARY_DIAGNOSIS_NAME": "Pheochromocytoma",
        "PANEL_VERSION": 2,
        "ONCOTREE_PRIMARY_DIAGNOSIS_META": "Pheochromocytoma",
        "TOTAL_ALIGNED_READS": 10716821,
        "POWERPATH_PATIENT_ID": "b3164f7b-c826-4e08-9ee6-8ff96d29b913",
        "TEST_TYPE": "11-104 Profile",
        "ORD_PHYSICIAN_NAME": "Maria Bellantoni [fake] M.D.",
        "ONCOTREE_BIOPSY_SITE_META": "Pheochromocytoma",
        "ONCOTREE_BIOPSY_SITE_COLOR": "Purple",
        "MEAN_SAMPLE_COVERAGE": 147,
        "VITAL_STATUS": "alive",
        "MRN": "b3164f7b-c826-4e08-9ee6-8ff96d29b913",
        "ONCOTREE_BIOPSY_SITE_NAME": "Adrenal Gland",
        "LAST_VISIT_DATE": cur_dt,
        "REPORT_COMMENT": "age_at_initial_pathologic_diagnosis 58 ct_scan nan ct_scan_findings nan days_to_initial_pathologic_diagnosis 0 excess_adrenal_hormone_diagnosis_method_type nan excess_adrenal_hormone_history_type mineralocorticoids excess_adrenal_hormone_history_type-2 nan max nan nf1 nan nf1_clinical_diagnosis nan ret nan sdha nan sdhaf2_sdh5 nan sdhb nan sdhc nan sdhd nan tmem127 nan vhl nan molecular_analysis_performed_indicator no histological_type adrenocortical carcinoma- usual type laterality left lymph_node_examined_count nan metastatic_neoplasm_confirmed_diagnosis_method_name nan metastatic_neoplasm_confirmed_diagnosis_method_name-2 nan metastatic_neoplasm_confirmed_diagnosis_method_text nan distant_metastasis_anatomic_site nan metastatic_neoplasm_initial_diagnosis_anatomic_site nan metastatic_neoplasm_initial_diagnosis_anatomic_site-2 nan metastatic_neoplasm_initial_diagnosis_anatomic_site-3 nan mitoses_count 5 number_of_lymphnodes_positive_by_he nan primary_lymph_node_presentation_assessment nan residual_tumor r0 tumor_tissue_site adrenal atypical_mitotic_figures atypical mitotic figures absent cytoplasm_presence_less_than_equal_25_percent cytoplasm presence <= 25% present diffuse_architecture diffuse architecture present invasion_of_tumor_capsule invasion of tumor capsule absent mitotic_rate mitotic rate > 5/50 hpf absent necrosis necrosis present nuclear_grade_iii_iv nuclear grade iii or iv absent sinusoid_invasion sinusoid invasion absent weiss_venous_invasion venous invasion absent weiss_score 3 year_of_initial_pathologic_diagnosis 2000",
        "ONCOTREE_PRIMARY_DIAGNOSIS_COLOR": "Purple",
        "ORD_PHYSICIAN_NPI": 7728,
        "DISEASE_CENTER_DESCR": "Adrenal Gland oncology",
        "REPORT_DATE": cur_dt,
        "BIRTH_DATE": cur_dt,
        "ALT_MRN": "b3164f7b-c826-4e08-9ee6-8ff96d29b913",
        "REPORT_VERSION": 1,
        "GENDER": "Male",
        "PATHOLOGIST_NAME": "Kacie Smith [fake] M.D.",
        'QUESTION1_YN': "Y",
        'QUESTION3_YN': "Y",
        'CRIS_YN': "Y",
    }

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
        "EMAIL_BODY": ""
    }

    status = {
        "_id": ObjectId(),
        "updated_genomic": 0,
        "new_genomic": 0,
        "silent": False,
        "new_clinical": 0,
        "updated_clinical": 0,
        "last_update": cur_dt,
        "data_push_id": now,
        'test_name': 'oncopanel'
    }

    def _new_status_random(self):

        # make a date.
        cur_dt = formatdate(time.mktime(datetime.datetime.now().timetuple()), localtime=False, usegmt=True)
        status = {
            'last_update': cur_dt,
            'new_clinical': 5,
            'updated_clinical': 6,
            'new_genomic': 7,
            'updated_genomic': 8
        }
        r, status_code = self.post('status', status)
        self.assert201(status_code)

    def _new_entry(self):

        # post clinical
        self.clin = self.add_remaining_required_fields([self.clin])
        r, status_code = self.post('clinical', self.clin)
        self.assert201(status_code)
        clinical = r
        clinical_id = r['_id']
        sample_id = r['SAMPLE_ID']

        # get some clinical id.
        result = self.db['clinical'].find_one({"SAMPLE_ID": "TCGA-OR-A5JO"})
        some_id = str(result['_id'])

        # fetch genomics we can add.
        genomics = self._get_genomic_records(ObjectId(some_id))
        for i in range(len(genomics)):

            # mark these.
            genomics[i]['COVERAGE'] = 9123
            genomics[i]['CLINICAL_ID'] = clinical_id
            genomics[i]['SAMPLE_ID'] = sample_id

            # clear this.
            for key in list(genomics[i].keys()):
                if key[0] == '_':
                    del genomics[i][key]

        # insert them.
        r, status_code = self.post('genomic', genomics[0:20])
        self.assert201(status_code)

        # return the entry.
        return clinical, r['_items']

    def test_deleted_genomic(self):

        # insert simulated person
        clinical, genomic = self._insert_pair()

        # add second genomic record
        for key in list(genomic.keys()):
            if key[0] == "_":
                del genomic[key]
        genomic["TRUE_PROTEIN_CHANGE"] = "p.TEST"
        genomic_2 = self._insert_genomic(clinical['_id'], data=genomic)
        genomic_2_id = ObjectId(genomic_2['_id'])

        # add a third record.
        genomic["TRUE_PROTEIN_CHANGE"] = "p.TEST2"
        genomic_3 = self._insert_genomic(clinical['_id'], data=genomic)
        genomic_3_id = ObjectId(genomic_3['_id'])

        # make a filter.
        g = {
            "TRUE_HUGO_SYMBOL": "SEMA6D",
            "WILDTYPE": False,
            "VARIANT_CATEGORY": ["MUTATION"]
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'genomic_filter': g,
            'label': 'test',
            'temporary': False,
            'status': 1
        }

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # get current matches.
        og_matches = list(self.db['match'].find())

        # delete the second and third genomic record.
        etag = genomic_2['_etag']
        for key in list(genomic_2.keys()):
            if key[0] == "_" and key != "_id":
                del genomic_2[key]
        r, status_code = self.delete('genomic/%s' % genomic_2['_id'], headers=[('If-Match', etag)])

        etag = genomic_3['_etag']
        for key in list(genomic_3.keys()):
            if key[0] == "_" and key != "_id":
                del genomic_3[key]
        r, status_code = self.delete('genomic/%s' % genomic_3['_id'], headers=[('If-Match', etag)])

        # run the re-matching.
        miner.rerun_filters()

        # get new matchets.
        matches = list(self.db['match'].find())

        # length of the two match lists should be equal because no clinical record was removed.
        assert len(matches) == len(og_matches)

        # ensure the deleted variant isn't there.
        for match in matches:
            for v in match['VARIANTS']:
                assert v != genomic_2_id
                assert v != genomic_3_id

            # check that the data_push_id is set correctly
            assert 'data_push_id' in match
            assert match['data_push_id'] is None, match['data_push_id']

    def test_deleted_genomic_new(self):

        # insert simulated person
        clinical, genomic = self._insert_pair()

        # add second genomic record
        for key in list(genomic.keys()):
            if key[0] == "_":
                del genomic[key]
        genomic["TRUE_PROTEIN_CHANGE"] = "p.TEST"
        genomic_2 = self._insert_genomic(clinical['_id'], data=genomic)
        genomic_2_id = ObjectId(genomic_2['_id'])

        # add a third record.
        genomic["TRUE_PROTEIN_CHANGE"] = "p.TEST2"
        genomic_3 = self._insert_genomic(clinical['_id'], data=genomic)
        genomic_3_id = ObjectId(genomic_3['_id'])

        # make a filter.
        g = {
            "TRUE_HUGO_SYMBOL": "SEMA6D",
            "WILDTYPE": False,
            "VARIANT_CATEGORY":  ["MUTATION"]
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'genomic_filter': g,
            'label': 'test',
            'temporary': False,
            'status': 1
        }

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # mark all these as new.
        self.db.match.update_many({}, {"$set": {"match_status": 0}})

        # get current matches.
        og_matches = list(self.db['match'].find())

        # delete the second and third genomic record.
        etag = genomic_2['_etag']
        for key in list(genomic_2.keys()):
            if key[0] == "_" and key != "_id":
                del genomic_2[key]
        r, status_code = self.delete('genomic/%s' % genomic_2['_id'], headers=[('If-Match', etag)])

        etag = genomic_3['_etag']
        for key in list(genomic_3.keys()):
            if key[0] == "_" and key != "_id":
                del genomic_3[key]
        r, status_code = self.delete('genomic/%s' % genomic_3['_id'], headers=[('If-Match', etag)])

        # run the re-matching.
        miner.rerun_filters()

        # get new matchets.
        matches = list(self.db['match'].find())

        # length of the two match lists should be equal because no clinical record was removed.
        assert len(matches) == len(og_matches)

        # ensure the deleted variant isn't there.
        for match in matches:
            for v in match['VARIANTS']:
                assert v != genomic_2_id
                assert v != genomic_3_id

            # make sure the match status is the same.
            assert match['match_status'] == 0

            # check that the data_push_id is set correctly
            assert 'data_push_id' in match
            assert match['data_push_id'] is None, match['data_push_id']

    def test_post_status_newclinical(self):
        self.db.run_log_match.drop()
        self.db.clinical_run_history_match.drop()

        # create a filter.
        g = {
            'TRUE_HUGO_SYMBOL': ['PRPF8'],
            'VARIANT_CATEGORY': ['MUTATION'],
            'WILDTYPE': False
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'genomic_filter': g,
            'label': 'test',
            'temporary': False,
            'status': 1,
            'protocol_id': '11-11111'
        }
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # UPDATE the matches status.
        results = self.db['match'].update_many({}, {'$set': {'MATCH_STATUS': 2}})

        # assert we have matches
        old_matches = list(self.db['match'].find())
        original_count = len(old_matches)
        assert original_count > 0

        # add new entry
        self._new_entry()

        # make a date.
        cur_dt = formatdate(time.mktime(datetime.datetime.now().timetuple()), localtime=False, usegmt=True)
        status = {
            'last_update': cur_dt,
            'new_clinical': 5,
            'updated_clinical': 6,
            'new_genomic': 7,
            'updated_genomic': 8,
            'silent': False,
            'data_push_id': self.now
        }
        r, status_code = self.post('rerun_filters', self.status)
        is_running = True
        time.sleep(3)
        while is_running:
            active_process = list(self.db.active_processes.find())
            if len(active_process) > 0:
                time.sleep(1)
            else:
                is_running = False
        self.assert200(status_code)

        # count again
        new_count = self.db['match'].count()
        assert new_count == original_count + 1
        assert new_count != original_count

        # get the new matches.
        new_matches = list(self.db['match'].find())

        # ensure the old matches maintain status.
        hits = 0
        old_id = set()
        for match in old_matches:
            old_id.add(match['_id'])
            for test in new_matches:
                if test['_id'] == match['_id']:
                    assert match['MATCH_STATUS'] == test['MATCH_STATUS']
                    hits += 1
                    break
        assert hits == original_count

        # assert the new matches are set to.
        hits = 0
        for match in new_matches:

            # skip the old ones.
            if match['_id'] in old_id:
                continue

            # ensure the new ones are marked accordinly.
            assert match['MATCH_STATUS'] == 0
            hits += 1

            # check that the data_push_id is set correctly
            assert 'data_push_id' in match
            assert match['data_push_id'] == self.now, '\nM: %s\nC: %s' % (
                match['data_push_id'], datetime.datetime(year=1995, month=1, day=1).strftime('%Y-%m-%d %H:%M:%S'))


    def test_post_status_vital(self):

        # force this patient to be alive.
        patient_id = ObjectId('56e1ddf88a68182c4d805e38')
        self.db.clinical.update_one({"_id": patient_id}, {"$set": {"VITAL_STATUS": "alive"}})

        # create a filter.
        g = {
            'TRUE_HUGO_SYMBOL': ['SUFU']
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'genomic_filter': g,
            'label': 'test',
            'temporary': False,
            'status': 1
        }
        r, status_code = self.post('filter', rule)
        filter_id = r['_id']
        self.assert201(status_code)

        # count matches
        matches = list(self.db['match'].find({'FILTER_ID': ObjectId(filter_id)}))
        match_cnt = len(matches)
        assert match_cnt == 61

        # assert our patient is in matches.
        found = False
        for m in matches:
            if ObjectId(m['CLINICAL_ID']) == patient_id:
                found = True
        assert found

        # cause the patient to become deceased.
        self.db.clinical.update_one({"_id": patient_id}, {"$set": {"VITAL_STATUS": "deceased", "_updated": datetime.datetime.now()}})

        # post a status update.
        cur_dt = formatdate(time.mktime(datetime.datetime.now().timetuple()), localtime=False, usegmt=True)
        status = {
            'last_update': cur_dt,
            'new_clinical': 5,
            'updated_clinical': 6,
            'new_genomic': 7,
            'updated_genomic': 8,
            'silent': False,
            'data_push_id': self.now
        }
        r, status_code = self.post('rerun_filters', self.status)
        is_running = True
        time.sleep(3)
        while is_running:
            active_process = list(self.db.active_processes.find())
            if len(active_process) > 0:
                time.sleep(1)
            else:
                is_running = False
        self.assert200(status_code)

        # reset the patient.
        self.db.clinical.update_one({"_id": patient_id}, {"$set": {"VITAL_STATUS": "alive"}})

        # we should see fewer matches.
        matches = list(self.db['match'].find({'FILTER_ID': ObjectId(filter_id), 'is_disabled': False}))
        match_cnt_new = len(matches)
        assert match_cnt_new > 0
        assert match_cnt_new < match_cnt

    def test_email(self):

        # generate text.
        num_matches = 5
        match_str = "matches"
        num_filters = 6

        match_str = "matches"
        if num_matches == 1:
            match_str = "match"

        cur_date = datetime.date.today().strftime("%B %d, %Y")
        cur_stamp = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")

        user = {
            'first_name': 'john',
            'last_name': 'doe'
        }

        # make the email
        html = miner._email_text(user, cur_stamp, {})

        # assert its equal.
        assert html.count("matches") > 0

    def test_new_matches(self):
        self.db.run_log_match.drop()
        self.db.clinical_run_history_match.drop()
        # POST filter
        c = {
            "ONCOTREE_PRIMARY_DIAGNOSIS_NAME": "Pheochromocytoma"
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
            'label': 'test',
            'temporary': False,
            'status': 1,
            'EMAIL': True,
            'test_name': 'oncopanel',
            'protocol_id': '11-1111'
        }
        filter_resp, status_code = self.post('filter', rule)
        filter_id = ObjectId(filter_resp['_id'])
        self.assert201(status_code)

        # assert that all matches associated with this filter are in the pending bin
        matches = list(self.db['match'].find({'FILTER_ID': filter_id}))
        assert matches
        assert len(matches) == 19
        for match in matches:
            assert match['MATCH_STATUS'] == 1

        assert len(list(self.db.run_log_match.find())) == 1

        # add clinical entry and status POST and check that the email count of new matches is correct
        # check that the new matches are in the new bin
        clin = self.clinical.copy()
        clin['VITAL_STATUS'] = 'alive'
        r, status_code = self.post('clinical', clin)
        self.assert201(status_code)
        self.db['genomic'].insert(self.genomic)

        time.sleep(1)
        self.db['filter'].update({'_id': filter_id}, {'$set': {'_updated': datetime.datetime.now()}})

        r, status_code = self.post('rerun_filters', self.status)
        is_running = True
        time.sleep(3)
        while is_running:
            active_process = list(self.db.active_processes.find())
            if len(active_process) > 0:
                time.sleep(1)
            else:
                is_running = False
        self.assert200(status_code)

        assert len(list(self.db.run_log_match.find())) == 2

        r, status_code = self.post('utility/send_emails', self.status)
        self.assert201(status_code)

        email = self.db['email'].find_one()
        assert len(list(self.db.clinical.find())) == 93
        assert email
        assert int(email['body'].split('identified ')[1].split(' new')[0]) == 1

        matches = list(self.db['match'].find({'FILTER_ID': filter_id}))
        assert matches
        for match in matches:
            if match['CLINICAL_ID'] == ObjectId(clin['_id']):
                assert match['MATCH_STATUS'] == 0
            else:
                assert match['MATCH_STATUS'] == 1

    def _check_matches(self):
        matches = list(self.db['match'].find())
        for match in matches:
            assert match['_new_match'] is True
