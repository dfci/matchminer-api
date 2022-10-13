# import
import json
from bson.objectid import ObjectId

from tests.test_matchminer import TestMinimal


class TestGenomic(TestMinimal):

    def _get_clinical_id(self):

        result = self.db['clinical'].find_one({"SAMPLE_ID": "TCGA-OR-A5JO"})
        return str(result['_id'])
        #return '569712f88a68182695c075c0'

    def test_get_genomic(self):

        # ensure we can retrieve clinical
        r, status_code = self.get('genomic?max_results=20')
        self.assert200(status_code)

        # ensure we have only 20.
        assert len(r['_items']) == 20


    def test_get_genomic_bytypes(self):

        # set the clinical id.
        clinical_id = self._get_clinical_id()

        # execute mutation query.
        qstr = "genomic?max_results=1000&where=%s" % json.dumps((
            {
                "CLINICAL_ID": clinical_id,
                "VARIANT_CATEGORY": "MUTATION",
                "WILDTYPE": False
            }))
        r, status_code = self.get(qstr)
        self.assert200(status_code)
        assert len(r['_items']) == 2, len(r['_items'])
        mut_items = r['_items']

        # execute cnv query.
        qstr = "genomic?where=%s&max_results=10000" % json.dumps((
            {
                "CLINICAL_ID": clinical_id,
                "VARIANT_CATEGORY": 'CNV',
                "WILDTYPE": False
            }))
        r, status_code = self.get(qstr)
        self.assert200(status_code)
        assert len(r['_items']) == 43

        # execute sv query.
        qstr = "genomic?where=%s&max_results=10000" % json.dumps((
            {
                "VARIANT_CATEGORY": 'SV',
            }))
        r, status_code = self.get(qstr)
        self.assert200(status_code)
        assert len(r['_items']) > 0

    def test_align_matches_genomic(self):

        clinical_id = ObjectId()
        genomic = [
            {'GENETIC_EVENT': None, 'CYTOBAND': 'DEMO', 'SAMPLE_ID': 'DEMO-01', 'CLINICAL_ID': clinical_id},
            {'GENETIC_EVENT': 'Arm level', 'CYTOBAND': 'DEMO', 'SAMPLE_ID': 'DEMO-02', 'CLINICAL_ID': clinical_id},
            {'GENETIC_EVENT': 'Chromosome level', 'CYTOBAND': 'DEMO', 'SAMPLE_ID': 'DEMO-03', 'CLINICAL_ID': clinical_id},
            {'GENETIC_EVENT': 'Focal event', 'CYTOBAND': 'DEMO', 'SAMPLE_ID': 'DEMO-04', 'CLINICAL_ID': clinical_id}
        ]
        self.db.genomic.insert_many(genomic)

        qstr = 'genomic?max_results=20&where=%s' % json.dumps({'CLINICAL_ID': str(clinical_id)})
        r, status_code = self.get(qstr)
        self.assert200(status_code)

        resp = r['_items']
        assert len(resp) == 4, resp
        for item in resp:
            if item['SAMPLE_ID'] == 'DEMO-01':
                assert item['CYTOBAND'] == 'DEMO', resp
            elif item['SAMPLE_ID'] == 'DEMO-02':
                assert item['CYTOBAND'] == 'DEMO Arm level', resp
            elif item['SAMPLE_ID'] == 'DEMO-03':
                assert item['CYTOBAND'] == 'DEMO Chromosome level', resp
            elif item['SAMPLE_ID'] == 'DEMO-04':
                assert item['CYTOBAND'] == 'DEMO Focal event', resp
            else:
                assert False, resp
