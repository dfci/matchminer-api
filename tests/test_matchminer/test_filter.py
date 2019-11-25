## import
import os
import pprint
import datetime
import time
import json
import hashlib
from email.utils import formatdate
from bson.objectid import ObjectId

from matchminer.constants import synonyms
from tests.test_matchminer import TestMinimal
from matchminer.utilities import add_simulated_sv

## test classes

class TestFilter(TestMinimal):

    def test_post_tmp(self):

        # make a complex query.
        dt = formatdate(time.mktime(datetime.datetime(year=1995, month=1, day=1).timetuple()), localtime=False, usegmt=True)
        c = {
                "BIRTH_DATE": {"$gte": dt},
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

            # check that the data_push_id is set correctly
            assert 'data_push_id' in x
            assert x['data_push_id'] is None

    def test_post_time(self):

        # make a complex query.
        c = {
                "BIRTH_DATE": {"$gte": "1926-02-03T11:28:34.144Z"},
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
        assert r['num_clinical'] > 20

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
        dt = formatdate(time.mktime(datetime.datetime(year=2000, month=1, day=1).timetuple()), localtime=False, usegmt=True)
        c = {
                "BIRTH_DATE": {"$gte": dt},
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

        # run the filter_doc manually.
        dt = datetime.datetime(year=2000, month=1, day=1)
        c = {
            "BIRTH_DATE": {"$gte": dt}
        }
        self.cbio.match(c=c)
        assert self.cbio.match_df.shape[0] == r['num_matches']


    def test_post_and(self):
        return # disabled until needed

        # make a complex query.
        dt = formatdate(time.mktime(datetime.datetime(year=1995, month=1, day=1).timetuple()), localtime=False, usegmt=True)
        c = {
            "$and": [
                {"BIRTH_DATE": {"$gte": dt}},
                {"GENDER": "male"},
            ]
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

        # ensure we only have 1.
        assert self.db['filter'].count() == 1

        # run the filter_doc manually.
        dt = datetime.datetime(year=1995, month=1, day=1)
        c = {
            "$and": [
                {"BIRTH_DATE": {"$gte": dt}},
                {"GENDER": "male"},
            ]
        }
        self.cbio.match(c=c)
        assert self.cbio.match_df.shape[0] == r['num_matches']

    def test_post_in(self):

        # make a complex query.
        g = {
            "WILDTYPE": True,
            "VARIANT_CATEGORY": {
                "$in": ["Mutation", "CNV"]
            },
            "TRUE_HUGO_SYMBOL": "ERCC2"
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

    def test_post_oncotree(self):

        # make a complex query.
        c = {
            "ONCOTREE_PRIMARY_DIAGNOSIS_NAME": "Adrenal Gland"
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

        # ensure we et lots of results.
        assert r['num_genomic'] > 500

    def test_post_empty(self):

        # make a silly filter.
        c = {
            "GENDER": "silly"
        }
        g = {
            'CNV_CALL': "High level amplification"
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
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

        # assert the number of matches in filter.
        assert r['num_clinical'] == 0
        assert r['num_matches'] == 0

        # modify the filters to be genomic silly.
        c['GENDER'] = 'male'
        g['CNV_CALL'] = 'silly'

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # ensure we only have 1.
        assert self.db['filter'].count() == 2

        # assert the number of matches in filter.
        assert r['num_genomic'] == 0
        assert r['num_matches'] == 0

        # modify the filters to be double silly.
        c['GENDER'] = 'silly'
        g['CNV_CALL'] = 'silly'

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # ensure we only have 1.
        assert self.db['filter'].count() == 3

        # assert the number of matches in filter.
        assert r['num_genomic'] == 0
        assert r['num_clinical'] == 0
        assert r['num_matches'] == 0

    def test_put_dirty(self):

        # make a filter.
        c = {
            "GENDER": "Male"
        }
        g = {
            'CNV_CALL': "High level amplification"
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
        assert self.db['match'].count() > 0

        # get the filter.
        r, status_code = self.get('filter/%s' % (r['_id']))
        self.assert200(status_code)

        # update variables.
        filter_id = r['_id']
        etag = r['_etag']
        r['genomic_filter']['CNV_CALL'] = "Heterozygous deletion"

        # sanitize object except for _id.
        for key in list(r.keys()):
            if key[0] == "_" and key != "_id":
                del r[key]

        r, status_code = self.put('filter/%s' % filter_id, r, headers=[('If-Match', etag)])
        self.assert200(status_code)
        assert self.db['match'].count() > 0

    def test_put(self):

        # set time constraints.
        start = time.time()

        # make a filter.
        c = {
            "GENDER": "Male"
        }
        g = {
            'CNV_CALL': "High level amplification"
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
        num_matches = r['num_matches']
        filter_objectid = ObjectId(r['_id'])
        assert self.db['match'].count() > 0

        # make sure the filter_hash is set.
        assert 'filter_hash' not in r
        filter_obj = self.db['filter'].find_one({'_id': filter_objectid})
        assert 'filter_hash' in filter_obj

        # update variables.
        filter_id = r['_id']
        etag = r['_etag']
        rule['genomic_filter']['CNV_CALL'] = "Heterozygous deletion"

        r, status_code = self.put('filter/%s' % filter_id, rule, headers=[('If-Match', etag)])
        self.assert200(status_code)
        assert self.db['match'].count() > 0

        # assert we have different number of matches.
        assert num_matches != r['num_matches']
        db_cnt = self.db['match'].count()
        re_cnt = r['num_samples']
        assert db_cnt == re_cnt

        # ensure match status is 1.
        results = list(self.db['match'].find({'FILTER_ID': filter_objectid}))
        assert len(results) > 0
        for match in results:
            assert match['FILTER_STATUS'] == 1

        # update variables status
        filter_id = r['_id']
        etag = r['_etag']
        rule['label'] = 'cheese'

        r, status_code = self.put('filter/%s' % filter_id, rule, headers=[('If-Match', etag)])
        self.assert200(status_code)
        assert self.db['match'].count() > 0

        # assert we have updated stats.
        results = list(self.db['match'].find({'FILTER_ID': filter_objectid}))
        assert len(results) > 0
        for match in results:
            assert match['FILTER_NAME'] == rule['label']


    def test_post_both(self):

        # set time constraints.
        start = time.time()

        # make a filter.
        c = {
            "GENDER": "male"
        }
        g = {
            'CNV_CALL': "High level amplification"
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

        # track duration.
        ttr = time.time() - start

        # ensure we only have 1.
        assert self.db['filter'].count() == 1

        # run the manual tcm.
        match_df = self.cbio.match(c=c, g=g)

        # assert the number of matches in filter.
        #print r['num_genomic'], self.cbio.genomic_df.shape
        assert r['num_genomic'] == self.cbio.genomic_df.shape[0]
        assert r['num_clinical'] == self.cbio.clinical_df.shape[0]

        # check we inserted the right number of matches.
        matches = list(self.db['match'].find({'FILTER_ID': ObjectId(r['_id'])}))
        match_cnt = len(matches)
        assert r['num_samples'] == match_cnt, (r['num_samples'], match_cnt)

        # these shouldn't take long
        assert ttr < 10.0, ttr

    def test_post_gen_only(self):

        # make a filter.
        g = {
            'CNV_CALL': "High level amplification"
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

        # run the manual tcm.
        match_df = self.cbio.match(g=g)

        # assert the number of matches in filter.
        assert r['num_genomic'] == self.cbio.genomic_df.shape[0]

    def test_post_clin_only(self):

        # make a filter.
        c = {
            "GENDER": "male"
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

        # ensure we only have 1.
        assert self.db['filter'].count() == 1

        # run the manual tcm.
        match_df = self.cbio.match(c=c)

        # assert the number of matches in filter.
        assert r['num_clinical'] == self.cbio.clinical_df.shape[0]

    def test_EYS(self):

        # try this test 10 times.
        for x in range(10):

            # make a filter.
            g = {
                "TRUE_HUGO_SYMBOL": "EYS",
                "WILDTYPE": False,
                "VARIANT_CATEGORY": {"$in":["MUTATION"]}
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

            # update variables.
            filter_id = r['_id']
            etag = r['_etag']
            rule['genomic_filter']['TRUE_HUGO_SYMBOL'] = "ERBB4"

            r, status_code = self.put('filter/%s' % filter_id, rule, headers=[('If-Match', etag)])
            self.assert200(status_code)

            # get the results via resource.
            qstr = "?where=%s" % json.dumps(({"status": 1, "TEAM_ID": str(self.team_id)}))
            rget, status_code = self.get("filter", query=qstr)
            self.assert200(status_code)

            # assert they all stay the same.
            for x in rget['_items']:
                assert x['genomic_filter']['TRUE_HUGO_SYMBOL'] == 'ERBB4'

    def test_protein(self):

        # try this test 10 times.
        for x in range(10):

            # make a filter.
            g = {
                "TRUE_HUGO_SYMBOL": "EYS",
                "WILDTYPE": False,
                "VARIANT_CATEGORY": {"$in":["MUTATION"]},
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
            assert r['num_matches'] == 1

    def test_exon(self):

        # try this test 10 times.
        for x in range(10):

            # make a filter.
            g = {
                "TRUE_HUGO_SYMBOL": "EYS",
                "WILDTYPE": False,
                "VARIANT_CATEGORY": {"$in":["MUTATION"]},
                "TRUE_TRANSCRIPT_EXON": 15
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
            assert r['num_matches'] > 0


    def test_svfreetext(self):

        # simplify.
        gene1 = "ZNRF3"
        gene2 = "PMS2"

        # make a filter.
        g = {
            "TRUE_HUGO_SYMBOL": gene1,
            "WILDTYPE": False,
            "VARIANT_CATEGORY": {"$in": ["SV"]}
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

        # make sure we have 5 hit.
        assert r['num_genomic'] == 1

        # try with multiple genes.
        rule['genomic_filter']['TRUE_HUGO_SYMBOL'] = {"$in": [gene1, gene2]}

        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # make sure we have 1 hit.
        assert r['num_genomic'] == 1

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

        # try this test 10 times.
        for x in range(10):

            # make a filter.
            g = {
                "TRUE_HUGO_SYMBOL": "EYS",
                "WILDTYPE": False,
                "VARIANT_CATEGORY": {"$in":["MUTATION"]}
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
            r_notwild, status_code = self.post('filter', rule)
            self.assert201(status_code)

            # insert a wild wone.
            rule['genomic_filter']['WILDTYPE'] = True
            r_wild, status_code = self.post('filter', rule)
            self.assert201(status_code)

            # make sure we got the total.
            assert r_notwild['num_samples'] + r_wild['num_samples'] > 50

    def test_histogram(self):

        # add a brand new clinical
        tmp = self.user_token
        self.user_token = self.service_token
        _ = self._insert_pair()
        self.user_token = tmp

        # make a filter.
        g = {
            "TRUE_HUGO_SYMBOL": "SEMA6D",
            "WILDTYPE": False,
            "VARIANT_CATEGORY": {"$in": ["MUTATION"]}
        }
        c = {
            "ONCOTREE_PRIMARY_DIAGNOSIS_NAME": "Pheochromocytoma",
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'genomic_filter': g,
            #'clinical_filter': c,
            'label': 'test',
            'temporary': False,
            'status': 1
        }

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # assert the histogram is present.
        assert 'enrollment' in r

        # assert we have a hit in the last bin
        cur_month = datetime.date.today()
        x = datetime.datetime(cur_month.year, cur_month.month, 1).strftime("%y-%m-%d")
        assert r['enrollment']['x_axis'][-1] == x, r['enrollment']['x_axis']
        assert r['enrollment']['y_axis'][-1] == 1, r['enrollment']['y_axis']

        # assert we have the graph
        assert 'png' not in r['enrollment']
        assert 'matches' not in r

    def test_post_multicat(self):

        # make rules.
        m_g = {
            "TRUE_HUGO_SYMBOL": {"$in": ["BMPR1A"]},
            "VARIANT_CATEGORY": {"$in": ["MUTATION"]},
            "WILDTYPE": False,
        }
        c_g = {
            "TRUE_HUGO_SYMBOL": {"$in": ["BMPR1A"]},
            "VARIANT_CATEGORY": {"$in": ["CNV"]},
            "CNV_CALL": {"$in": ["Homozygous deletion"]},
            "WILDTYPE": False,
        }
        s_g = {
            "TRUE_HUGO_SYMBOL": {"$in": ["BMPR1A"]},
            "VARIANT_CATEGORY": {"$in": ["SV"]},
            "WILDTYPE": False,
        }
        g = {
            "TRUE_HUGO_SYMBOL": {"$in": ["BMPR1A"]},
            "VARIANT_CATEGORY": {"$in": ["MUTATION", "CNV"]},
            "CNV_CALL": {"$in": ["Homozygous deletion"]},
            "WILDTYPE": False,
        }
        c = {}

        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
            'label': 'test',
            'temporary': False,
            'status': 1
        }

        # run mutation.
        rule['genomic_filter'] = m_g
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)
        m_matches = set([x['CLINICAL_ID'] for x in list(self.db['match'].find({'FILTER_ID': ObjectId(r['_id'])}))])

        # run cnv.
        rule['genomic_filter'] = c_g
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)
        c_matches = set([x['CLINICAL_ID'] for x in list(self.db['match'].find({'FILTER_ID': ObjectId(r['_id'])}))])

        u_matches = set([str(x) for x in m_matches.union(c_matches)])

        # run combined.
        rule['genomic_filter'] = g
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)
        matches = set([str(x['CLINICAL_ID']) for x in list(self.db['match'].find({'FILTER_ID': ObjectId(r['_id'])}))])

        # make sure we get all.
        assert u_matches == matches

    def test_post_multicat_sv(self):


        # make rules.
        m_g = {
            "TRUE_HUGO_SYMBOL": {"$in": ["BMPR1A"]},
            "VARIANT_CATEGORY": {"$in": ["MUTATION"]},
            "WILDTYPE": False,
        }
        c_g = {
            "TRUE_HUGO_SYMBOL": {"$in": ["BMPR1A"]},
            "VARIANT_CATEGORY": {"$in": ["CNV"]},
            "CNV_CALL": {"$in": ["Homozygous deletion"]},
            "WILDTYPE": False,
        }
        s_g = {
            "TRUE_HUGO_SYMBOL": {"$in": ["TRAJ34", "BMPR1A"]},
            "VARIANT_CATEGORY": {"$in": ["SV"]},
            "WILDTYPE": False,
        }
        g = {
            "TRUE_HUGO_SYMBOL": {"$in": ["BMPR1A", "TRAJ34"]},
            "VARIANT_CATEGORY": {"$in": ["MUTATION", "CNV", "SV"]},
            "CNV_CALL": {"$in": ["Homozygous deletion"]},
            "WILDTYPE": False,
        }
        c = {}

        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
            'label': 'test',
            'temporary': False,
            'status': 1
        }

        # run mutation.
        rule['genomic_filter'] = m_g
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)
        m_matches = set([x['CLINICAL_ID'] for x in list(self.db['match'].find({'FILTER_ID': ObjectId(r['_id'])}))])

        # run cnv.
        rule['genomic_filter'] = c_g
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)
        c_matches = set([x['CLINICAL_ID'] for x in list(self.db['match'].find({'FILTER_ID': ObjectId(r['_id'])}))])

        # run sv.
        rule['genomic_filter'] = s_g
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)
        s_matches = set([x['CLINICAL_ID'] for x in list(self.db['match'].find({'FILTER_ID': ObjectId(r['_id'])}))])

        # combine the individual results
        u_matches = set([str(x) for x in m_matches.union(c_matches.union(s_matches))])

        # run combined.
        rule['genomic_filter'] = g
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)
        matches = set([str(x['CLINICAL_ID']) for x in list(self.db['match'].find({'FILTER_ID': ObjectId(r['_id'])}))])

        # make sure we get all.
        assert u_matches == matches

    def test_post_sv(self):
        return              # disabled by james on 9/6/16 to be replaced by proper unit test not
        # relying on pre-populated data.
        # insert the fake sv.
        svs = add_simulated_sv()
        tmp = self.user_token
        self.user_token = self.service_token
        self.post('genomic', svs)
        self.user_token = tmp

        # make rules.
        gene = 'FANCF'
        s_g = {
            "TRUE_HUGO_SYMBOL": {"$in": [gene]},
            "VARIANT_CATEGORY": {"$in": ["SV"]},
            "WILDTYPE": False,
        }
        c = {}

        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
            'label': 'test sv make these sqiglies go away',
            'temporary': False,
            'status': 1
        }

        # run mutation.
        rule['genomic_filter'] = s_g
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)
        assert r["num_matches"] > 0

        # check alias in this.
        matches = list(self.db['match'].find({'FILTER_ID': ObjectId(r['_id'])}))
        for match in matches:

            # get all variants.
            comments = list()
            for variant in match['VARIANTS']:
                tmp = self.db['genomic'].find_one({"_id": variant})
                comments.append(tmp['STRUCTURAL_VARIANT_COMMENT'])

            # certify comments are in synonmys
            syns = set(synonyms[gene])
            syns.add(gene)
            for c in comments:
                hit = False
                for s in syns:
                    if c.count(s) > 0:
                        hit = True
                assert hit

    def test_post_description(self):

        # set time constraints.
        start = time.time()

        # make a filter.
        c = {
            "GENDER": "Male"
        }
        g = {
            "TRUE_HUGO_SYMBOL": "ERCC2",
            'VARIANT_CATEGORY': 'MUTATION'
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
        rule['genomic_filter']['TRUE_HUGO_SYMBOL'] = {"$in": ["ERCC2", "EGFR3"]}
        rule['genomic_filter']['VARIANT_CATEGORY'] = {"$in": ["MUTATION", "SV"]}
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        filter_doc = self.db['filter'].find_one({"_id": ObjectId(r['_id'])})
        assert filter_doc['description'] == "ERCC2, EGFR3: Mutation, Structural rearrangement, Gender: Male"

        # most complex filter.
        rule['clinical_filter']['ONCOTREE_PRIMARY_DIAGNOSIS_NAME'] = "_LIQUID_"
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        filter_doc = self.db['filter'].find_one({"_id": ObjectId(r['_id'])})
        assert filter_doc['description'] == "ERCC2, EGFR3: Mutation, Structural rearrangement in Liquid cancers, Gender: Male"

        rule['clinical_filter']['ONCOTREE_PRIMARY_DIAGNOSIS_NAME'] = "Adrenocortical Adenoma"
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        filter_doc = self.db['filter'].find_one({"_id": ObjectId(r['_id'])})
        assert filter_doc['description'] == "ERCC2, EGFR3: Mutation, Structural rearrangement in Adrenocortical Adenoma, Gender: Male"

        # EXON specified.
        rule['genomic_filter']['TRUE_HUGO_SYMBOL'] = "ERCC2"
        rule['genomic_filter']['TRUE_EXON_CHANGE'] = 10
        rule['genomic_filter']['VARIANT_CATEGORY'] = "MUTATION"
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        filter_doc = self.db['filter'].find_one({"_id": ObjectId(r['_id'])})
        assert filter_doc['description'] == "ERCC2 exon 10 in Adrenocortical Adenoma, Gender: Male"

        # protein specified.
        del rule['genomic_filter']['TRUE_EXON_CHANGE']
        rule['genomic_filter']['TRUE_PROTEIN_CHANGE'] = "V600E"
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        filter_doc = self.db['filter'].find_one({"_id": ObjectId(r['_id'])})
        assert filter_doc['description'] == "ERCC2 V600E in Adrenocortical Adenoma, Gender: Male"

        # age specified.
        dt = formatdate(time.mktime(datetime.datetime(year=1995, month=5, day=4).timetuple()), localtime=False, usegmt=True)
        rule['clinical_filter']['BIRTH_DATE'] = {"$gte": dt}
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        filter_doc = self.db['filter'].find_one({"_id": ObjectId(r['_id'])})
        assert filter_doc['description'] == "ERCC2 V600E in Adrenocortical Adenoma, Gender: Male, Age < 24"
