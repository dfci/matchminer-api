import unittest
import eve
import simplejson as json
from datetime import datetime
from pymongo import MongoClient
from eve import ISSUES
import base64
import datetime
import time
from email.utils import formatdate
from bson import ObjectId
import re
import random
import string
from matchminer.custom import blueprint
from matchminer.bootstrap import bootstrap
from matchminer.validation import ConsentValidatorEve
from matchminer.settings import *
from matchminer.events import register_hooks
from matchminer import security


class ValueStack(object):
    """
    Descriptor to store multiple assignments in an attribute.

    Due to the multiple self.app = assignments in tests, it is difficult to
    keep track by hand of the applications created in order to close their
    database connections. This descriptor helps with it.
    """
    def __init__(self, on_delete):
        """
        :param on_delete: Action to execute when the attribute is deleted
        """
        self.elements = []
        self.on_delete = on_delete

    def __set__(self, obj, val):
        self.elements.append(val)

    def __get__(self, obj, objtype):
        return self.elements[-1] if self.elements else None

    def __delete__(self, obj):
        for item in self.elements:
            self.on_delete(item)
        self.elements = []


def close_pymongo_connection(app):
    """
    Close the pymongo connection in an eve/flask app
    """
    if 'pymongo' not in app.extensions:
        return
    del app.extensions['pymongo']
    del app.media


class TestMinimal(unittest.TestCase):
    """ Start the building of the tests for an application
    based on Eve by subclassing this class and provide proper settings
    using :func:`setUp()`
    """
    app = ValueStack(close_pymongo_connection)
    inserted_clinical = list()
    inserted_genomic = list()

    def setUp(self, settings_file=None, url_converters=None):
        """ Prepare the test fixture

        :param settings_file: the name of the settings file.  Defaults
                              to `eve/tests/test_settings.py`.
        """

        # settings.
        self.this_directory = os.path.dirname(os.path.realpath(__file__))
        if settings_file is None:
            # Load the settings file, using a robust path
            settings_file = os.path.join(self.this_directory,
                                         'test_settings.py')

        # default values.
        self.connection = None
        self.team = {
            "_id": ObjectId("66a52871a8c829842fbe618b"),
            "name": "purple monkey"
        }
        self.team_id = self.team['_id']
        self.user = {
            "_id": ObjectId("5697ecb48a6ba828126f8128"),
            "first_name": 'John',
            "last_name": 'Doe',
            "title": "M.D. PhD",
            "email": 'jdoe@demo',
            "token": 'abc123',
            "user_name": "jd00",
            'teams': [self.team_id],
            'roles': ['user']
        }
        self.service = {
            "first_name": 'SERVICE',
            "last_name": 'SERVICE',
            "title": "",
            "email": 'jdoe@demo',
            "token": 'xyz946',
            "user_name": "SERVICE",
            'teams': [],
            'roles': ['service']
        }
        self.curator = {
            "first_name": 'CURATOR',
            "last_name": 'CURATOR',
            "title": "",
            "email": 'jdoe@demo',
            "token": 'kjdhfg76',
            "user_name": "CURATOR",
            'teams': [],
            'roles': ['curator']
        }
        self.service_token = self.service['token']
        self.user_id = self.user['_id']
        self.user_token = self.user['token']
        self.curator_token = self.curator['token']

        # setup the database.
        self.setupDB()

        # prepare the app
        self.settings_file = settings_file
        self.app = eve.Eve(settings=self.settings_file,
                           url_converters=url_converters,
                           auth=security.TokenAuth,
                           validator=ConsentValidatorEve)

        # create the test client
        self.test_client = self.app.test_client()

        # set domain.
        self.domain = self.app.config['DOMAIN']

        # register hooks
        self.app = register_hooks(self.app)

        # register blueprints.
        self.app.register_blueprint(blueprint)

        # create the database pointer
        self.db = self.connection[self.app.config['MONGO_DBNAME']]

        # initialize the database if necessary.
        self.initDB()

        # clear backup.
        # shutil.rmtree(BACKUP_DIR)
        # os.makedirs(BACKUP_DIR)

    def tearDown(self):
        del self.app
        self.dropDB()

    def _insert_match_small(self):

        # make a complex query.
        dt = formatdate(time.mktime(datetime.datetime(year=1995, month=1, day=1).timetuple()), localtime=False, usegmt=True)
        c = {
            "BIRTH_DATE": {"^gte": dt},
        }
        g = {
            "TRUE_HUGO_SYMBOL": "BRCA2"
        }
        rule = {
            'USER_ID': self.user_id,
            'TEAM_ID': self.team_id,
            'clinical_filter': c,
            'genomic_filter': g,
            'label': 'test',
            'status': 1,
            'temporary': False,
        }

        # insert it.
        r, status_code = self.post('filter', rule)
        self.assert201(status_code)

        # return the id.
        return r['_id']

    def _insert_filter(self):

        # create a filter.
        g = {
            'TRUE_HUGO_SYMBOL': 'PRPF8',
            'VARIANT_CATEGORY': 'MUTATION',
            'WILDTYPE': False
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

        # return the id.
        return r['_id']


    def _get_genomic_records(self, clinical_id):

        # get all results.
        return list(self.db['genomic'].find({'CLINICAL_ID': clinical_id}))

    def _get_match_records(self, clinical_id):

        # get all results.
        return list(self.db['match'].find({'CLINICAL_ID': clinical_id}))


    def assert200(self, status):
        self.assertEqual(status, 200)

    def assert201(self, status):
        self.assertEqual(status, 201)

    def assert204(self, status):
        self.assertEqual(status, 204)

    def assert301(self, status):
        self.assertEqual(status, 301)

    def assert304(self, status):
        self.assertEqual(status, 304)

    def assert404(self, status):
        self.assertEqual(status, 404)

    def assert422(self, status):
        self.assertEqual(status, 422)

    def assert405(self, status):
        self.assertEqual(status, 405)

    def _make_headers(self, headers=[]):

        # add the defaults
        headers.append(('Content-Type', 'application/json'))
        headers.append(('Authorization', 'Basic ' + base64.b64encode(f'{self.user_token}:'.encode('utf-8')).decode('utf-8')))

        # just return list.
        return headers

    def get(self, resource, query='', item=None):

        # make headers.
        headers = self._make_headers()

        if resource in self.domain:
            resource = self.domain[resource]['url']
        if item:
            request = '/%s/%s%s' % (resource, item, query)
        else:
            request = '/%s%s' % (resource, query)

        r = self.test_client.get('api' + request, headers=headers)
        return self.parse_response(r)

    def post(self, url, data, headers=None, content_type='application/json'):

        # clear object ids.
        for key in data:
            try:
                if isinstance(data[key], ObjectId):
                    data[key] = str(data[key])
            except TypeError:
                continue

        # make headers.
        if headers is None:
            headers = self._make_headers()
        else:
            headers = self._make_headers(headers=headers)

        r = self.test_client.post('api/' + url, data=json.dumps(data), headers=headers)
        return self.parse_response(r)

    def put(self, url, data, headers=None):
        # make headers.
        if headers is None:
            headers = self._make_headers()
        else:
            headers = self._make_headers(headers=headers)

        r = self.test_client.put('api/' + url, data=json.dumps(data), headers=headers)
        return self.parse_response(r)

    def patch(self, url, data, headers=None):
        # make headers.
        if headers is None:
            headers = self._make_headers()
        else:
            headers = self._make_headers(headers=headers)

        r = self.test_client.patch('api/' + url, data=json.dumps(data), headers=headers)
        return self.parse_response(r)

    def delete(self, url, headers=None):

        # make headers.
        if headers is None:
            headers = self._make_headers()
        else:
            headers = self._make_headers(headers=headers)

        r = self.test_client.delete('api/' + url, headers=headers)
        return self.parse_response(r)

    def parse_response(self, r):
        try:
            v = json.loads(r.get_data())
        except ValueError:
            v = None
        return v, r.status_code

    def assertValidationErrorStatus(self, status):
        self.assertEqual(status,
                         self.app.config.get('VALIDATION_ERROR_STATUS'))

    def assertValidationError(self, response, matches):
        self.assertTrue(eve.STATUS in response)
        self.assertTrue(eve.STATUS_ERR in response[eve.STATUS])
        self.assertTrue(ISSUES in response)
        issues = response[ISSUES]
        self.assertTrue(len(issues))

        for k, v in list(matches.items()):
            self.assertTrue(k in issues)
            self.assertTrue(v in issues[k])

    def assertExpires(self, resource):
        r = self.test_client.get(resource)

        expires = r.headers.get('Expires')
        self.assertTrue(expires is not None)

    def assertCacheControl(self, resource):
        r = self.test_client.get(resource)

        cache_control = r.headers.get('Cache-Control')
        self.assertTrue(cache_control is not None)
        self.assertEqual(cache_control,
                         self.domain[self.known_resource]['cache_control'])

    def assertIfModifiedSince(self, resource):
        r = self.test_client.get(resource)

        last_modified = r.headers.get('Last-Modified')
        self.assertTrue(last_modified is not None)
        r = self.test_client.get(resource, headers=[('If-Modified-Since',
                                                    last_modified)])
        self.assert304(r.status_code)
        self.assertTrue(not r.get_data())

    def assertItem(self, item, resource):
        self.assertEqual(type(item), dict)

        updated_on = item.get(self.app.config['LAST_UPDATED'])
        self.assertTrue(updated_on is not None)
        try:
            datetime.strptime(updated_on, self.app.config['DATE_FORMAT'])
        except Exception as e:
            self.fail('Cannot convert field "%s" to datetime: %s' %
                      (self.app.config['LAST_UPDATED'], e))

        created_on = item.get(self.app.config['DATE_CREATED'])
        self.assertTrue(updated_on is not None)
        try:
            datetime.strptime(created_on, self.app.config['DATE_FORMAT'])
        except Exception as e:
            self.fail('Cannot convert field "%s" to datetime: %s' %
                      (self.app.config['DATE_CREATED'], e))

        link = item.get('_links')
        _id = item.get(self.domain[resource]['id_field'])
        self.assertItemLink(link, _id)

    def assertPagination(self, response, page, total, max_results):
        p_key, mr_key = self.app.config['QUERY_PAGE'], \
            self.app.config['QUERY_MAX_RESULTS']
        self.assertTrue(self.app.config['META'] in response)
        meta = response.get(self.app.config['META'])
        self.assertTrue(p_key in meta)
        self.assertTrue(mr_key in meta)
        self.assertTrue('total' in meta)
        self.assertEqual(meta[p_key], page)
        self.assertEqual(meta[mr_key], max_results)
        self.assertEqual(meta['total'], total)

    def assertHomeLink(self, links):
        self.assertTrue('parent' in links)
        link = links['parent']
        self.assertTrue('title' in link)
        self.assertTrue('href' in link)
        self.assertEqual('home', link['title'])
        self.assertEqual("/", link['href'])

    def assertResourceLink(self, links, resource):
        self.assertTrue('self' in links)
        link = links['self']
        self.assertTrue('title' in link)
        self.assertTrue('href' in link)
        url = self.domain[resource]['url']
        self.assertEqual(url, link['title'])
        self.assertEqual("%s" % url, link['href'])

    def assertCollectionLink(self, links, resource):
        self.assertTrue('collection' in links)
        link = links['collection']
        self.assertTrue('title' in link)
        self.assertTrue('href' in link)
        url = self.domain[resource]['url']
        self.assertEqual(url, link['title'])
        self.assertEqual("%s" % url, link['href'])

    def assertNextLink(self, links, page):
        self.assertTrue('next' in links)
        link = links['next']
        self.assertTrue('title' in link)
        self.assertTrue('href' in link)
        self.assertEqual('next page', link['title'])
        self.assertTrue("%s=%d" % (self.app.config['QUERY_PAGE'], page)
                        in link['href'])

    def assertPrevLink(self, links, page):
        self.assertTrue('prev' in links)
        link = links['prev']
        self.assertTrue('title' in link)
        self.assertTrue('href' in link)
        self.assertEqual('previous page', link['title'])
        if page > 1:
            self.assertTrue("%s=%d" % (self.app.config['QUERY_PAGE'], page)
                            in link['href'])

    def assertItemLink(self, links, item_id):
        self.assertTrue('self' in links)
        link = links['self']
        self.assertTrue('title' in link)
        self.assertTrue('href' in link)
        self.assertTrue('/%s' % item_id in link['href'])

    def assertLastLink(self, links, page):
        if page:
            self.assertTrue('last' in links)
            link = links['last']
            self.assertTrue('title' in link)
            self.assertTrue('href' in link)
            self.assertEqual('last page', link['title'])
            self.assertTrue("%s=%d" % (self.app.config['QUERY_PAGE'], page)
                            in link['href'])
        else:
            self.assertTrue('last' not in links)

    def assert400(self, status):
        self.assertEqual(status, 400)

    def assert401(self, status):
        self.assertEqual(status, 401)

    def assert401or405(self, status):
        self.assertTrue(status == 401 or 405)

    def assert403(self, status):
        self.assertEqual(status, 403)

    def assert405(self, status):
        self.assertEqual(status, 405)

    def assert412(self, status):
        self.assertEqual(status, 412)

    def assert500(self, status):
        self.assertEqual(status, 500)

    def initDB(self):

        # check if the clinical and genomic empty.
        if self.connection[MONGO_DBNAME]['clinical'] == 0 or self.connection[MONGO_DBNAME]['genomic'] == 0:

            # bootstrap.
            bootstrap(self)

        # add testing user.
        user_db = self.db['user']
        team_db = self.db['team']

        team_db.insert_one(self.team)

        # add user and team.
        user_db.insert_one(self.user)

        # add service.
        self.service_id = user_db.insert_one(self.service)
        # add curator
        self.curator_id = user_db.insert_one(self.curator)


    def setupDB(self):

        # drop the database.
        self.dropDB()

        # connect to database.
        self.connection = MongoClient(MONGO_URI)

        # establish connection.
        if MONGO_USERNAME:
            self.connection[MONGO_DBNAME].add_user(MONGO_USERNAME,
                                                   MONGO_PASSWORD)

    def dropDB(self):
        # connect to database.
        self.connection = MongoClient(MONGO_URI)

        # drop all tables except the genomic/clinical
        db = self.connection[MONGO_DBNAME]
        db.drop_collection("user")
        db.drop_collection("team")
        db.drop_collection("filter")
        db.drop_collection("match")
        db.drop_collection("hipaa")
        db.drop_collection("status")
        db.drop_collection("trial")
        db.drop_collection("normalize")
        db.drop_collection("email")
        db.drop_collection("run_log_match")
        db.drop_collection("clinical_run_history_match")
        db.drop_collection("active_processes")

        # clear extra clinical and genomic.
        db['clinical'].delete_many({"TOTAL_READS" : 123, "ORD_PHYSICIAN_NPI": 0000})
        db['genomic'].delete_many({'COVERAGE': 9123})
        db['genomic'].delete_many({"STRUCTURAL_VARIANT_COMMENT": re.compile("tmp6654.*", re.IGNORECASE)})
        for id in self.inserted_clinical:
            db['clinical'].delete_one({'_id': ObjectId(id)})
        for id in self.inserted_genomic:
            db['genomic'].delete_one({'_id': ObjectId(id)})

        # last check.
        db['clinical'].delete_many({"SAMPLE_ID": "TCGA-OR-TEST1"})

        # close connection.
        self.connection.close()

    def _insert_pair(self):

        # insert clinical
        clinical = self._insert_clinical()

        # insert genomic.
        genomic = self._insert_genomic(clinical['_id'])

        # return the pair.
        return clinical, genomic


    def _insert_clinical(self, check=True):
        # make an entry.
        clinical = self.clinical.copy()

        # insert it.
        r, status_code = self.post('clinical', clinical)
        if check:
            self.assert201(status_code)

        # record it.
        if status_code == 201:
            self.inserted_clinical.append(r['_id'])

        # return it
        return r

    def _insert_genomic(self, clinical_id, data=False, check=True):
        if data is False:
            genomic = self.genomic.copy()
        else:
            genomic = data

        # insert it.
        r, status_code = self.post('genomic', genomic)

        if check:
            self.assert201(status_code)

        # record it.
        if status_code == 201:
            self.inserted_genomic.append(r['_id'])

        # return it
        return r

    # Simulated Data
    cur_dt = formatdate(time.mktime(datetime.datetime.now().timetuple()), localtime=False, usegmt=True)
    bir_dt = formatdate(time.mktime(datetime.datetime(year=1995, month=1, day=1).timetuple()), localtime=False, usegmt=True)
    clinical = {
        '_id': ObjectId(),
        "PCT_TARGET_BASE": 0.6764308658975878,
        "LAST_NAME": "Mcginnis[Fake]",
        "TUMOR_PURITY_PERCENT": 0.6273209625954723,
        "ONCOTREE_PRIMARY_DIAGNOSIS": "PHC",
        "ONCOTREE_BIOPSY_SITE": "ADRENAL_GLAND",
        "FIRST_NAME": "Michael",
        "PATIENT_ID": "b3164f7b-c826-4e08-9ee6-8ff96d29b913",
        "DATE_RECEIVED_AT_SEQ_CENTER": cur_dt,
        "SAMPLE_ID": "TCGA-OR-TEST1",
        "ONCOTREE_BIOPSY_SITE_TYPE": "Metastatic",
        "TOTAL_READS": 123,
        "ONCOTREE_PRIMARY_DIAGNOSIS_NAME": "Pheochromocytoma",
        "PANEL_VERSION": 2,
        "ONCOTREE_PRIMARY_DIAGNOSIS_META": "Pheochromocytoma",
        "TOTAL_ALIGNED_READS": 10716821,
        "POWERPATH_PATIENT_ID": "b3164f7b-c826-4e08-9ee6-8ff96d29b913",
        "TEST_TYPE": "11-104 Profile",
        "ORD_PHYSICIAN_NAME": "Maria Bellantoni [fake] M.D.",
        "ONCOTREE_BIOPSY_SITE_META": "Pheochromocytoma",
        "ONCOTREE_BIOPSY_SITE_COLOR": "Purple",
        "MEAN_SAMPLE_COVERAGE": 147,
        "VITAL_STATUS": "deceased",
        "MRN": "b3164f7b-c826-4e08-9ee6-8ff96d29b913",
        "ONCOTREE_BIOPSY_SITE_NAME": "Adrenal Gland",
        "LAST_VISIT_DATE": cur_dt,
        "REPORT_COMMENT": "age_at_initial_pathologic_diagnosis 58 ct_scan nan ct_scan_findings nan days_to_initial_pathologic_diagnosis 0 excess_adrenal_hormone_diagnosis_method_type nan excess_adrenal_hormone_history_type mineralocorticoids excess_adrenal_hormone_history_type-2 nan max nan nf1 nan nf1_clinical_diagnosis nan ret nan sdha nan sdhaf2_sdh5 nan sdhb nan sdhc nan sdhd nan tmem127 nan vhl nan molecular_analysis_performed_indicator no histological_type adrenocortical carcinoma- usual type laterality left lymph_node_examined_count nan metastatic_neoplasm_confirmed_diagnosis_method_name nan metastatic_neoplasm_confirmed_diagnosis_method_name-2 nan metastatic_neoplasm_confirmed_diagnosis_method_text nan distant_metastasis_anatomic_site nan metastatic_neoplasm_initial_diagnosis_anatomic_site nan metastatic_neoplasm_initial_diagnosis_anatomic_site-2 nan metastatic_neoplasm_initial_diagnosis_anatomic_site-3 nan mitoses_count 5 number_of_lymphnodes_positive_by_he nan primary_lymph_node_presentation_assessment nan residual_tumor r0 tumor_tissue_site adrenal atypical_mitotic_figures atypical mitotic figures absent cytoplasm_presence_less_than_equal_25_percent cytoplasm presence <= 25% present diffuse_architecture diffuse architecture present invasion_of_tumor_capsule invasion of tumor capsule absent mitotic_rate mitotic rate > 5/50 hpf absent necrosis necrosis present nuclear_grade_iii_iv nuclear grade iii or iv absent sinusoid_invasion sinusoid invasion absent weiss_venous_invasion venous invasion absent weiss_score 3 year_of_initial_pathologic_diagnosis 2000",
        "ONCOTREE_PRIMARY_DIAGNOSIS_COLOR": "Purple",
        "ORD_PHYSICIAN_NPI": 0000,
        "DISEASE_CENTER_DESCR": "Adrenal Gland oncology",
        "REPORT_DATE": cur_dt,
        "BIRTH_DATE": bir_dt,
        "BIRTH_DATE_INT": 19950105,
        "ALT_MRN": "b3164f7b-c826-4e08-9ee6-8ff96d29b913",
        "REPORT_VERSION": 1,
        "GENDER": "Male",
        "PATHOLOGIST_NAME": "Kacie Smith [fake] M.D.",
        'QUESTION1_YN': "Y",
        'QUESTION3_YN': "Y",
        'CRIS_YN': "Y",
        'QUESTION2_YN': 'Y',
        'BLOCK_NUMBER': '',
        'QUESTION5_YN': 'Y',
        'ORD_PHYSICIAN_EMAIL': '',
        'QUESTION4_YN': '',
        'QC_RESULT': '',
        'data_push_id': '2017-01-01 05:00:00',
        'TEST_NAME': 'oncopanel'
    }

    genomic = {
        '_id': ObjectId(),
        "TRANSCRIPT_SOURCE": "NM_153618.1",
        "BESTEFFECT_TRANSCRIPT_EXON": 7,
        "TRUE_ENTREZ_ID": "80031",
        "TRUE_VARIANT_CLASSIFICATION": "Missense_Mutation",
        "CANONICAL_VARIANT_CLASSIFICATION": "Missense_Mutation",
        "TRUE_STRAND": "+",
        "TRUE_PROTEIN_CHANGE": "p.I160V",
        "VARIANT_CATEGORY": "MUTATION",
        "BESTEFFECT_VARIANT_CLASSIFICATION": "Missense_Mutation",
        "TIER": 4,
        "ALLELE_FRACTION": 0.7977839374344301,
        "CANONICAL_STRAND": "+",
        "BEST": True,
        "CANONICAL_CDNA_TRANSCRIPT_ID": "ENST00000316364.5",
        "ALTERNATE_ALLELE": "A",
        "CHROMOSOME": "15",
        "POSITION": 48053888,
        "WILDTYPE": False,
        "CLINICAL_ID": ObjectId(clinical['_id']),
        "CANONICAL_TRANSCRIPT_EXON": 7,
        "BESTEFFECT_HUGO_SYMBOL": "SEMA6D",
        "REFERENCE_ALLELE": "A",
        "COVERAGE": 0,
        "BESTEFFECT_CDNA_CHANGE": "c.478A>G",
        "TRUE_CDNA_CHANGE": "c.478A>G",
        "TRUE_CDNA_TRANSCRIPT_ID": "ENST00000316364.5",
        "TRUE_HUGO_SYMBOL": "SEMA6D",
        "CANONICAL_CDNA_CHANGE": "c.478A>G",
        "SAMPLE_ID": "TCGA-OR-TEST1",
        "BESTEFFECT_ENTREZ_ID": "80031",
        "SOMATIC_STATUS": "Somatic",
        "BESTEFFECT_CDNA_TRANSCRIPT_ID": "ENST00000316364.5",
        "REFERENCE_GENOME": "37",
        "BESTEFFECT_PROTEIN_CHANGE": "p.I160V",
        "TRUE_TRANSCRIPT_EXON": 7,
        "CANONICAL_PROTEIN_CHANGE": "p.I160V",
        "CANONICAL_ENTREZ_ID": "80031",
        "CANONICAL_HUGO_SYMBOL": "SEMA6D",
        'TEST_NAME': 'oncopanel'
    }

    status = {
        "_id": ObjectId(),
        "updated_genomic": 0,
        "new_genomic": 6063,
        "silent": False,
        "new_clinical": 137,
        "updated_clinical": 17,
        "last_update": datetime.datetime(year=1995, month=1, day=1)
    }

    match = {
        "_id": ObjectId(),
        "MATCH_STATUS": 0,
        "VARIANT_CATEGORY": "MUTATION",
        "CLINICAL_ID": clinical['_id'],
        "TRUE_HUGO_SYMBOL": "BRAF",
        "TEAM_ID": ObjectId(),
        "FILTER_STATUS": 1,
        "FILTER_NAME": "MEK Inhibitor",
        "VARIANTS": [
            ObjectId()
        ],
        "ONCOTREE_PRIMARY_DIAGNOSIS_NAME": "Diffuse Glioma",
        "USER_ID": ObjectId(),
        "MMID": "D47CE1",
        "FILTER_ID": ObjectId(),
        "PATIENT_MRN": "XXXXXX",
        "EMAIL_SUBJECT": "",
        "EMAIL_ADDRESS": "test@test.test",
        "EMAIL_BODY": "",
    }

    trial_status_fields = ['drugs', 'genes', 'tumor_types', 'sponsor', 'coordinating_center',
                           'phase_summary', 'accrual_goal', 'investigator', 'age_summary', 'protocol_number',
                           'disease_status', 'nct_number', 'disease_center']

    def add_remaining_required_fields(self, table):
        """
        Given a clinical database table as a list of dictionaries, this method will iterate through each entry
        and add in the remaining missing required clinical fields from the default self.clinical values
        """

        existing_keys = []
        for item in table:
            existing_keys += list(item.keys())
            existing_keys = list(set(existing_keys))

        required_keys = list(self.clinical.keys())
        for key in required_keys:

            if key == '_id':
                continue

            if key not in existing_keys:
                for item in table:
                    if isinstance(self.clinical[key], ObjectId):
                        item[key] = str(ObjectId())
                    else:
                        item[key] = self.clinical[key]

        return table

    def _check_email(self):
        email = list(self.db['email'].find())
        assert len(email) == 1
        self.db['email'].drop()

    @staticmethod
    def _rand_alphanum(length):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

    dbnames = ['clinical', 'genomic', 'trial', 'normalize', 'filter', 'match']
    def _savedb(self):
        """
        Loads important collections into memory so the database
        can be wiped for the unit test and then restored afterwards
        """

        self.clinicaldb = list(self.db['clinical'].find())
        self.genomicdb = list(self.db['genomic'].find())
        self.trialdb = list(self.db['trial'].find())
        self.normalizedb = list(self.db['normalize'].find())
        self.filterdb = list(self.db['filter'].find())
        self.matchdb = list(self.db['match'].find())

        for dbname in self.dbnames:
            self.db[dbname].drop()

    def _restoredb(self):
        for db, dbname in zip(
            [self.clinicaldb, self.genomicdb, self.trialdb, self.normalizedb, self.filterdb, self.matchdb], self.dbnames
        ):
            if db:
                self.db[dbname].insert_many(db)
