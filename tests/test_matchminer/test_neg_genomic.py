_author__ = 'zachary'
from bson.objectid import ObjectId

from matchminer.database import get_db
from tests.test_matchminer import TestMinimal


class TestNegGenomic(TestMinimal):

    def setUp(self, settings_file=None, url_converters=None):

        # call parent
        super(TestNegGenomic, self).setUp(settings_file=None, url_converters=None)

        # switch to service account.
        self.user_token = self.service_token

        self.db = get_db()
        self.db.negative_genomic.drop()

        self.clinical_id = ObjectId()
        self.db.clinical.insert_one({'_id': self.clinical_id})
        self.item = {
            'clinical_id': str(self.clinical_id),
            'sample_id': 'XXXX',
            'true_hugo_symbol': 'PTEN',
            'true_transcript_exon': 1,
            'true_codon': None,
            'coverage': 100000.,
            'coverage_type': 'PN',
            'panel': 'none',
            'roi_type': 'G'
        }

    def tearDown(self):
        self.db.negative_genomic.drop()
        self.db.clinical.remove({'_id': self.clinical_id})

    def test_neg_genomic(self):

        # POST

        # gene
        r, status_code = self.post('negative_genomic', [self.item])
        self.assert201(status_code)
        assert 'entire_gene' in r and r['entire_gene'] is True, r

        # exon
        self.item['roi_type'] = 'E'
        r, status_code = self.post('negative_genomic', [self.item])
        self.assert201(status_code)
        assert 'show_exon' in r and r['show_exon'] is True, r

        # codon
        self.item['roi_type'] = 'C'
        r, status_code = self.post('negative_genomic', [self.item])
        self.assert201(status_code)
        assert 'show_codon' in r and r['show_codon'] is True, r

        # GET
        r, status_code = self.get('negative_genomic')
        self.assert200(status_code)

