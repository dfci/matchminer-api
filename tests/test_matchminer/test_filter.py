import json
from bson.objectid import ObjectId
from tests.test_matchminer import TestMinimal


class TestFilter(TestMinimal):
    def setUp(self, settings_file=None, url_converters=None):

        # call parent
        super(TestFilter, self).setUp(settings_file=None, url_converters=None)
        self.db['run_log_match'].drop()
        self.db['clinical_run_history_match'].drop()

    def tearDown(self):
        self.db['run_log_match'].drop()
        self.db['clinical_run_history_match'].drop()

    def test_post_tmp(self):

        # make a complex query.
        dt = "1926-02-03T11:28:34.144Z"
        c = {
            "BIRTH_DATE": {"^gt": dt},
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
            'label': 'test',
            'temporary': True,
            'status': 1
        }

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # no matches should be present.
        assert self.db['match'].count() == 0

        # insert without temporary and we get matches.
        rule['temporary'] = False

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # matches should be present
        assert self.db['match'].count() > 0

        # ensure user and team is transferred.
        for x in self.db['match'].find():
            assert str(x['TEAM_ID']) == str(self.team_id)
            assert str(x['USER_ID']) == str(self.user_id)


    def test_post_time(self):

        # make a complex query.
        c = {
            "BIRTH_DATE": {"^gt": "1926-02-03T11:28:34.144Z"},
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
            'label': 'test',
            'temporary': False,
            'status': 1
        }

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        r = self.get('match')
        num_matches = len(r[0]['_items'])
        assert num_matches > 20


    def test_post_special(self):

        # make a complex query.
        c = {
            "ONCOTREE_PRIMARY_DIAGNOSIS_NAME": "_LIQUID_"
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
            'label': 'test',
            'temporary': True,
            'status': 1
        }

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # insert it.
        rule['clinical_filter']["ONCOTREE_PRIMARY_DIAGNOSIS_NAME"] = "_SOLID_"
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

    def test_post_dt(self):

        # make a complex query.
        dt = "1926-02-03T11:28:34.144Z"
        c = {
            "BIRTH_DATE": {"^gt": dt},
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
            'label': 'test',
            'temporary': True,
            'status': 1
        }

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

    def test_post_in(self):

        # make a complex query.
        g = {
            "WILDTYPE": True,
            "VARIANT_CATEGORY": ["Mutation", "CNV"],
            "TRUE_HUGO_SYMBOL": ["ERCC2"]
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'genomic_filter': g,
            'label': 'test',
            'temporary': True,
            'status': 1
        }

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # ensure we only have 1.
        assert self.db['filter'].count() == 1

    def test_put(self):

        # make a filter.
        c = {"GENDER": "Male"}
        g = {'CNV_CALL': ["High level amplification"]}
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
            'genomic_filter': g,
            'label': 'test',
            'temporary': False,
            'status': 1
        }

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        r = self.get('match')
        num_matches = len(r[0]['_items'])
        assert num_matches > 0

    def test_post_gen_only(self):

        # make a filter.
        g = {
            'CNV_CALL': ["High level amplification"]
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

        # ensure we only have 1.
        assert self.db['filter'].count() == 1

        r = self.get('match')
        assert len(r[0]['_items']) > 0

    def test_post_clin_only(self):

        # make a filter.
        c = {
            "GENDER": "Male"
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
            'label': 'test',
            'temporary': False,
            'status': 1
        }

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # ensure we only have 1.
        assert self.db['filter'].count() == 1

        r = self.get('match')
        assert len(r[0]['_items']) > 0

    def test_EYS(self):

        # make a filter.
        g = {
            "TRUE_HUGO_SYMBOL": ["EYS"],
            "WILDTYPE": False,
            "VARIANT_CATEGORY": ["MUTATION"]
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'genomic_filter': g,
            'clinical_filter': {},
            'label': 'test',
            'temporary': False,
            'status': 1
        }

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # update variables.
        filter_id = r['_id']
        etag = r['_etag']
        rule['genomic_filter']['TRUE_HUGO_SYMBOL'] = ["ERBB4"]

        r, status_code = self.put('filter/%s' % filter_id, rule, headers=[('If-Match', etag)])
        self.assert200(status_code)

        # get the results via resource.
        qstr = "?where=%s" % json.dumps(({"status": 1, "TEAM_ID": str(self.team_id)}))
        rget, status_code = self.get("filter", query=qstr)
        self.assert200(status_code)

        # assert they all stay the same.
        for x in rget['_items']:
            assert x['genomic_filter']['TRUE_HUGO_SYMBOL'] == ['ERBB4']

    def test_protein(self):

        # make a filter.
        g = {
            "TRUE_HUGO_SYMBOL": ["EYS"],
            "WILDTYPE": False,
            "VARIANT_CATEGORY": ["MUTATION"],
            "TRUE_PROTEIN_CHANGE": "p.C757S"
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

        r = self.get('match')
        assert len(r[0]['_items']) > 0

    def test_exon(self):

        # make a filter.
        g = {
            "TRUE_HUGO_SYMBOL": ["EYS"],
            "WILDTYPE": False,
            "VARIANT_CATEGORY": ["MUTATION"],
            "TRUE_TRANSCRIPT_EXON": 15
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'genomic_filter': g,
            'clinical_filter': {},
            'label': 'test',
            'temporary': False,
            'status': 1
        }

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        r = self.get('match')
        assert len(r[0]['_items']) > 0

    def test_re_sv(self):

        texts = ["KMT2D MLL2", "KMT2D (MLL2)", "MLL2 KMT2D", "(MLL2) KM2D"]
        token = "MLL"
        token2 = "MLL2"

        import re
        x = re.compile("(.*\W%s\W.*)|(^%s\W.*)|(.*\W%s$)|(\\b%s\\b)" % (token, token, token, token), re.IGNORECASE)
        for text in texts:
            match = x.match(text)
            assert match is None, text

        y = re.compile("(.*\W%s\W.*)|(^%s\W.*)|(.*\W%s$)" % (token2, token2, token2), re.IGNORECASE)
        for text in texts:
            match = y.match(text)
            assert match is not None, text

        assert x.match("MLL") is not None

    def test_wildtype(self):

        # make a filter.
        g = {
            "TRUE_HUGO_SYMBOL": ["EYS"],
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
        status_code = self.post('filter', rule)
        self.assert201(status_code[1])

        r = self.get('match')
        r_notwild = len(r[0]['_items'])
        assert len(r[0]['_items']) > 0

        # insert a wild one.
        rule['genomic_filter']['WILDTYPE'] = True
        status_code = self.post('filter', rule)
        self.assert201(status_code[1])

        r = self.get('match')
        r_wild = len(r[0]['_items'])
        assert len(r[0]['_items']) > 0

        # make sure we got the total.
        assert r_notwild + r_wild > 50

    def test_post_description(self):

        # make a filter.
        c = {
            "GENDER": "Male"
        }
        g = {
            "TRUE_HUGO_SYMBOL": ["ERCC2"],
            'VARIANT_CATEGORY': ['MUTATION']
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
            'genomic_filter': g,
            'label': 'test',
            'temporary': False,
            'status': 1
        }

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        filter_doc = self.db['filter'].find_one({"_id": ObjectId(r['_id'])})
        assert filter_doc['description'] == "ERCC2 Mutation, Gender: Male"

        # more complex filter.
        rule['genomic_filter']['TRUE_HUGO_SYMBOL'] = ["ERCC2", "EGFR3"]
        rule['genomic_filter']['VARIANT_CATEGORY'] = ["MUTATION", "SV"]
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        filter_doc = self.db['filter'].find_one({"_id": ObjectId(r['_id'])})
        assert filter_doc['description'] == "ERCC2, EGFR3: Mutation, Structural rearrangement, Gender: Male"

        # most complex filter.
        rule['clinical_filter']['ONCOTREE_PRIMARY_DIAGNOSIS_NAME'] = "_LIQUID_"
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        filter_doc = self.db['filter'].find_one({"_id": ObjectId(r['_id'])})
        assert filter_doc[
                   'description'] == "ERCC2, EGFR3: Mutation, Structural rearrangement in Liquid cancers, Gender: Male"

        rule['clinical_filter']['ONCOTREE_PRIMARY_DIAGNOSIS_NAME'] = "Adrenocortical Adenoma"
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        filter_doc = self.db['filter'].find_one({"_id": ObjectId(r['_id'])})
        assert filter_doc[
                   'description'] == "ERCC2, EGFR3: Mutation, Structural rearrangement in Adrenocortical Adenoma, Gender: Male"

        # EXON specified.
        rule['genomic_filter']['TRUE_HUGO_SYMBOL'] = "ERCC2"
        rule['genomic_filter']['TRUE_TRANSCRIPT_EXON'] = 10
        rule['genomic_filter']['VARIANT_CATEGORY'] = ["MUTATION"]
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        filter_doc = self.db['filter'].find_one({"_id": ObjectId(r['_id'])})
        assert filter_doc['description'] == "ERCC2 exon 10 Mutation in Adrenocortical Adenoma, Gender: Male"

        # protein specified.
        del rule['genomic_filter']['TRUE_TRANSCRIPT_EXON']
        rule['genomic_filter']['TRUE_PROTEIN_CHANGE'] = "V600E"
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        filter_doc = self.db['filter'].find_one({"_id": ObjectId(r['_id'])})
        assert filter_doc['description'] == "ERCC2 V600E Mutation in Adrenocortical Adenoma, Gender: Male"

        # signature specified
        del rule['genomic_filter']['TRUE_HUGO_SYMBOL']
        del rule['genomic_filter']['TRUE_PROTEIN_CHANGE']
        rule['genomic_filter']['VARIANT_CATEGORY'] = ['SIGNATURE']
        rule['genomic_filter']['POLE_STATUS'] = 'Yes'
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        filter_doc = self.db['filter'].find_one({"_id": ObjectId(r['_id'])})
        assert filter_doc['description'] == "PolE Signature in Adrenocortical Adenoma, Gender: Male"

        # Age is being calculated temporarily in relation to today's date which makes testing difficult.
        # Once ages are represented entirely as CTML can add this back
        # age specified.
        # dt = "2002-02-03T11:28:34.144Z"
        # rule['clinical_filter']['BIRTH_DATE'] = {"^lt": dt}
        # r, status_code = self.post('filter', rule)
        # self.assert201(status_code)
        #
        # filter_doc = self.db['filter'].find_one({"_id": ObjectId(r['_id'])})
        # assert filter_doc['description'] == 'ERCC2 V600E Mutation in Adrenocortical Adenoma, Gender: Male, Age > 17'
