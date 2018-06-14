import unittest
import datetime

from tcm import CBioEngine
from matchminer import settings
from matchminer import data_model

class TestEngine(unittest.TestCase):

    def setUp(self):

        # get the engine.
        self.cbio = CBioEngine(settings.MONGO_URI, settings.MONGO_DBNAME, data_model.match_schema, muser=settings.MONGO_USERNAME, mpass=settings.MONGO_PASSWORD,
                 collection_clinical=settings.COLLECTION_CLINICAL, collection_genomic=settings.COLLECTION_GENOMIC)


    def test_match_iter(self):

        # perform match.
        dt = datetime.datetime(year=1996, month=1, day=1)
        c = {
            "$and": [
                {"BIRTH_DATE": {"$gte": dt}},
                {"GENDER": "Male"},
            ]
        }
        g = {
            'ALLELE_FRACTION': {"$gte": 0.75}
        }
        self.cbio.match(c=c, g=g)

        # iterate over resuilts.
        for match in self.cbio.match_iter():
            assert match is not None

    def test_match_and(self):

        # build age range criteria
        dt = datetime.datetime(year=1990, month=1, day=1)
        c = {
            "$and": [
                {"BIRTH_DATE": {"$gte": dt}},
                {"GENDER": "Male"},
            ]
        }
        self.cbio.match(c=c)

        # assert hits
        assert self.cbio.match_df.shape[0] > 0

    def test_match_empty(self):

        # build age range criteria
        dt = datetime.datetime(year=2020, month=1, day=1)
        c = {
            "BIRTH_DATE": {"$gte": dt}
        }
        matches = self.cbio.match(c=c)

        # assert we have no matches.
        assert matches is None

    def test_match_all(self):

        # disable because intersection needs to take vital_status into account.
        return

        # perform match.
        self.cbio.match()

        # ensure we do get the actual intersection.
        all_ids = set(list(self.cbio.clinical_df._id))

        # the intersection should be the number of genomic records.
        assert self.cbio.match_df.shape[0] == self.cbio.genomic_df.shape[0]

    def test_match_range(self):

        # build age range criteria
        dt = datetime.datetime(year=2000, month=1, day=1)
        c = {
            "BIRTH_DATE": {"$gte": dt}
        }
        self.cbio.match(c=c)

        # count numbers via mongo.
        results = list(self.cbio._c.find({"BIRTH_DATE": {"$gte": dt}}))

        # assert same size.
        assert len(results) == self.cbio.clinical_df.shape[0]

        # build tumor percentage.
        c = {
            "TUMOR_PURITY_PERCENT": {"$gte": 0.75}
        }
        self.cbio.match(c=c)

        # count numbers via mongo.
        results = list(self.cbio._c.find(c))

        # assert same size.
        assert len(results) == self.cbio.clinical_df.shape[0]

    def test_match_both(self):

        # build criteria.
        c = {
            "GENDER": "Male"
        }
        g = {
            "TRUE_HUGO_SYMBOL": "BRCA2"
        }
        results = self.cbio.match(c=c, g=g)

        # count numbers via mongo.
        clin_hits = list(self.cbio._c.find({"GENDER": "Male", "VITAL_STATUS": "alive"}))

        # extract sample ids.
        sample_ids = []
        for hit in clin_hits:
            sample_ids.append(hit['_id'])

        # get variants with these hits.
        var_hits = list(self.cbio._g.find({
            "CLINICAL_ID": {"$in": sample_ids},
            "TRUE_HUGO_SYMBOL": "BRCA2"}))

        # make sure we have the same amount.
        assert len(var_hits) == results.shape[0]

    def test_match_sex(self):
        return
        # build criteria.
        c = {
            "GENDER": "Male"
        }
        results = self.cbio.match(c=c)

        # count numbers via mongo.
        clin_hits = list(self.cbio._c.find({"GENDER": "Male"}))

        # extract sample ids.
        sample_ids = []
        for hit in clin_hits:
            sample_ids.append(hit['_id'])

        # get variants with these hits.
        var_hits = list(self.cbio._g.find({"CLINICAL_ID": {"$in":sample_ids}}))

        # make sure we have the same amount.
        assert len(var_hits) == results.shape[0]

    def test_fields_set(self):

        # build criteria.
        c = {
            "GENDER": "Male"
        }
        results = self.cbio.match(c=c, g_fields={"TRUE_HUGO_SYMBOL": 1})

        # assert we have fields in match_df.
        assert 'TRUE_HUGO_SYMBOL' in set(self.cbio.match_df.columns)

        # try clinical
        results = self.cbio.match(c=c, c_fields={"SAMPLE_ID": 1})
        assert 'SAMPLE_ID' in set(self.cbio.match_df.columns)

if __name__ == '__main__':
    unittest.main()
