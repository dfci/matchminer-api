# import
import os
import pprint
import json
import time
import datetime
from rfc822 import formatdate
from bson import ObjectId

from matchminer import miner
from tests.test_matchminer import TestMinimal


class TestSecurity(TestMinimal):

    def setUp(self, settings_file=None, url_converters=None):

        # call parent
        super(TestSecurity, self).setUp(settings_file=None, url_converters=None)

        # clean the user, team collections.
        self.db['user'].delete_many({})
        self.db['team'].delete_many({})

    def test_admin_role(self):

        # query genomics using bad token expect 401.
        qstr = "?max_results=1"
        r, status_code = self.get('genomic', query=qstr)
        assert status_code == 401

        # add super-user.
        super_token =  "123456"
        super_id = self.db['user'].insert({
            'user_name': "",
            'first_name': "",
            'last_name': "",
            'title': "",
            'email': "",
            'token':super_token,
            'teams': [],
            'roles': ["admin"]
        })
        super_id = ObjectId(super_id)

        # query genomics use super-user, it should return 200.
        self.user_token = super_token
        r, status_code = self.get('genomic', query=qstr)
        assert status_code == 200

        # insert a clinical record using super-user, it should work.
        r = self._insert_clinical()
        assert r['_status'] == 'OK'

    def test_user_role(self):

        # add a dumb user.
        dumb_token =  "abc"
        dumb_id = self.db['user'].insert({
            'user_name': "",
            'first_name': "",
            'last_name': "",
            'title': "",
            'email': "",
            'token': dumb_token,
            'teams': [],
            'roles': ["user"]
        })
        dumb_id = ObjectId(dumb_id)

        # insert a clincial record using dumb-user, it should fail.
        self.user_token = dumb_token
        r = self._insert_clinical(check=False)
        assert r['_status'] == 'ERR'

        # insert a genomic record using dumb-user, it should fail.
        clinical = self.db['clinical'].find_one({})
        r = self._insert_genomic(clinical['_id'], check=False)
        assert r['_status'] == 'ERR'

        # insert a user and it should fail.
        user = {
            'user_name': "TEST",
            'first_name': "TEST",
            'last_name': "TEST",
            'title': "TEST",
            'email': "TEST",
            'teams': [],
            'roles': ["admin"]
        }
        r, status_code = self.post('user', user)
        self.assert401(status_code)

        # insert a status and it should fail.
        cur_dt = formatdate(time.mktime(datetime.datetime.now().timetuple()))
        status = {
            'last_update': cur_dt,
            'new_clinical': 5,
            'updated_clinical': 6,
            'new_genomic': 7,
            'updated_genomic': 8,
            'data_push_id': '2017-01-01 05:00:00'
        }
        r, status_code = self.post('status', status)
        self.assert401(status_code)

        # shant be able to get from hipaa.
        qstr = "?max_results=1"
        r, status_code = self.get('hipaa', query=qstr)
        assert status_code == 401

        # should b able to get from clinical, genomic, match, filter
        qstr = "?max_results=1"
        for res in ['clinical', 'genomic', 'match', 'filter']:
            r, status_code = self.get(res, query=qstr)
            assert status_code == 200

    def test_service_role(self):

        # add a dumb user.
        dumb_token =  "abc"
        dumb_id = self.db['user'].insert({
            'user_name': "",
            'first_name': "",
            'last_name': "",
            'title': "",
            'email': "",
            'token': dumb_token,
            'teams': [],
            'roles': ["service"]
        })
        dumb_id = ObjectId(dumb_id)

        # insert a clincial record using dumb-user, it should fail.
        self.user_token = dumb_token
        r = self._insert_clinical(check=False)
        assert r['_status'] == 'OK'

        # insert a genomic record using dumb-user, it should fail.
        clinical = self.db['clinical'].find_one({})
        r = self._insert_genomic(clinical['_id'], check=False)
        assert r['_status'] == 'OK'

        # insert a user and it should fail.
        user = {
            'user_name': "TEST",
            'first_name': "TEST",
            'last_name': "TEST",
            'title': "TEST",
            'email': "TEST",
            'teams': [],
            'roles': ["admin"]
        }
        r, status_code = self.post('user', user)
        self.assert201(status_code)

        # insert a status and it should pass.
        cur_dt = formatdate(time.mktime(datetime.datetime.now().timetuple()))
        status = {
            'last_update': cur_dt,
            'new_clinical': 5,
            'updated_clinical': 6,
            'new_genomic': 7,
            'updated_genomic': 8,
            'silent': True,
            'data_push_id': '2017-01-01 05:00:00'
        }
        r, status_code = self.post('status', status)
        self.assert201(status_code)

        # shant be able to get from hipaa.
        qstr = "?max_results=1"
        r, status_code = self.get('hipaa', query=qstr)
        assert status_code == 401

        # should b able to get from clinical, genomic, match, filter
        qstr = "?max_results=1"
        for res in ['clinical', 'genomic', 'match', 'filter']:
            r, status_code = self.get(res, query=qstr)
            assert status_code == 200

    def test_user_role(self):

        # add a dumb user.
        dumb_token =  "abc"
        dumb_id = self.db['user'].insert({
            'user_name': "",
            'first_name': "",
            'last_name': "",
            'title': "",
            'email': "",
            'token': dumb_token,
            'teams': [],
            'roles': ["user"]
        })
        dumb_id = ObjectId(dumb_id)

        # insert a clincial record using dumb-user, it should fail.
        self.user_token = dumb_token
        r = self._insert_clinical(check=False)
        assert r['_status'] == 'ERR'

        # insert a genomic record using dumb-user, it should fail.
        clinical = self.db['clinical'].find_one({})
        r = self._insert_genomic(clinical['_id'], check=False)
        assert r['_status'] == 'ERR'

        # insert a user and it should fail.
        user = {
            'user_name': "TEST",
            'first_name': "TEST",
            'last_name': "TEST",
            'title': "TEST",
            'email': "TEST",
            'teams': [],
            'roles': ["admin"]
        }
        r, status_code = self.post('user', user)
        self.assert401(status_code)

        # insert a status and it should fail.
        cur_dt = formatdate(time.mktime(datetime.datetime.now().timetuple()))
        status = {
            'last_update': cur_dt,
            'new_clinical': 5,
            'updated_clinical': 6,
            'new_genomic': 7,
            'updated_genomic': 8,
            'data_push_id': '2017-01-01 05:00:00'
        }
        r, status_code = self.post('status', status)
        self.assert401(status_code)

        # shant be able to get from hipaa.
        qstr = "?max_results=1"
        r, status_code = self.get('hipaa', query=qstr)
        assert status_code == 401

        # should b able to get from clinical, genomic, match, filter
        qstr = "?max_results=1"
        for res in ['clinical', 'genomic', 'match', 'filter']:
            r, status_code = self.get(res, query=qstr)
            assert status_code == 200

    def test_resource_access(self):

        # add two users.
        team1_id = self.db['team'].insert({
            "name": "user1"
        })
        team1_id = ObjectId(team1_id)
        user1_token =  "abc"
        user1_id = self.db['user'].insert({
            'user_name': "",
            'first_name': "",
            'last_name': "",
            'title': "",
            'email': "",
            'token': user1_token,
            'teams': [team1_id],
            'roles': ["user"]
        })
        user1_id = ObjectId(user1_id)

        team2_id = self.db['team'].insert({
            "name": "user2"
        })
        team2_id = ObjectId(team2_id)
        user2_token =  "xyz"
        user2_id = self.db['user'].insert({
            'user_name': "",
            'first_name': "",
            'last_name': "",
            'title': "",
            'email': "",
            'token': user2_token,
            'teams': [team2_id],
            'roles': ["user"]
        })
        user2_id = ObjectId(user1_id)

        # add a filter from user 1.
        g = {
            'TRUE_HUGO_SYMBOL': 'PRPF8',
            'VARIANT_CATEGORY': 'MUTATION',
            'WILDTYPE': False
        }
        rule = {
            'USER_ID': user1_id,
            'TEAM_ID': team1_id,
            'genomic_filter': g,
            'label': 'test',
            'temporary': False,
            'status': 1
        }
        self.user_token = user1_token
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)
        filter1_id = ObjectId(r['_id'])

        # add a filter from user 2.
        g = {
            'TRUE_HUGO_SYMBOL': 'PRPF8',
            'VARIANT_CATEGORY': 'MUTATION',
            'WILDTYPE': False
        }
        rule = {
            'USER_ID': user2_id,
            'TEAM_ID': team2_id,
            'genomic_filter': g,
            'label': 'test',
            'temporary': False,
            'status': 1
        }
        self.user_token = user2_token
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)
        filter2_id = ObjectId(r['_id'])

        # swap back to user1
        self.user_token = user1_token

        # assert we can access said filter item.
        r, status_code = self.get("filter/%s" % filter1_id)
        self.assert200(status_code)

        # # test we can't send a query missing team_id
        # r, status_code = self.get("filter", query="?where=%s" % json.dumps(({"label": "test"})))
        # assert status_code == 406

        # test we can send a query with right team_id
        r, status_code = self.get("filter", query="?where=%s" % json.dumps(({
            "label": "test",
            "TEAM_ID": str(team1_id)
        })))
        self.assert200(status_code)
        assert len(r['_items']) > 0
        for f in r['_items']:

            # assert we only get filters with this team id.
            assert f['TEAM_ID'] == str(team1_id)

        # try the match stuff doesn't work.
        r, status_code = self.get("match", query="?where=%s" % json.dumps(({
            "FILTER_ID": str(filter1_id),
            "TEAM_ID": str(team1_id)
        })))
        self.assert200(status_code)
        assert len(r['_items']) > 0

        # swap to second user.
        self.user_token = user2_token

        # # assert we cannot access filter from other user.
        # r, status_code = self.get("filter/%s" % filter1_id)
        # self.assert404(status_code)

        # # assert the resource query is invalid
        # r, status_code = self.get("filter", query="?where=%s" % json.dumps(({
        #     "label": "test",
        #     "TEAM_ID": str(team1_id)
        # })))
        # self.assert404(status_code)

        # assert we only get correct matches.
        r, status_code = self.get("match", query="?where=%s" % json.dumps(({
            "FILTER_ID": str(filter2_id),
            "TEAM_ID": str(team2_id)
        })))
        assert len(r['_items']) > 0
        for f in r['_items']:

            # assert we only get filters with this team id.
            assert f['TEAM_ID'] == str(team2_id)
