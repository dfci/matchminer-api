# import
import os
import yaml
import datetime
from matchminer.utilities import set_curated, set_updated
from matchminer.miner import prepare_criteria

from tests.test_matchminer import TestMinimal


class TestCustom(TestMinimal):

    i = 0

    def setUp(self, settings_file=None, url_converters=None):
        super(TestCustom, self).setUp(settings_file=None, url_converters=None)
        YAML_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../', 'data/yaml'))
        with open(os.path.join(YAML_DIR, "00-003.yml")) as fin:
            self.trial = yaml.load(fin)

        self.today = datetime.datetime.now().strftime('%B %d, %Y')

    def tearDown(self):
        self.db.trial.remove({'protocol_no': '00-003'})

    def test_match_count(self):

        # insert matches.
        filter_id = self._insert_match_small()

        # get the match-count.
        r, status_code = self.get('utility/count_match')
        self.assert200(status_code)

        # assert we have values.
        r = r[str(filter_id)]
        assert r['new'] == 0
        assert r['pending'] > 0
        assert r['flagged'] == 0
        assert r['not_eligible'] == 0
        assert r['enrolled'] == 0

    def test_unique(self):

        # get unique list from endpoint.
        r, status_code = self.get('utility/unique?resource=genomic&field=VARIANT_CATEGORY')
        self.assert200(status_code)

        # assert we have values.
        assert set(r['values']) == set(['MUTATION', 'CNV', 'SV'])

    def test_unique_oncotree(self):

        # get unique list from endpoint.
        r, status_code = self.get('utility/unique?resource=clinical&field=ONCOTREE_PRIMARY_DIAGNOSIS_NAME')
        self.assert200(status_code)

        # assert we have values.
        a = set(['Kidney', 'Dedifferentiated Chordoma', 'Acute Monocytic Leukemia', 'Melanoma', 'Lung'])
        tmp = list()
        for x in r['values']:
            tmp.append(x['text'])
        b = set(tmp)
        c = a.intersection(b)

        assert len(c) == len(a)


    def test_autocomplete(self):

        # gene completetion.
        r, status_code = self.get('utility/autocomplete?resource=genomic&field=TRUE_HUGO_SYMBOL&value=brca')
        self.assert200(status_code)
        assert set(r['values']) == set(['BRCA2', 'BRCA1'])

        # gene + integer.
        r, status_code = self.get('utility/autocomplete?resource=genomic&field=TRUE_TRANSCRIPT_EXON&value=8&gene=PIK3R1')
        self.assert200(status_code)
        assert set(r['values']) == set([8])

        # gene + empty integer.
        r, status_code = self.get('utility/autocomplete?resource=genomic&field=TRUE_TRANSCRIPT_EXON&value=&gene=PIK3R1')
        self.assert200(status_code)
        assert set(r['values']) == set([8])

        # gene + string.
        r, status_code = self.get('utility/autocomplete?resource=genomic&field=TRUE_PROTEIN_CHANGE&value=p&gene=APC')
        self.assert200(status_code)
        assert set(r['values']) == set(['p.K1462fs', 'p.R1435T', 'p.N125S', 'p.R2543K'])


        # gene + empty string.
        r, status_code = self.get('utility/autocomplete?resource=genomic&field=TRUE_PROTEIN_CHANGE&value=&gene=APC')
        self.assert200(status_code)
        tmp = {"$or": [
            {'TRUE_HUGO_SYMBOL': 'APC'},
            {'CNV_HUGO_SYMBOL': 'APC'},
        ]}
        x = set(self.db['genomic'].find(tmp).distinct("TRUE_PROTEIN_CHANGE"))
        x.remove(None)
        assert set(r['values']) == x

    def test_autocomplete_oncotree(self):

        # oncotree field.
        r, status_code = self.get('utility/autocomplete?resource=clinical&field=ONCOTREE_PRIMARY_DIAGNOSIS_NAME&value=Adrenal')
        self.assert200(status_code)
        assert set(r['values']) == set(['Adrenal Gland', 'Pheochromocytoma', 'Adrenocortical Adenoma', 'Adrenocortical Carcinoma'])

    def test_set_update(self):
        trial = set_updated(self.trial)
        assert 'last_updated' in trial, trial
        trial = self._check_trial_post(trial)

        # send again
        trial = set_updated(trial)
        assert 'last_updated' in trial, trial
        assert 'curated_on' in trial and trial['curated_on'] == '', trial
        for field in self.trial_status_fields:
            assert field in trial['_summary'], '%s\n\n %s' % (trial['_summary'], field)
        self._check_trial_post(trial)

        # curate
        trial = set_curated(trial)
        assert 'last_updated' in trial, trial
        assert 'curated_on' in trial and trial['curated_on'], trial
        for field in self.trial_status_fields:
            assert field in trial['_summary'], '%s\n\n%s' % (trial['_summary'], field)
        self._check_trial_post(trial)

    def test_set_curate(self):
        trial = set_curated(self.trial)
        assert 'curated_on' in trial, trial
        trial = self._check_trial_post(trial)

        # send again
        trial = set_curated(trial)
        assert 'curated_on' in trial, trial
        assert 'last_updated' in trial and trial['last_updated'] == self.today, trial
        for field in self.trial_status_fields:
            assert field in trial['_summary'], '%s\n\n%s' % (trial['_summary'], field)
        self._check_trial_post(trial)

        # update
        trial = set_updated(trial)
        assert 'curated_on' in trial, trial
        assert 'last_updated' in trial and trial['last_updated'], trial
        for field in self.trial_status_fields:
            assert field in trial['_summary'], '%s\n\n%s' % (trial['_summary'], field)
        self._check_trial_post(trial)

    def _check_trial_post(self, trial):
        self.user_token = self.curator_token
        trial = self._prep_trial(trial)
        r, status_code = self.post("trial", trial)
        assert status_code == 201
        dbtrial = self.db.trial.find_one({'protocol_no': '00-003'})
        assert dbtrial
        trial = dbtrial
        return trial

    def _prep_trial(self, trial):
        if 'curated_on' not in trial:
            trial['curated_on'] = ''
        if 'last_updated' not in trial:
            trial['last_updated'] = self.today
        newtrial = {'protocol_id': self.i}
        fields = ['last_updated', 'curated_on', 'data_table4', 'program_area_list', 'sponsor_list', 'site_list',
                  'principal_investigator', 'age', 'oncology_group_list', 'protocol_target_accrual', 'treatment_list',
                  'staff_list', 'short_title', 'protocol_no', 'phase', 'cancer_center_accrual_goal_upper',
                  'long_title', 'management_group_list', 'protocol_type', 'nct_id']
        for field in fields:
            newtrial[field] = trial[field]
        self.i += 1
        return newtrial

    def test_prepare_criteria(self):

        item = {
            'clinical_filter': {
                'BIRTH_DATE': {'^lte': "1999-05-16T17:09:46.737Z"},
                'ONCOTREE_PRIMARY_DIAGNOSIS_NAME': 'Breast'
            },
            'genomic_filter': {
                'WILDTYPE': False,
                'VARIANT_CATEGORY': {'^in': ['MUTATION']},
                'TRUE_HUGO_SYMBOL': {'^in': ['ERBB2']},
                'TRUE_PROTEIN_CHANGE': {'^in': ['p.G309A', 'p.G309E']}
            }
        }
        c, g, _ = prepare_criteria(item)
        assert g == {
            '$or': [
                {
                    'WILDTYPE': False,
                    'TRUE_PROTEIN_CHANGE': {'$in': ['p.G309A', 'p.G309E']},
                    'VARIANT_CATEGORY': 'MUTATION',
                    'TRUE_HUGO_SYMBOL': {'$in': ['ERBB2']}
                }
            ]
        }

        item['genomic_filter']['TRUE_PROTEIN_CHANGE'] = 'p.G309A'
        c, g, _ = prepare_criteria(item)
        assert g == {
            '$or': [
                {
                    'WILDTYPE': False,
                    'TRUE_PROTEIN_CHANGE': 'p.G309A',
                    'VARIANT_CATEGORY': 'MUTATION',
                    'TRUE_HUGO_SYMBOL': {'$in': ['ERBB2']}
                }
            ]
        }
