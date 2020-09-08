import unittest
import json
import os
import yaml
import datetime as dt

from matchminer.event_hooks.event_utils import entry_insert
from matchminer.event_hooks.trial import insert_data_clinical, trial_insert, insert_data_genomic
from matchminer.database import get_db
from matchminer.matchengine_v1.engine import MatchEngine
from matchminer.utilities import set_curated, reannotate_trials, set_updated
from matchminer.trial_search import Summary, ParseMatchTree, Autocomplete

from tests.data import yaml_schema
from tests.unit.utilities.validation import TrialValidation
from tests.data.mock.trial import on_trial
from tests.unit.test_api import trial, trial2, match_tree_example, match_tree_example2, match_tree_example3

TEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../', 'data'))
YAML_DIR = os.path.join(TEST_DIR, 'yaml')

MAPPING = {
    "key": "trial",
    "values": {
        "oncotree_primary_diagnosis": {
            "cns/brain": "CNS/Brain",
            "colorectal adenocarcinoma": "Colorectal Adenocarcinoma",
            "myelodysplasia": "Myelodysplasia",
            "_SOLID_": "_SOLID_",
            "_LIQUID_": "_LIQUID_",
            "Glioblastoma": "Glioblastoma",
            "Gliosarcoma": "Gliosarcoma",
            "Anaplastic Astrocytoma": "Anaplastic Astrocytoma",
            "invasive breast carcinoma": "Invasive Breast Carcinoma",
            "non-hodgkin lymphoma": "Non-Hodgkin Lymphoma",
            "acute myeloid leukemia": "Acute Myeloid Leukemia",
            "lung adenocarcinoma": "Lung Adenocarcinoma",
            "lung adenosquamous carcinoma": "Lung Adenosquamous Carcinoma",
            "diffuse large b-cell lymphoma": "!Diffuse Large B-Cell Lymphoma",
            "pancreatic adenocarcinoma": "Pancreatic Adenocarcinoma",
            "Non-Small Cell Lung Cancer": "Non-Small Cell Lung Cancer",
            'breast': 'Breast'
        },
        "site_status": {
            "NEW": "New",
            "ON HOLD": "On Hold",
            "SRC APPROVAL": "SRC Approval",
            "IRB INITIAL APPROVAL": "IRB Initial Approal",
            "ACTIVATION COORDINATOR SIGNOFF": "Activation Coordinator Signoff",
            "OPEN TO ACCRUAL": "Open to Accrual",
            "CLOSED TO ACCRUAL": "Closed to Accrual",
            "SUSPENDED": "Suspended",
            "IRB STUDY CLOSURE": "IRB Study Closure",
            "TERMINATED": "Terminated"
        },
        "status": {
            "NEW": "New",
            "ON HOLD": "On Hold",
            "SRC APPROVAL": "SRC Approval",
            "IRB INITIAL APPROVAL": "IRB Initial Approval",
            "ACTIVATION COORDINATOR SIGNOFF": "Activation Coordinator Signoff",
            "OPEN TO ACCRUAL": "Open to Accrual",
            "CLOSED TO ACCRUAL": "Closed to Accrual",
            "SUSPENDED": "Suspended",
            "IRB STUDY CLOSURE": "IRB Study Closure",
            "TERMINATED": "Terminated"
        }
    }
}

def _handle_exc(trial):
    """Field name "diseasesite_code" can come in from the yaml as string or integer but must be stored as a string"""

    for k, v in trial.items():
        if k == 'disease_site_code':
            trial[k] = str(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    item = _handle_exc(item)
        elif isinstance(v, dict):
            trial[k] = _handle_exc(v)

    return trial

class TestTrialValidation(TrialValidation):

    def setUp(self):

        # call validation setup
        super(TestTrialValidation, self).setUp()

        # create the validator.
        resource_def = self.app.config['DOMAIN']['trial']
        schema = resource_def['schema']

        with self.app.app_context():
            self.v = self.app.validator(schema=schema, resource='trial')

    def tearDown(self):

        # call validation setup
        super(TestTrialValidation, self).tearDown()

    def test_trial_schema(self):

        # loop over each trial.
        for trial_name in os.listdir(YAML_DIR):

            # skip purposly bad one.
            if trial_name == "bad.yml":
                continue

            # load yaml.
            trial_path = os.path.join(YAML_DIR, trial_name)
            with open(trial_path, "rb") as fin:
                data_json = yaml.load(fin.read())

            # fix string issue.
            data_json = _handle_exc(data_json)

            with self.app.app_context():
                self.v.validate(data_json)
                assert len(self.v.errors) == 0, self.v.errors

    def test_trial_insert(self):

        # loop over each trial.
        executed_new_yaml = False
        for trial_name in os.listdir(YAML_DIR):

            # open the trial as json
            trial_path = os.path.join(YAML_DIR, trial_name)
            with open(trial_path, "rb") as fin:

                # load yaml
                data_json = yaml.load(fin.read())

                # normalize.
                entry_insert('trial', [data_json])

                # insert it.
                trial_insert([data_json])

                # check these fields are present.
                assert '_summary' in data_json

            # trial 15-153 contains hormone receptor status and wildtype hugo symbol fields
            if trial_name == '00-002.yml':
                assert 'PIK3CA' in data_json['_summary']["genes"]
                assert 'wt PIK3CA' in data_json['_summary']["genes"]
                assert 'Invasive Breast Carcinoma ER+/HER2-' in data_json['_summary']['tumor_types']
                assert len(data_json['_summary']['tumor_types']) == 1
                assert set(data_json['_summary']['disease_status']) == {'Metastatic', 'Advanced'}
                executed_new_yaml = True

            if trial_name == '00-001.yml':
                for diag in data_json['_summary']['tumor_types']:
                    assert diag[0] != '!'

        assert executed_new_yaml, 'Please add trial 00-002 to the tests/data/yaml directory so that' \
                                  'hormone receptor status and wildtype hugo symbol functionality can be' \
                                  'adequately tested.'

    def test_insert_data_clinical(self):
        result = {}
        data = {'age_numerical': '>=18', 'oncotree_primary_diagnosis': '!Ocular Melanoma'}
        insert_data_clinical(result, data, '123')
        assert 'oncotree_primary_diagnosis' in result

    def test_insert_data_genomic(self):

        # make simulated genomic clause
        result = {}
        data = dict(
            hugo_symbol="EGFR",
            variant_category="Mutation",
            wildtype=True
        )

        # insert and verify wildtype structure
        insert_data_genomic(result, data, '123')
        assert set(result.keys()) == {'wildtype_hugo_symbol', 'variant_category'}
        assert result['wildtype_hugo_symbol'] == [{"id": ["123"], "value": "wt EGFR"}]

        # repeat with non wildtype
        result = {}
        del data['wildtype']
        insert_data_genomic(result, data, '123')
        assert set(result.keys()) == {'hugo_symbol', 'variant_category'}

        # try with copy number (currently no explicit facet is built just make sure hugo_symbol is present)
        result = {}
        data = dict(
            hugo_symbol="MET",
            cnv_call="High Amplification",
            variant_category="Copy Number Variation"
        )
        insert_data_genomic(result, data, '123')
        assert set(result.keys()) == {'hugo_symbol', 'variant_category', 'cnv_call'}

        # try with SV (currently no explicit facet is built just make sure hugo_symbol is present)
        result = {}
        data = dict(
            hugo_symbol="ALK",
            variant_category="Structural Variation"
        )
        insert_data_genomic(result, data, '123')
        assert set(result.keys()) == {'hugo_symbol', 'variant_category'}

        # MMR/MS status
        result = {}
        data = dict(
            mmr_status="MMR-Proficient"
        )
        insert_data_genomic(result, data, '123')
        assert set(result.keys()) == {'mmr_status'}


class TestTrialFields(unittest.TestCase):

    def  mapping_oncotree(self):

        # insert the mapping
        db = get_db()
        mapping = {
            "key": "trial",
            "values": {
                "oncotree_primary_diagnosis": {"cns/brain": "CNS/Brain"}
            }
        }
        db['normalize'].insert(mapping)

        # set data example
        data = {'match': [{'or': [{'or': [{'clinical': {'oncotree_primary_diagnosis': 'Breast', 'age_numerical': '>=18'}}, {
            'clinical': {'oncotree_primary_diagnosis': 'Renal Cell Carcinoma', 'age_numerical': '>=18'}}, {
                                    'clinical': {'oncotree_primary_diagnosis': 'Pleural Mesothelioma',
                                                 'age_numerical': '>=18'}}, {
                                    'clinical': {'oncotree_primary_diagnosis': 'Peritoneal Mesotheliom',
                                                 'age_numerical': '>=18'}}, {
                                    'clinical': {'oncotree_primary_diagnosis': 'Gastrointestinal Stromal Tumor',
                                                 'age_numerical': '>=18'}}]}, {'and': [{'or': [
            {'genomic': {'wildcard_protein_change': 'p.G12', 'hugo_symbol': 'KRAS'}},
            {'genomic': {'wildcard_protein_change': 'p.G13', 'hugo_symbol': 'KRAS'}},
            {'genomic': {'wildcard_protein_change': 'p.Q61', 'hugo_symbol': 'KRAS'}}]}, {'clinical': {
            'oncotree_primary_diagnosis': 'Lung Adenocarcinoma', 'age_numerical': '>=18'}}]}, {'and': [{'or': [
            {'genomic': {'variant_category': 'Mutation', 'hugo_symbol': 'IDH1'}},
            {'genomic': {'variant_category': 'Mutation', 'hugo_symbol': 'IDH2'}}]}, {'and': [
            {'clinical': {'oncotree_primary_diagnosis': '_SOLID_', 'age_numerical': '>=18'}},
            {'clinical': {'oncotree_primary_diagnosis': '!CNS/Brain', 'age_numerical': '>=18'}}]}]}, {
                            'and': [{'genomic': {'hugo_symbol': 'MYC', 'cnv_call': 'High Amplification'}}, {
                                'clinical': {'oncotree_primary_diagnosis': '_SOLID_', 'age_numerical': '>=18'}}]}]}]}

        # do the mapping.
        entry_insert("trial", [data])

        # assert it is updated.
        assert data['match'][0]['or'][2]['and'][1]['and'][1]['clinical']['oncotree_primary_diagnosis'] == '!CNS/Brain'

    def test_trial_normalization(self):

        db = get_db()
        db['normalize'].insert(MAPPING)

        # define test json
        with open(os.path.join(YAML_DIR, "00-001.yml")) as fin:
            test_json = yaml.load(fin)

        # do the mapping.
        entry_insert("trial", [test_json])

        trial_insert([test_json])

        db['normalize'].drop()


class TestTrialUtilities(unittest.TestCase):

    db = None

    def setUp(self):

        # set pointer to db.
        self.db = get_db()
        self.tearDown()

    def tearDown(self):

        # flush database (only trials for now)
        self.db['trial'].drop()

    def test_trial_reinsert(self):

        # remove extra fields.
        fields = ['_summary']
        trial = yaml_schema.yaml_test_json.copy()
        for key in fields:
            if key in trial:
                del trial[key]

        # insert it.
        self.db['trial'].insert(trial)

        # check we don't have fields.
        for trial in self.db['trial'].find():
            for x in fields:
                assert x not in trial

        # re-annotate it.
        reannotate_trials()

        # assert we have the fields in the output.
        for trial in self.db['trial'].find():
            for x in fields:
                assert x in trial

    def test_trial_summary(self):

        on_trial['_genomic'] = {'hugo_symbol': [{'value': 'TEST'}]}
        on_trial['_clinical'] = {'disease_status': [{'value': ['TEST']}]}
        other = {'management_group': [{'value': 'TEST'}]}

        # create trial tree
        db = get_db()
        me = MatchEngine(db)
        status, trial_tree = me.create_trial_tree(on_trial, no_validate=True)

        # validate summary
        summary = Summary(on_trial['_clinical'],
                          on_trial['_genomic'],
                          other,
                          trial_tree)
        item = summary.create_summary(on_trial)
        status_fields = ['drugs', 'genes', 'tumor_types', 'sponsor',
                         'phase_summary', 'accrual_goal', 'investigator', 'age_summary', 'protocol_number',
                         'disease_status', 'nct_number', 'disease_center', 'short_title',
                         'hormone_receptor_status']

        for field in status_fields:
            assert field in item, self._debug(item, field)

            if field not in ['dfci_investigator', 'hormone_receptor_status']:
                assert item[field], '%s| %s' % (field, item)

        # remove all fields and validate that the summary will not error
        del on_trial['age']
        del on_trial['phase']
        del on_trial['nct_id']
        del on_trial['protocol_no']
        del on_trial['principal_investigator']
        del on_trial['cancer_center_accrual_goal_upper']
        del on_trial['site_list']
        del on_trial['sponsor_list']
        del on_trial['drug_list']
        del on_trial['staff_list']

        status, trial_tree = me.create_trial_tree(on_trial, no_validate=True)
        summary = Summary(on_trial['_clinical'],
                          on_trial['_genomic'],
                          other,
                          trial_tree)
        item = summary.create_summary(on_trial)

        for field in status_fields:
            assert field in item, self._debug(item, field)

    def test_ms_status(self):

        on_trial['_clinical'] = {}
        on_trial['_genomic'] = {'mmr_status': [{'value': 'MMR-Proficient'}]}
        db = get_db()
        me = MatchEngine(db)
        status, trial_tree = me.create_trial_tree(on_trial, no_validate=True)
        summary = Summary(on_trial['_clinical'],
                          on_trial['_genomic'],
                          {},
                          trial_tree)
        item = summary.create_summary(on_trial)
        assert 'mmr_status' in item, self._debug(item, 'mmr_status')

        on_trial['_genomic'] = {'ms_status': [{'value': 'MSI-H'}]}
        status, trial_tree = me.create_trial_tree(on_trial, no_validate=True)
        summary = Summary(on_trial['_clinical'],
                          on_trial['_genomic'],
                          {},
                          trial_tree)
        item = summary.create_summary(on_trial)
        assert 'ms_status' in item, self._debug(item, 'ms_status')

    def test_updatedt_with_curatedt(self):

        # set up
        today = dt.datetime.now().strftime('%B %d, %Y')
        old = 'October 27, 2016'
        on_trial['_genomic'] = {'hugo_symbol': [{'value': 'TEST'}]}
        on_trial['_clinical'] = {'disease_status': [{'value': ['TEST']}]}

        # set both dates to OLD
        on_trial['curated_on'] = old
        on_trial['last_updated'] = old
        assert on_trial['curated_on'] == old, self._debug(on_trial, 'curated_on')
        assert on_trial['last_updated'] == old, self._debug(on_trial, 'last_updated')

        # set "last_updated" to TODAY
        trial = set_updated(on_trial)
        assert trial['curated_on'] == old, self._debug(trial, 'curated_on')
        assert trial['last_updated'] == today, self._debug(trial, 'last_updated')

        # check dates are preserved after trial_insert is called
        trial['protocol_no'] = '01-001'
        trial = trial_insert([trial])
        trial = trial[0]
        assert trial['curated_on'] == old, self._debug(trial, 'curated_on')
        assert trial['last_updated'] == today, self._debug(trial, 'last_updated')

        # check the other way around
        on_trial['curated_on'] = old
        trial['last_updated'] = old
        assert trial['curated_on'] == old, self._debug(trial, 'curated_on')
        assert trial['last_updated'] == old, self._debug(trial, 'last_updated')

        trial = set_curated(on_trial)
        assert trial['curated_on'] == today, self._debug(trial, 'curated_on')
        assert trial['last_updated'] == today, self._debug(trial, 'last_updated')

        trial = trial_insert([trial])
        trial = trial[0]
        assert trial['curated_on'] == today, self._debug(trial, 'curated_on')
        assert trial['last_updated'] == today, self._debug(trial, 'last_updated')

    def test_extract_genes(self):

        m = MatchEngine(get_db())
        match_tree = trial['treatment_list']['step'][0]['match'][0]
        g = m.create_match_tree(match_tree)
        pmt = ParseMatchTree(g)
        genes = pmt.extract_genes()

        assert 'BRAF' in genes, genes
        assert 'KRAS' in genes, genes
        assert 'EGFR' not in genes
        assert 'test' not in genes, genes
        assert len(genes) == 2, genes

        match_tree = trial['treatment_list']['step'][0]['match'][2]
        g = m.create_match_tree(match_tree)
        pmt = ParseMatchTree(g)
        genes = pmt.extract_genes()
        assert 'BRAF' not in genes, genes

    def test_extract_cancer_types(self):

        m = MatchEngine(get_db())
        match_tree = match_tree_example
        g = m.create_match_tree(match_tree)
        pmt = ParseMatchTree(g)
        cancer_type_dict = pmt.extract_cancer_types()

        assert sorted(cancer_type_dict['diagnoses']) == sorted([
            'Ocular Melanoma'
        ]), cancer_type_dict['diagnoses']

        assert sorted(cancer_type_dict['cancer_types_expanded']) == sorted([
            'Ocular Melanoma',
            'Uveal Melanoma',
            'Conjunctival Melanoma'
        ]), cancer_type_dict['cancer_types_expanded']

        assert sorted(cancer_type_dict['excluded_cancer_types']) == [], cancer_type_dict['excluded_cancer_types']
        assert cancer_type_dict['primary_cancer_types'] == ['Eye'], cancer_type_dict['primary_cancer_types']

        m = MatchEngine(get_db())
        match_tree = match_tree_example2
        g = m.create_match_tree(match_tree)
        pmt = ParseMatchTree(g)
        cancer_type_dict = pmt.extract_cancer_types()

        assert sorted(cancer_type_dict['diagnoses']) == sorted(['_SOLID_']), cancer_type_dict['diagnoses']
        assert 'Acute Lymphoid Leukemia' not in cancer_type_dict['cancer_types_expanded'], cancer_type_dict['cancer_types_expanded']
        assert sorted(cancer_type_dict['excluded_cancer_types']) == [], cancer_type_dict['excluded_cancer_types']
        assert cancer_type_dict['primary_cancer_types'] == ['All Solid Tumors'], cancer_type_dict['primary_cancer_types']

        m = MatchEngine(get_db())
        match_tree = match_tree_example3
        g = m.create_match_tree(match_tree)
        pmt = ParseMatchTree(g)
        cancer_type_dict = pmt.extract_cancer_types()

        assert sorted(cancer_type_dict['diagnoses']) == sorted(['_LIQUID_']), cancer_type_dict['diagnoses']
        assert 'Acute Lymphoid Leukemia' in cancer_type_dict['cancer_types_expanded'], cancer_type_dict[
            'cancer_types_expanded']
        assert sorted(cancer_type_dict['excluded_cancer_types']) == [], cancer_type_dict['excluded_cancer_types']
        assert cancer_type_dict['primary_cancer_types'] == ['All Liquid Tumors'], cancer_type_dict['primary_cancer_types']

    def test_extract_variants(self):

        m = MatchEngine(get_db())
        match_tree = trial['treatment_list']['step'][0]['match'][0]
        g = m.create_match_tree(match_tree)
        pmt = ParseMatchTree(g)
        v = pmt.extract_variants()
        assert 'BRAF V600E' in v['variants']
        assert 'BRAF V600K' in v['variants']
        assert 'KRAS any' in v['variants']
        assert 'EGFR wt' in v['wts']
        assert len(v['variants']) == 3
        assert len(v['wts']) == 1

        match_tree = trial['treatment_list']['step'][0]['match'][1]
        g = m.create_match_tree(match_tree)
        pmt = ParseMatchTree(g)
        v = pmt.extract_variants()

        assert 'PTEN CNV' in v['cnvs']
        assert 'BRCA1 SV' in v['svs']
        assert 'BRAF V600' in v['exclusions']
        assert len(v['variants']) == 0
        assert len(v['cnvs']) == 1
        assert len(v['svs']) == 1
        assert len(v['wts']) == 0
        assert len(v['exclusions']) == 1

        match_tree = trial['treatment_list']['step'][0]['match'][2]
        g = m.create_match_tree(match_tree)
        pmt = ParseMatchTree(g)
        v = pmt.extract_variants()
        assert 'BRAF V600E' not in v['variants']
        assert len(v['variants']) == 0
        assert len(v['wts']) == 0
        assert 'BRAF V600E' in v['exclusions']

        match_tree = trial['treatment_list']['step'][0]['match'][4]
        g = m.create_match_tree(match_tree)
        pmt = ParseMatchTree(g)
        v = pmt.extract_variants()
        assert 'BRAF V600K' in v['variants']
        assert 'EGFR any' in v['variants']
        assert len(v['variants']) == 2
        assert 'PTEN CNV' in v['cnvs']
        assert len(v['cnvs']) == 1
        assert 'KRAS' in v['exclusions']
        assert 'NRAS' in v['exclusions']
        assert len(v['exclusions']) == 2
        assert 'NTRK1 wt' in v['wts']
        assert len(v['wts']) == 1

    def test_extract_signatures(self):

        m = MatchEngine(get_db())
        match_tree = trial['treatment_list']['step'][0]['match'][3]
        g = m.create_match_tree(match_tree)
        pmt = ParseMatchTree(g)
        s = pmt.extract_signatures()

        assert 'MMR-D' in s[0]
        assert 'MSI-H' in s[1]

    def test_extract_hr_status(self):

        m = MatchEngine(get_db())
        match_tree = trial['treatment_list']['step'][0]['match'][5]
        g = m.create_match_tree(match_tree)
        pmt = ParseMatchTree(g)
        hr = pmt.extract_hr_status()

        assert sorted(hr) == sorted(['HER2 Negative', 'ER Negative', 'PR Positive'])

    def test_add_autocomplete(self):

        suggestor_options = [
            'cancer_type_suggest',
            'hugo_symbol_suggest',
            'variant_suggest',
            'wildtype_suggest',
            'cnv_suggest',
            'sv_suggest',
            'protocol_no_suggest',
            'disease_center_suggest',
            'disease_status_suggest',
            'drug_suggest',
            'investigator_suggest',
            'mmr_status_suggest',
            'nct_number_suggest'
        ]

        search_options = [
            'tumor_types',
            'genes',
            'variants',
            'wildtype_genes',
            'cnv_genes',
            'sv_genes',
            'exclusion_genes',
            'protocol_no',
            'drugs',
            'age',
            'phase',
            'disease_status',
            'nct_number',
            'disease_center',
            'mmr_status',
            'ms_status',
            'mutational_signatures',
            'investigator',
            'short_title'
        ]

        summary = {
            "short_title": "TITLE",
            "dfci_investigator": {
                "email_address": "FAKE@FAKE.FAKE",
                "first_name": "First",
                "last_name": "Last",
                "is_overall_pi": True,
                "staff_role": "DFCI Principal Investigator",
                "last_first": "Last First",
                "first_last": "First Last",
                "institution_name": "Dana-Farber Cancer Institute"
            },
            "site": [{"id": [0o1], "value": "Dana-Farber Cancer Institute"}],
            "tumor_types": [
                "CT1",
                "CT2",
                "CT3"
            ],
            "sponsor": "Dana-Farber/Harvard Cancer Center",
            "coordinating_center": "Dana-Farber Cancer Institute",
            "protocol_number": "00-001",
            "nct_number": "NCT01",
            "nonsynonymous_genes": [
                "RET",
                "KIT",
                "PDGFRA",
                "PDGFRB"
            ],
            "status": [{"id": [0o1],"value": "Closed to Accrual"}],
            "management_group": [{"id": [0o1], "value": "fake management group value"}],
            "nonsynonymous_wt_genes": [
                "EGFR",
                "KRAS",
                "ALK"
            ],
            "drugs": ["Loxo-101"],
            "genes": [
                "PDGFRB",
                "PDGFRA",
                "wt ALK",
                "wt EGFR",
                "RET",
                "KIT",
                "wt KRAS"
            ],
            "age_summary": "Adults",
            "phase": [{"id": [0o1], "value": "II"}],
            "variants": [],
            "phase_summary": "II",
            "ms_status": "",
            "accrual_goal": 0o1,
            "investigator": "Last, First, M.",
            "age": [{"id": [0o1],"value": "Adults"}],
            "mmr_status": "",
            "mutational_signatures": "",
            "disease_status": ["Advanced"],
            "disease_center": "DF/HCC Lung Cancer (includes thoracic cancers)"
        }

        trial['_summary'] = summary
        autocomplete = Autocomplete(trial)
        suggest, search, pct = autocomplete.add_autocomplete()
        assert sorted(suggest.keys()) == sorted(suggestor_options), list(suggest.keys())
        assert sorted(search.keys()) == sorted(search_options), list(search.keys())
        assert pct == ['Skin']

        cts = suggest['cancer_type_suggest']
        assert isinstance(cts, list)
        assert sorted(cts[0].keys()) == sorted(['input', 'output', 'weight'])
        assert isinstance(cts[0]['input'], list)
        assert isinstance(cts[0]['output'], str)
        cancer_types = [i['output'] for i in cts]
        assert 'Melanoma' in cancer_types
        assert '!Melanoma' not in cancer_types
        assert 'test' not in cancer_types
        assert sorted(cancer_types) == sorted([
            'Skin',
            'Melanoma',
            'Congenital Nevus',
            'Genitourinary Mucosal Melanoma',
            'Cutaneous Melanoma',
            'Melanoma of Unknown Primary',
            'Desmoplastic Melanoma',
            'Lentigo Maligna Melanoma',
            'Acral Melanoma']
        )

        dcs = suggest['disease_center_suggest']
        assert isinstance(dcs, dict)
        assert sorted(dcs.keys()) == sorted(['input', 'output'])
        assert isinstance(dcs['input'], list)
        assert isinstance(dcs['output'], str)

        invs = suggest['investigator_suggest']
        assert isinstance(invs, list)
        assert sorted(invs[0].keys()) == sorted(['input', 'output'])
        assert isinstance(invs[0]['input'], list)
        assert isinstance(invs[0]['output'], str)

        gs = suggest['hugo_symbol_suggest']
        assert isinstance(gs, dict)
        assert list(gs.keys()) == ['input']
        assert 'BRAF' in gs['input']
        assert 'KRAS' in gs['input']
        assert 'test' not in gs['input']
        assert 'PIK3CA' in gs['input']
        assert 'PTEN' in gs['input']
        assert len(gs['input']) == 4

        vs = suggest['variant_suggest']
        assert isinstance(vs, list)
        variants = [i['input'] for i in vs]
        assert 'BRAF V600K' in variants
        assert 'BRAF V600E' in variants
        assert 'EGFR wt' not in variants

        wts = suggest['wildtype_suggest']
        assert isinstance(wts, list)
        assert wts[0]['input'] == 'EGFR wt'
        assert wts[0]['weight'] == 5

        assert sorted(search.keys()) == sorted(search_options)
        assert search['age'] == 'Adults'
        assert search['disease_status'] == ['Advanced']
        assert search['drugs'] == ['Loxo-101']
        assert sorted(search['genes']) == sorted(['BRAF', 'KRAS', 'PIK3CA', 'PTEN'])
        assert search['investigator'] == ['First Last']
        assert sorted(search['tumor_types']) == sorted([
            'Melanoma',
            'Congenital Nevus',
            'Genitourinary Mucosal Melanoma',
            'Cutaneous Melanoma',
            'Melanoma of Unknown Primary',
            'Desmoplastic Melanoma',
            'Skin',
            'Lentigo Maligna Melanoma',
            'Acral Melanoma']
        )
        assert sorted(search['variants']) == sorted(['BRAF V600K', 'BRAF V600E', 'KRAS any', 'PIK3CA any', 'PTEN any'])
        assert sorted(search['wildtype_genes']) == sorted(['EGFR wt'])
        assert 'short_title' in search

        # ----------------------------------------------------------------------- #

        trial2['_summary'] = summary
        autocomplete = Autocomplete(trial2)
        suggest, search, pct = autocomplete.add_autocomplete()
        assert sorted(suggest.keys()) == sorted(suggestor_options)
        assert sorted(search.keys()) == sorted(search_options)

        assert suggest['cnv_suggest'][0]['input'] == 'PTEN CNV'
        assert suggest['cnv_suggest'][0]['weight'] == 3
        assert sorted(suggest['hugo_symbol_suggest']['input']) == sorted(['BRCA1', 'PTEN'])
        assert suggest['sv_suggest'][0]['input'] == 'BRCA1 SV'
        assert suggest['variant_suggest'] == []
        assert suggest['wildtype_suggest'] == []

        assert search['cnv_genes'] == ['PTEN CNV']
        assert search['exclusion_genes'] == ['BRAF V600']
        assert search['sv_genes'] == ['BRCA1 SV']
        assert search['variants'] == []
        assert search['wildtype_genes'] == []

    @staticmethod
    def _debug(trial, field):
        return '%s\nKEY: %s' % (json.dumps(trial, sort_keys=True, indent=4), field)
