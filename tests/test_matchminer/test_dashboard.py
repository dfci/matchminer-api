import random
from bson.objectid import ObjectId

from tests.test_matchminer import TestMinimal
from matchminer.events import add_dashboard_row


class TestDashboard(TestMinimal):

    def setUp(self, settings_file=None, url_converters=None):
        super(TestDashboard, self).setUp(settings_file=None, url_converters=None)
        self.user_token = self.service_token
        self.db['dashboard'].drop()

    def tearDown(self):
        self.db['dashboard'].drop()

    def test_update_dashboard(self):
        add_dashboard_row(self.status)

    def test_public_stats(self):

        # save clinical and trial entries from the start of the test
        all_clinical = list(self.db['clinical'].find())
        all_trials = list(self.db['trial'].find())

        # add trials and patients
        trials = []
        clinical = []
        for _ in range(10):
            clinical.append({'_id': ObjectId(), 'MRN': self._rand_alphanum(5)})
            trials.append({'_id': ObjectId(), 'protocol_no': random.randint(1000, 9999)})

        self._reinsert(clinical, trials)

        # GET public_stats
        self._get_public_stats(10)

        # Added complexity: duplicate MRNS and protocol nos
        trials = []
        clinical = []
        mrn = self._rand_alphanum(5)
        protocol = random.randint(1000, 9999)
        for _ in range(10):
            clinical.append({'_id': ObjectId(), 'MRN': mrn})
            trials.append({'_id': ObjectId(), 'protocol_no': protocol})

        # reinsert
        self._reinsert(clinical, trials)

        # GET
        self._get_public_stats(1)

        # Edge Case: no MRN in clinical, no protocol_no in trials
        del clinical[0]['MRN']
        del trials[0]['protocol_no']
        clinical[0]['placeholder'] = 'N/A'
        trials[0]['placeholder'] = 'N/A'
        clinical[1]['MRN'] = None
        trials[1]['protocol_no'] = None

        # reinsert
        resultc, resultt = self._reinsert(clinical, trials)

        # GET
        self._get_public_stats(2)

        # put original clinical and trial tables back
        self.db['clinical'].remove({'_id': {'$in': resultc.inserted_ids}})
        self.db['trial'].remove({'_id': {'$in': resultt.inserted_ids}})
        if all_clinical:
            self.db['clinical'].insert_many(all_clinical)
        if all_trials:
            self.db['trial'].insert_many(all_trials)

    def _get_public_stats(self, num):
        r, status_code = self.get('public_stats')
        assert r['_items'][0]['num_clinical_trials'] == num
        assert r['_items'][0]['num_patients'] == num
        self.assert200(status_code)

    def _reinsert(self, clinical, trials):
        self.db['clinical'].drop()
        self.db['trial'].drop()
        resultc = self.db['clinical'].insert_many(clinical)
        resultt = self.db['trial'].insert_many(trials)
        return resultc, resultt
