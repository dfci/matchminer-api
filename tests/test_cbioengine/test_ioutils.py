import unittest
import datetime

# from tcm import ioutils

class TestIOUtils(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_clinical_load(self):
        pass
        # load clinical data.
        #clinical_df = ioutils.clinical_load(settings.DATA_CLINICAL_CSV)

        # assert we have values.
        #assert clinical_df.shape[0] > 0

    def test_genomic_load(self):
        pass
        # load clinical data.
        #genomic_df = ioutils.genomic_load(settings.DATA_GENOMIC_CSV)

        # assert we have values.
        #assert genomic_df.shape[0] > 0

    def test_clinical_gen(self):
        pass
        # load clinical data.
        #clinical_df = ioutils.clinical_load(settings.DATA_CLINICAL_CSV)

        # pass to generator.
        #for entry in ioutils.clinical_gen(clinical_df):

            # make sure we have all keys.
        #    assert len(data_model.clinical_schema) == len(entry)

    def test_genomic_gen(self):
        pass
        # load clinical data.
        #genomic_df = ioutils.genomic_load(settings.DATA_GENOMIC_CSV)

        # pass to generator.
        #for entry in ioutils.genomics_gen(genomic_df):

            # make sure we have all keys.
        #    assert len(data_model.genomic_schema) - 1 == len(entry)


if __name__ == '__main__':
    unittest.main()
