from bson import ObjectId

from tests.test_matchminer import TestMinimal


class TestClinical(TestMinimal):

    def setUp(self, settings_file=None, url_converters=None):

        # call parent
        super(TestClinical, self).setUp(settings_file=None, url_converters=None)

        # switch to service account.
        self.user_token = self.service_token


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
        for key in list(r.keys()):
            if key[0] == "_" and key != "_id":
                del r[key]
        r['QUESTION1_YN'] = "N"

        # put the new filter.
        r, status_code = self.put('clinical/%s' % clinical_id, r, headers=[('If-Match', etag)])
        self.assert422(status_code)

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
        match['clinical_id'] = str(clinical_resp['_id'])
        match['hash'] = "sometesthash"
        match['is_disabled'] = False
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
        assert check_match['is_disabled'] == True

        # restore database to original state
        self._restoredb()
