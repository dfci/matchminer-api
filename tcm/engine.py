import logging
import pandas as pd
from eve.io.mongo.validation import Validator
from pymongo import MongoClient

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', )


class CBioEngine(object):

    connection = None
    clinical_df = None
    genomic_df = None
    match_df = None
    living_genomic = 0

    def __init__(self, mongo_uri, mongo_dbname, match_schema, muser=None, mpass=None,
                 collection_clinical="clinical", collection_genomic="genomic"):

        # save these commmon variables.
        self.mongo_uri = mongo_uri
        self.mongo_dbname = mongo_dbname
        self.muser = muser
        self.mpass = mpass
        self.collection_clinical = collection_clinical
        self.collection_genomic = collection_genomic

        # establish database connection.
        self._setup_db()

        # set variables.
        self.match_schema = match_schema

    def match(self, c=None, g=None, c_fields=None, g_fields=None):

        logging.info("matching: num_clinical=%d, num_genomic=%d" % (self._c.count(), self._g.count()))
        self.match_clinical(c=c, c_fields=c_fields)
        self.match_genomic(g=g, g_fields=g_fields)

        if self.clinical_df.shape[0] != 0 and self.genomic_df.shape[0] != 0:

            match_df = pd.merge(self.clinical_df,
                                self.genomic_df,
                                how='inner',
                                left_on=['_id', 'SAMPLE_ID'],
                                right_on=['CLINICAL_ID', 'SAMPLE_ID'])

            match_all_df = match_df.copy()

            alive_query = {"VITAL_STATUS": "alive"}
            alive_patients = list(self._c.find(alive_query))
            alive_ids = [item['SAMPLE_ID'] for item in alive_patients]
            match_df.fillna(value='alive', inplace=True)
            match_df = match_df[match_df['SAMPLE_ID'].isin(alive_ids)]

            self.genomic_df = self.genomic_df[self.genomic_df['SAMPLE_ID'].isin(alive_ids)]
            self.living_genomic = self.genomic_df.shape[0]

        else:

            match_df = None
            match_all_df = None
            alive_ids = self._c.find({}).distinct("SAMPLE_ID")

            if self.genomic_df.shape[0] == 0:
                self.living_genomic = 0
            else:
                self.genomic_df = self.genomic_df[self.genomic_df['SAMPLE_ID'].isin(alive_ids)]
                self.living_genomic = self.genomic_df.shape[0]

        self.match_df = match_df
        self.match_all_df = match_all_df

        return self.match_df

    def match_clinical(self, c=None, c_fields=None):

        # fix empty.
        if c is None:
            c = {}

        # query each table.
        if c_fields is None:
            results = self._c.find(c, {'_id': 1, 'SAMPLE_ID': 1, 'REPORT_DATE': 1, 'VITAL_STATUS': 1})

        else:
            c_fields['SAMPLE_ID'] = 1
            c_fields['VITAL_STATUS'] = 1
            c_fields['_id'] = 1
            results = self._c.find(c, c_fields)

        # convert to dataframe.
        clinical_df = pd.DataFrame(list(results))

        # save as global var.
        self.clinical_df = clinical_df

        # return it.
        return self.clinical_df

    def match_genomic(self, g=None, g_fields=None):

        # fix empty.
        if g is None:
            g = {}

        # query each table.
        if g_fields is None:
            results = self._g.find(g, {'CLINICAL_ID': 1, 'SAMPLE_ID': 1})

        else:
            g_fields['SAMPLE_ID'] = 1
            g_fields['CLINICAL_ID'] = 1
            results = self._g.find(g, g_fields)

        # convert to dataframe.
        genomic_df = pd.DataFrame(list(results))

        # save as global var.
        self.genomic_df = genomic_df

        # return it.
        return self.genomic_df

    def match_iter(self):

        # short circuit on empty
        if self.match_df is None:
            return

        # create validator.
        v = Validator(self.match_schema)

        # names cols.
        cis = zip(range(len(self.match_df.columns)), list(self.match_df.columns))

        # strip out underscore fields.
        tmp = []
        for a, b in cis:
            if b[0] == "_" and b != "_id_y":
                continue
            tmp.append((a,b))
        cis = tmp

        # loop over each entry.
        for row in self.match_df.itertuples():

            # create dictionary.
            tmp = {}
            for i, key in cis:

                # extract value.
                val = row[i+1]

                # convert nan
                if pd.isnull(val):
                    val = None

                # convert special key.
                if key == "_id_y":
                    key = "GENOMIC_ID"

                # save it to dict.
                tmp[key] = val

            # yield the match
            yield tmp

    def _setup_db(self):

        # connect to database.
        self.connection = MongoClient(self.mongo_uri)

        # establish the collection interface.
        self._c = self.connection[self.mongo_dbname][self.collection_clinical]
        self._g = self.connection[self.mongo_dbname][self.collection_genomic]

    def _close_db(self):
        self.connection.close()