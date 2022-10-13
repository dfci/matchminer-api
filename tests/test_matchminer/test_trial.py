import os
import yaml
import copy

from matchminer.event_hooks.trial import build_trial_elasticsearch_fields
from tests.test_matchminer import TestMinimal

YAML_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../', 'data/yaml'))
TEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../', 'data'))

## test classes

class TestTrial(TestMinimal):

    mapping = {
        "key": "trial",
        "values": {
            "oncotree_primary_diagnosis": {
                "cns/brain": "CNS/Brain",
                "myelodysplasia": "Myelodysplasia",
                "_SOLID_": "_SOLID_",
                "_LIQUID_": "_LIQUID_",
                "Glioblastoma": "Glioblastoma",
                "Gliosarcoma": "Gliosarcoma",
                "Anaplastic Astrocytoma": "Anaplastic Astrocytoma",
                "breast": "Breast",
                "Non-Hodgkin Lymphoma": "Non-Hodgkin Lymphoma",
                "Bladder Urothelial Carcinoma": "Bladder Urothelial Carcinoma"
            },
            "status": {
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
            }
        }
    }

    def setUp(self, settings_file=None, url_converters=None):

        # call parent
        super(TestTrial, self).setUp(settings_file=None, url_converters=None)

        # switch to service account.
        self.user_token = self.curator_token

        # drop any normalizations.
        self.db['normalize'].drop()

        # insert the mapping
        self.db['normalize'].insert(self.mapping)

    def tearDown(self):

        # drop any normalizations.
        self.db['normalize'].drop()

    def test_trial_validation(self):

        # define test json
        with open(os.path.join(YAML_DIR, "00-003.yml")) as fin:
            test_json = yaml.safe_load(fin)

        # post and it should fail.
        r, status_code = self.post("trial", test_json)
        assert status_code == 422, r

        # add values to database.
        self.db['normalize'].drop()
        mapping = copy.deepcopy(self.mapping)
        mapping['values']['oncotree_primary_diagnosis']["Diffuse Large B-Cell Lymphoma"] = "Diffuse Large B-Cell Lymphoma"
        self.db['normalize'].insert(mapping)

        # post and it should pass
        build_trial_elasticsearch_fields([test_json])
        assert test_json['treatment_list']['step'][1]['arm'][1]['match'][0]['and'][1]['clinical']['oncotree_primary_diagnosis'] == '!Diffuse Large B-Cell Lymphoma'
        assert test_json['status'] == 'OPEN TO ACCRUAL'


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
        assert sorted(test_json['_suggest'].keys()) == sorted(suggestor_options)

        genes = test_json['_suggest']['hugo_symbol_suggest']['input']
        assert isinstance(genes, list)
        assert 'MYC' in genes
        assert len(genes) == 1

        assert test_json['_suggest']['cancer_type_suggest'] == []

