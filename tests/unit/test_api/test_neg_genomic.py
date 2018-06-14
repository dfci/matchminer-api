_author__ = 'zachary'
import unittest
from bson.objectid import ObjectId

from matchminer.database import get_db
from matchminer.events import negative_genomic


class TestNegGenomic(unittest.TestCase):

    def setUp(self):
        self.db = get_db()
        self.db.negative_genomic.drop()

        self.item = {
            'clinical_id': ObjectId(),
            'sample_id': 'XXXX',
            'true_hugo_symbol': 'PTEN',
            'true_transcript_exon': 1,
            'true_codon': None,
            'coverage': 100000.,
            'coverage_type': 'PN',
            'panel': 'None',
            'roi_type': 'G'
        }

    def tearDown(self):
        self.db.negative_genomic.drop()

    def test_neg_genomic_hook(self):

        # gene
        negative_genomic([self.item])
        assert 'entire_gene' in self.item and self.item['entire_gene'] is True

        # codon
        self.item['roi_type'] = 'C'
        negative_genomic([self.item])
        assert 'show_codon' in self.item and self.item['show_codon'] is True

        # exon
        self.item['roi_type'] = 'E'
        negative_genomic([self.item])
        assert 'show_exon' in self.item and self.item['show_exon'] is True
