from bson import ObjectId

from tests.test_matchminer import TestMinimal


class TestClinical(TestMinimal):

    def setUp(self, settings_file=None, url_converters=None):

        # call parent
        super(TestClinical, self).setUp(settings_file=None, url_converters=None)

        # switch to service account.
        self.user_token = self.service_token

    def _get_clinical_id(self):

        result = self.db['clinical'].find_one({"SAMPLE_ID": "TCGA-OR-A5JO"})
        return str(result['_id'])

    def test_get_clinical(self):

        # ensure we can retrieve clinical
        r, status_code = self.get('clinical')
        self.assert200(status_code)

    def test_get_clinical_embed(self):

        # ensure we can retrieve clinical
        r, status_code = self.get('clinical/%s' % self._get_clinical_id())
        self.assert200(status_code)

        # make sure we have related field.
        assert 'RELATED' in r

        # make sure there is no self relations going on.
        for clinical in r['RELATED']:
            assert clinical['_id'] != r['_id']

        # make sure its populated for hte special case.
        result = self.db['clinical'].find_one({"SAMPLE_ID": "TCGA-PK-A5HC"})

        r, status_code = self.get('clinical/%s' % result['_id'])
        self.assert200(status_code)
        assert 'RELATED' in r
        assert len(r['RELATED']) > 0

    def test_get_withmatch(self):

        # setup genes.
        gene1 = "ZNRF3"
        gene2 = "PMS2"

        # make a filter.
        c = {
            'PANEL_VERSION': 1
        }
        g = {
            'TRUE_HUGO_SYMBOL': gene1,
            'VARIANT_CATEGORY': 'SV'
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'genomic_filter': g,
            'label': 'test',
            'temporary': False,
            'status': 1
        }
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # get the demo patient id.
        tmp = self.db['clinical'].find_one({"SAMPLE_ID": "TCGA-OR-A5JF"})
        clinical_id = str(tmp['_id'])

        # execute clinical query.
        qstr = "clinical/%s" % clinical_id
        r, status_code = self.get(qstr)

        # assert the match is embedded.
        assert 'FILTER' in r
        assert 'temporary' in r['FILTER'][0], r['FILTER']

    def test_get_withenrolled(self):

        # setup genes.
        gene1 = "ZNRF3"
        gene2 = "PMS2"

        # make a filter.
        c = {
            'PANEL_VERSION': 1
        }
        g = {
            'TRUE_HUGO_SYMBOL': gene1,
            'VARIANT_CATEGORY': 'SV'
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'genomic_filter': g,
            'label': 'test',
            'temporary': False,
            'status': 1
        }
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)
        filter_id = str(r['_id'])

        # set all matches to enrolled.
        self.db['match'].update({}, {"$set": {"MATCH_STATUS": 4}})

        # get the demo patient id.
        tmp = self.db['clinical'].find_one({"SAMPLE_ID": "TCGA-OR-A5JF"})
        clinical_id = str(tmp['_id'])

        # execute clinical query.
        qstr = "clinical/%s" % clinical_id
        r, status_code = self.get(qstr)

        # assert the match is embedded.
        assert 'FILTER' in r
        assert 'ENROLLED' in r
        assert len(r['ENROLLED']) == 1
        assert r['ENROLLED'][0] == filter_id

    def test_post_clinical(self):

        # ensure we can post clinical
        r, status_code = self.post('clinical', self.clinical)
        self.assert201(status_code)

        # check automatic fields.
        assert r['FIRST_LAST'] == r['FIRST_NAME'] + " " + r['LAST_NAME']
        assert r['LAST_FIRST'] == r['LAST_NAME'] + " " + r['FIRST_NAME']

    def test_put_clinical(self):

        # ensure we can post clinical
        r, status_code = self.post('clinical', self.clinical)
        self.assert201(status_code)

        # modify it.
        r['FIRST_NAME'] = "pizza"

        # extract etag.
        etag = r['_etag']
        clinical_id = r['_id']

        # sanitize object except for _id.
        for key in r.keys():
            if key[0] == "_" and key != "_id":
                del r[key]

        # put the new filter.
        r, status_code = self.put('clinical/%s' % clinical_id, r, headers=[('If-Match', etag)])
        self.assert200(status_code)

        # check automatic fields.
        assert r['FIRST_LAST'] == r['FIRST_NAME'] + " " + r['LAST_NAME']
        assert r['LAST_FIRST'] == r['LAST_NAME'] + " " + r['FIRST_NAME']

    def test_post_clinical_notunique(self):

        # post clinical first
        r, status_code = self.post('clinical', self.clinical)
        self.assert201(status_code)

        # post clinical second should return 422
        r, status_code = self.post('clinical', self.clinical)
        self.assert422(status_code)

    def test_post_clinical_consent(self):

       # post clinical first
        r, status_code = self.post('clinical', self.clinical)
        self.assert201(status_code)

        # post poorly formatted.
        new_clin = self.clinical.copy()
        new_clin['QUESTION1_YN'] = "N"
        r, status_code = self.post('clinical', new_clin)
        self.assert422(status_code)

    def test_update_clinical_consent(self):

        # need to switch to  service account to patch.
        self.user_token = self.service_token

        # post clinical first
        r, status_code = self.post('clinical', self.clinical)
        self.assert201(status_code)

        # extract etag.
        etag = r['_etag']
        clinical_id = r['_id']

        # sanitize object except for _id.
        for key in r.keys():
            if key[0] == "_" and key != "_id":
                del r[key]
        r['QUESTION1_YN'] = "N"

        # put the new filter.
        r, status_code = self.put('clinical/%s' % clinical_id, r, headers=[('If-Match', etag)])
        self.assert422(status_code)

    def test_delete_clinical(self):

        # post clinical
        r, status_code = self.post('clinical', self.clinical)
        self.assert201(status_code)
        clinical_id = r['_id']
        sample_id = r['SAMPLE_ID']
        etag = r['_etag']

        # fetch genomics we can add.
        genomics = self._get_genomic_records(ObjectId(self._get_clinical_id()))
        for i in range(len(genomics)):

            # mark these.
            genomics[i]['COVERAGE'] = 9123
            genomics[i]['CLINICAL_ID'] = clinical_id
            genomics[i]['SAMPLE_ID'] = sample_id

            # clear this.
            for key in genomics[i].keys():
                if key[0] == '_':
                    del genomics[i][key]

        # insert them.
        r, status_code = self.post('genomic', genomics)
        self.assert201(status_code)

        # create a filter.
        c = {
            "GENDER" : "Male",
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
            'label': 'test',
            'temporary': False,
            'status': 1
        }
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # assert we have genomics and match entries.
        results = self._get_genomic_records(ObjectId(clinical_id))
        assert len(results) > 0


        '''
        results = self._get_match_records(ObjectId(clinical_id))
        print results
        assert len(results) > 0
        '''

        # delete the posted clinical.
        r, status_code = self.delete('clinical/%s' % clinical_id, headers=[("If-Match", etag)])
        self.assert204(status_code)

        # ensure the genomic records are also deleted.
        results = self._get_genomic_records(ObjectId(clinical_id))
        assert len(results) == 0

        # ensure associated matches are equal to zero.
        results = self._get_match_records(ObjectId(clinical_id))
        assert len(results) == 0

    def test_vital_status_patch(self):

        # clear database, but save entries
        self._savedb()

        # add clinical entry and match entry
        clin = self.clinical.copy()
        del clin['_id']
        clin['VITAL_STATUS'] = 'alive'
        clinical_resp, status_code = self.post("clinical", clin)
        assert status_code == 201

        match = self.match.copy()
        del match['_id']
        del match['FILTER_ID']
        match['CLINICAL_ID'] = str(clinical_resp['_id'])
        match['VARIANTS'] = []
        match_resp, status_code = self.post("match", match)
        assert status_code == 201

        # change mrn
        update = clinical_resp.copy()
        update['MRN'] = 'NEW_MRN'
        for field in ['_updated', '_created', '_status', '_links', '_etag']:
            del update[field]
        clinical_resp, status_code = self.put('clinical/%s' % str(clinical_resp['_id']), update,
                                              headers=[('If-Match', clinical_resp['_etag'])])
        self.assert200(status_code)

        # check that the match was not deleted
        check_match = self.db['match'].find_one({'_id': ObjectId(match_resp['_id'])})
        assert check_match

        # change vital status
        payload = {'VITAL_STATUS': 'deceased'}
        clinical_resp, status_code = self.patch('clinical/%s' % str(clinical_resp['_id']),
                                                payload,
                                                headers=[('If-Match', clinical_resp['_etag'])])
        self.assert200(status_code)

        # check that the match was deleted
        check_match = self.db['match'].find_one({'_id': ObjectId(match_resp['_id'])})
        assert not check_match

        # restore database to original state
        self._restoredb()
