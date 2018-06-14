import tempfile
import oncotreenx

from matchminer.utilities import *
from tests.test_matchminer import TestMinimal
from matchminer.trial_search import Autocomplete, expand_liquid_oncotree


class TestUtilities(TestMinimal):

    def setUp(self, settings_file=None, url_converters=None):
        super(TestUtilities, self).setUp(settings_file=None, url_converters=None)
        self.a = Autocomplete({'_summary': {}, 'treatment_list': {}})

    def tearDown(self):
        self.db.registration.drop()

    def test_insertion_memory(self):

        # create temporary data.
        txt = '''Timestamp,First Name,Last Name,Partners ID,Institutional Email Address,Protocol Number for you are requesting access to MatchMiner,Indicate your reason for requesting access to MatchMiner,Approved by ??
4/26/2016,Tom,Test1,test1,TEST1@test.com,00-000,PI,YES
4/27/2016,Joe,Test2,test2,TEST2@test.com,Several,Dz Ctr leader,YES
4/26/2016,Philippe,Test3,test3,TEST3@test.com,00-000,PI,YES
'''

        # build equivalent.
        data = list()
        for line in txt.split("\n"):
            if len(line) == 0: continue
            data.append(line.strip().split(","))

        # test insertion.
        insert_users(data, from_file=False)

        assert self.db.user.find().count() == 6

    def test_insertion_file(self):

        # create temporary data.
        txt = '''Timestamp,First Name,Last Name,Partners ID,Institutional Email Address,Protocol Number for you are requesting access to MatchMiner,Indicate your reason for requesting access to MatchMiner,Approved by ??
4/26/2016,Tom,Test1,test1,TEST1@test.com,00-000,PI,YES
4/27/2016,Joe,Test2,test2,TEST2@test.com,Several,Dz Ctr leader,YES
4/26/2016,Philippe,Test3,test3,TEST3@test.com,00-000,PI,YES
'''

        temp = tempfile.NamedTemporaryFile()
        try:

            # write.
            temp.write(txt)
            temp.seek(0)

            # test insertion.
            insert_users(temp.name, from_file=True)
            assert self.db.user.find().count() == 6

        finally:
            # Automatically cleans up the file
            temp.close()

    def test_revoke_access(self):

        # create temporary data.
        txt = '''Timestamp,First Name,Last Name,Partners ID,Institutional Email Address,Protocol Number for you are requesting access to MatchMiner,Indicate your reason for requesting access to MatchMiner,Approved by ??
4/26/2016,Tom,Test1,test1,TEST1@test.com,00-000,PI,YES
4/27/2016,Joe,Test2,test2,TEST2@test.com,Several,Dz Ctr leader,YES
4/26/2016,Philippe,Test3,test3,TEST3@test.com,00-000,PI,YES
'''

        # build equivalent.
        data = list()
        for line in txt.split("\n"):
            if len(line) == 0: continue
            data.append(line.strip().split(","))

        # test insertion.
        insert_users(data, from_file=False)
        assert self.db.user.find().count() == 6

        # revoke access
        txt = '''Timestamp,First Name,Last Name,Partners ID,Institutional Email Address,Protocol Number for you are requesting access to MatchMiner,Indicate your reason for requesting access to MatchMiner,Approved by ??
4/26/2016,Tom,Test1,test1,TEST1@test.com,00-000,PI,YES
4/27/2016,Joe,Test2,test2,TEST2@test.com,Several,Dz Ctr leader,NO
4/26/2016,Philippe,Test3,test3,TEST3@test.com,00-000,PI,YES
'''

        # build equivalent.
        data = list()
        for line in txt.split("\n"):
            if len(line) == 0: continue
            data.append(line.strip().split(","))

        # test insertion.
        insert_users(data, from_file=False)
        assert self.db.user.find().count() == 6
        assert self.db.user.find_one({"first_name": "Joe"})['user_name'] == ''

    def test_get_investigator_suggest(self):

        investigator = 'Last, First'
        dfci_investigator = {
            'first_name': 'DF',
            'last_name': 'DL'
        }
        inv_suggest = self.a._get_investigator_suggest(investigator, dfci_investigator)
        assert sorted(inv_suggest[0]['input']) == sorted(['First', 'Last'])
        assert inv_suggest[0]['output'] == 'First Last'
        assert sorted(inv_suggest[1]['input']) == sorted(['DF', 'DL'])
        assert inv_suggest[1]['output'] == 'DF DL'

        investigator = 'Last, First, M'
        dfci_investigator = {
            'first_name': 'DF',
            'last_name': 'DL'
        }
        inv_suggest = self.a._get_investigator_suggest(investigator, dfci_investigator)
        assert sorted(inv_suggest[0]['input']) == sorted(['First', 'Last'])
        assert inv_suggest[0]['output'] == 'First Last'
        assert sorted(inv_suggest[1]['input']) == sorted(['DF', 'DL'])
        assert inv_suggest[1]['output'] == 'DF DL'

        investigator = 'Last'
        dfci_investigator = {
            'first_name': 'DF',
            'last_name': 'DL'
        }
        inv_suggest = self.a._get_investigator_suggest(investigator, dfci_investigator)
        assert sorted(inv_suggest[0]['input']) == sorted(['Last'])
        assert inv_suggest[0]['output'] == 'Last'
        assert sorted(inv_suggest[1]['input']) == sorted(['DF', 'DL'])
        assert inv_suggest[1]['output'] == 'DF DL'

        investigator = ''
        dfci_investigator = {
            'first_name': 'DF',
            'last_name': 'DL'
        }
        inv_suggest = self.a._get_investigator_suggest(investigator, dfci_investigator)
        assert sorted(inv_suggest[0]['input']) == sorted([])
        assert inv_suggest[0]['output'] == ''
        assert sorted(inv_suggest[1]['input']) == sorted(['DF', 'DL'])
        assert inv_suggest[1]['output'] == 'DF DL'

        investigator = 'Last, First'
        dfci_investigator = {
            'last_name': 'DL'
        }
        inv_suggest = self.a._get_investigator_suggest(investigator, dfci_investigator)
        assert sorted(inv_suggest[0]['input']) == sorted(['First', 'Last'])
        assert inv_suggest[0]['output'] == 'First Last'
        assert sorted(inv_suggest[1]['input']) == sorted(['DL'])
        assert inv_suggest[1]['output'] == 'DL'

        investigator = 'Last, First'
        dfci_investigator = {
            'first_name': 'DL'
        }
        inv_suggest = self.a._get_investigator_suggest(investigator, dfci_investigator)
        assert sorted(inv_suggest[0]['input']) == sorted(['First', 'Last'])
        assert inv_suggest[0]['output'] == 'First Last'
        assert sorted(inv_suggest[1]['input']) == sorted(['DL'])
        assert inv_suggest[1]['output'] == 'DL'

        investigator = 'Last, First'
        dfci_investigator = {}
        inv_suggest = self.a._get_investigator_suggest(investigator, dfci_investigator)
        assert sorted(inv_suggest[0]['input']) == sorted(['First', 'Last'])
        assert inv_suggest[0]['output'] == 'First Last'
        assert len(inv_suggest) == 1

        investigator = 'Last, First'
        dfci_investigator = None
        inv_suggest = self.a._get_investigator_suggest(investigator, dfci_investigator)
        assert sorted(inv_suggest[0]['input']) == sorted(['First', 'Last'])
        assert inv_suggest[0]['output'] == 'First Last'
        assert len(inv_suggest) == 1

        investigator = 'Last, First'
        dfci_investigator = 'First Last'
        inv_suggest = self.a._get_investigator_suggest(investigator, dfci_investigator)
        assert sorted(inv_suggest[0]['input']) == sorted(['First', 'Last'])
        assert inv_suggest[0]['output'] == 'First Last'
        assert len(inv_suggest) == 1

    def test_expand_liquid_oncotree(self):

        onco_tree = oncotreenx.build_oncotree(file_path=TUMOR_TREE)
        l, s, = expand_liquid_oncotree(onco_tree)
        assert 'Leukemia' in l
        assert 'Leukemia' not in s

    def test_get_cancer_type_weight(self):

        ct = "Breast"
        r = self.a._get_cancer_type_weight(ct, hierarchy='primary')
        assert r['input'] == ["Breast"]
        assert r['output'] == 'Breast'
        assert r['weight'] == 10

        ct = "Non-Small Cell Lung Cancer"
        r = self.a._get_cancer_type_weight(ct)
        assert sorted(r['input']) == sorted(["Non-Small Cell Lung Cancer", "Non-Small", "Cell", "Lung", "Cancer"])
        assert r['output'] == "Non-Small Cell Lung Cancer", r
        assert r['weight'] == 5

        ct = "All Solid Tumors"
        r = self.a._get_cancer_type_weight(ct)
        assert sorted(r['input']) == sorted(["All Solid Tumors", "Solid", "Tumors"]), r
        assert r['output'] == "All Solid Tumors", r
        assert r['weight'] == 20

        ct = "All Liquid Tumors"
        r = self.a._get_cancer_type_weight(ct)
        assert sorted(r['input']) == sorted(["All Liquid Tumors", "Liquid", "Tumors"])
        assert r['output'] == "All Liquid Tumors", r
        assert r['weight'] == 20

    def test_get_variants_weight(self):

        v = 'IDH1 wt'
        r = self.a._get_variants_weight(v, esrule='wts')
        assert r['input'] == 'IDH1 wt'
        assert r['weight'] == 5

        v = 'IDH1 R132C'
        r = self.a._get_variants_weight(v)
        assert r['input'] == 'IDH1 R132C'
        assert r['weight'] == 1

        v = 'PTEN CNV'
        r = self.a._get_variants_weight(v, esrule='cnvs')
        assert r['input'] == 'PTEN CNV'
        assert r['weight'] == 3

        v = 'BRCA1 SV'
        r = self.a._get_variants_weight(v, esrule='svs')
        assert r['input'] == 'BRCA1 SV'
        assert r['weight'] == 3

    def test_get_tumor_types_search(self):

        ct_suggest = [{
            'input': ["Non-Small Cell Lung Cancer", 'Non-Small', 'Cell', 'Lung', 'Cancer'],
            'output': "Non-Small Cell Lung Cancer",
            'weight': 5
        }]
        r = self.a._get_tumor_types_search(ct_suggest)
        assert r == ["Non-Small Cell Lung Cancer"]

        ct_suggest = [{
            'input': ["All Solid Tumors", 'All', 'Solid', 'Tumors'],
            'output': "All Solid Tumors",
            'weight': 1
        }]
        r = self.a._get_tumor_types_search(ct_suggest)
        assert r == ["_SOLID_"]

        ct_suggest = [{
            'input': ["All Liquid Tumors", 'All', 'Liquid', 'Tumors'],
            'output': "All Liquid Tumors",
            'weight': 1
        }]
        r = self.a._get_tumor_types_search(ct_suggest)
        assert r == ["_LIQUID_"]
