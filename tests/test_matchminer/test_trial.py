## import
import os
import yaml
import copy
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
            test_json = yaml.load(fin)

        # post and it should fail.
        r, status_code = self.post("trial", test_json)
        assert status_code == 422, r

        # add values to database.
        self.db['normalize'].drop()
        mapping = copy.deepcopy(self.mapping)
        mapping['values']['oncotree_primary_diagnosis']["Diffuse Large B-Cell Lymphoma"] = "Diffuse Large B-Cell Lymphoma"
        self.db['normalize'].insert(mapping)

        # post and it should pass
        r, status_code = self.post("trial", test_json)
        assert r['treatment_list']['step'][1]['arm'][1]['match'][0]['and'][1]['clinical']['oncotree_primary_diagnosis'] == '!Diffuse Large B-Cell Lymphoma'
        assert r['status'] == 'Open to Accrual'
        assert status_code == 201

        db_trial = self.db['trial'].find_one({'protocol_no': '00-003'})

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
        assert sorted(db_trial['_suggest'].keys()) == sorted(suggestor_options)

        genes = db_trial['_suggest']['hugo_symbol_suggest']['input']
        assert isinstance(genes, list)
        assert 'MYC' in genes
        assert len(genes) == 1

        assert db_trial['_suggest']['cancer_type_suggest'] == []

    def test_trial_put(self):

        # define test json
        with open(os.path.join(YAML_DIR, "00-001.yml")) as fin:
            test_json = yaml.load(fin)

        # add values to database.
        self.db['normalize'].drop()
        mapping = copy.deepcopy(self.mapping)
        mapping['values']['oncotree_primary_diagnosis']["Diffuse Large B-Cell Lymphoma"] = "Diffuse Large B-Cell Lymphoma"
        self.db['normalize'].insert(mapping)

        # post and it should fail.
        r, status_code = self.post("trial", test_json)
        assert status_code == 201

        # update it.
        etag = r['_etag']
        trial_id = r['_id']
        for key in list(r.keys()):
            if key[0] == '_':
                del r[key]

        # manually tweak
        r['treatment_list']['step'][0]['arm'][0]['match'][0]['and'][1]['clinical']['oncotree_primary_diagnosis'] = "Bladder Urothelial Carcinoma"

        # PUT the udpate
        r, status_code = self.patch("trial/%s" % trial_id, r, headers=[('If-Match', etag)])
        assert status_code == 200

        # assert the _ vars are updated.
        assert len(r['_summary']['tumor_types']) == 2
        assert sorted(r['_summary']['tumor_types'])[0] == "Bladder Urothelial Carcinoma"
        assert sorted(r['_summary']['tumor_types'])[1] == "_SOLID_"
