from bson.objectid import ObjectId

from tests.test_matchminer import TestMinimal
from matchminer.event_hooks.user import email_user
from matchminer import settings


class TestEmail(TestMinimal):
    email = {
        '_id': ObjectId(),
        'email_from': 'FROM@gmail.com',
        'email_to': 'TO@gmail.com',
        'cc': ['CC@gmail.com'],
        'subject': 'Test Email',
        'body': 'Hello World'
    }

    def setUp(self, settings_file=None, url_converters=None):
        super(TestEmail, self).setUp(settings_file=None, url_converters=None)
        self.user_token = self.service_token
        self.db['email'].insert_one(self.email)

    def tearDown(self):
        self.db['email'].remove({'subject': 'Test Email'})

    def test_post_email(self):
        del self.email['_id']
        r, status_code = self.post('email', self.email)
        self.assert201(status_code)

    def test_get_email(self):
        r, status_code = self.get('email')
        self.assert200(status_code)

    def test_get_email_item(self):
        r, status_code = self.get('email/%s' % self.db['email'].find_one({'subject': 'Test Email'})['_id'])
        self.assert200(status_code)

    def test_inserted_user_email(self):
        self.db['email'].drop()

        keep = settings.WELCOME_EMAIL
        settings.WELCOME_EMAIL = "YES"

        email_user(
            [{
                "_id": ObjectId(),
                "first_name": 'John',
                "last_name": 'Doe',
                "title": "M.D. PhD",
                "email": 'noemail@test.test',
                "token": 'abc123',
                "user_name": "jd00",
                'teams': [ObjectId()],
                'roles': ['user']
            }]
        )
        self._check_email()
        settings.WELCOME_EMAIL = keep

    def test_not_approved(self):
        self.db.email.drop()
        email_user([{
            '_id': ObjectId(),
            'first_name': 'John',
            'last_name': 'Doe',
            'title': 'M.D. PhD',
            'email': 'noemail@test.test',
            'token': 'abc123',
            'user_name': '',
            'teams': [ObjectId()],
            'roles': ['cti']
        }])
        emails = list(self.db.email.find())
        assert len(emails) == 0
