# import
import os
import yaml
import datetime
import binascii

from matchminer.event_hooks.trial import build_trial_elasticsearch_fields
from matchminer.utilities import set_curated, set_updated
from matchminer.custom import generate_encryption_key_epic, encrypt_epic, decrypt_epic

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


    def test_unique(self):

        # get unique list from endpoint.
        r, status_code = self.get('utility/unique?resource=genomic&field=VARIANT_CATEGORY')
        self.assert200(status_code)

        # assert we have values.
        assert set(r['values']) == {'MUTATION', 'CNV', 'SV'}

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

        # gene + integer.
        r, status_code = self.get(
            'utility/autocomplete?resource=genomic&field=TRUE_TRANSCRIPT_EXON&value=8&gene=PIK3R1')
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
            {'TRUE_HUGO_SYMBOL': 'APC'}
        ]}
        x = set(self.db['genomic'].find(tmp).distinct("TRUE_PROTEIN_CHANGE"))
        x.remove(None)
        assert set(r['values']) == x

    def test_set_update(self):
        trial = set_updated(self.trial)
        trial = self._prep_trial(trial)
        assert 'last_updated' in trial, trial
        build_trial_elasticsearch_fields([trial])

        # send again
        trial = set_updated(trial)
        build_trial_elasticsearch_fields([trial])
        assert 'last_updated' in trial, trial
        assert 'curated_on' in trial and trial['curated_on'] == '', trial
        for field in self.trial_status_fields:
            assert field in trial['_summary'], '%s\n\n %s' % (trial['_summary'], field)

        # curate
        trial = set_curated(trial)
        assert 'last_updated' in trial, trial
        assert 'curated_on' in trial and trial['curated_on'], trial
        for field in self.trial_status_fields:
            assert field in trial['_summary'], '%s\n\n%s' % (trial['_summary'], field)

    def test_set_curate(self):
        trial = set_curated(self.trial)
        assert 'curated_on' in trial, trial
        build_trial_elasticsearch_fields([trial])

        # send again
        trial = set_curated(trial)
        assert 'curated_on' in trial, trial
        assert 'last_updated' in trial and trial['last_updated'] == self.today, trial
        for field in self.trial_status_fields:
            assert field in trial['_summary'], '%s\n\n%s' % (trial['_summary'], field)
        build_trial_elasticsearch_fields([trial])

        # update
        trial = set_updated(trial)
        assert 'curated_on' in trial, trial
        assert 'last_updated' in trial and trial['last_updated'], trial
        for field in self.trial_status_fields:
            assert field in trial['_summary'], '%s\n\n%s' % (trial['_summary'], field)

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

    # Values taken from EPIC's encryption tool
    # See: https://open.epic.com/Tech/TechSpec?spec=Epic.EncryptionValidator.exe&specType=tools
    def test_generate_epic_key(self):
        shared_secret = 'PartnersTest'
        key = generate_encryption_key_epic(shared_secret).key
        assert binascii.hexlify(key).decode('utf-8').upper() == '73FB225DE1361CA4A1232244EC4EA55A'

    def test_encrypt_epic(self):
        key = generate_encryption_key_epic('PartnersTest')
        assert encrypt_epic(key,
                            'Field1|Field2|Field3|DSGGNCRASTKMSOXMR') == '18sQogCGwZUnIzVQvI7nNycKqth2t8RkiW3BPN14UJ/ZBkL4wEtuKq1ovZqotORO'

    def test_decrypt_epic(self):
        key = generate_encryption_key_epic('PartnersTest')
        assert decrypt_epic(key,
                            '18sQogCGwZUnIzVQvI7nNycKqth2t8RkiW3BPN14UJ/ZBkL4wEtuKq1ovZqotORO') == 'Field1|Field2|Field3|DSGGNCRASTKMSOXMR'
