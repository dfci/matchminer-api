import unittest
from datetime import datetime as dt

from matchminer.database import get_db
from matchminer.trial_search import Summary


class TestUtilities(unittest.TestCase):

    def setUp(self):
        self.db = get_db()
        self.db.status.drop()

        self.now = '2017-0{0}-01 05:00:00'

        self.db.status.insert_many([{
            'updated_genomic': 0,
            'new_genomic': 10,
            'updated_clinical': 0,
            'new_clinical': 5,
            'last_update': dt.now(),
            'data_push_id': self.now.format(m)
        } for m in [1, 2, 3, 4, 5, 6]])

    def tearDown(self):
        self.db.status.drop()


    def test_get_dfci_investigator(self):

        # dfci site principal investigator exists
        trial = {
            'principal_investigator': 'Kirk, James, T.',
            'staff_list': {
                'protocol_staff': [
                    {
                        "first_name": "Jean-Luc",
                        "last_name": "Picard",
                        "institution_name": "Dana-Farber Cancer Institute",
                        "staff_role": "Site Principal Investigator",
                        "email_address": "correct email",
                    },
                    {
                        "first_name": "James",
                        "last_name": "Kirk",
                        "institution_name": "Dana-Farber Cancer Institute",
                        "staff_role": "Sub-Investigator",
                        "email_address": "incorrect email",
                    },
                    {
                        "first_name": "Catherine",
                        "last_name": "Janeway",
                        "institution_name": "MGH",
                        "staff_role": "Research Nurse",
                        "email_address": "incorrect email",
                    }
                ]
            }
        }

        summary = Summary(None, None, None, None)
        summary._get_dfci_investigator(trial)
        resp = summary.dfci_investigator
        assert resp['first_name'] == 'Jean-Luc', resp['first_name']
        assert resp['last_name'] == 'Picard', resp['last_name']
        assert resp['first_last'] == 'Jean-Luc Picard', resp['first_last']
        assert resp['last_first'] == 'Picard Jean-Luc', resp['last_first']
        assert resp['institution_name'] == 'Dana-Farber Cancer Institute', resp['institution_name']
        assert resp['staff_role'] == 'DFCI Principal Investigator', resp['staff_role']
        assert resp['email_address'] == 'correct email', resp['email_address']
        assert resp['is_overall_pi'] is False, resp['is_overall_pi']

        # dfci site principal investigator doesn't exist but dfci overall principal investigator does
        trial = {
            'principal_investigator': 'Kirk, James, T.',
            'staff_list': {
                'protocol_staff': [
                    {
                        "first_name": "Jean-Luc",
                        "last_name": "Picard",
                        "institution_name": "Dana-Farber Cancer Institute",
                        "staff_role": "Overall Principal Investigator",
                        "email_address": "correct email",
                    },
                    {
                        "first_name": "James",
                        "last_name": "Kirk",
                        "institution_name": "Dana-Farber Cancer Institute",
                        "staff_role": "Sub-Investigator",
                        "email_address": "incorrect email",
                    },
                    {
                        "first_name": "Catherine",
                        "last_name": "Janeway",
                        "institution_name": "MGH",
                        "staff_role": "Research Nurse",
                        "email_address": "incorrect email",
                    }
                ]
            }
        }

        summary = Summary(None, None, None, None)
        summary._get_dfci_investigator(trial)
        resp = summary.dfci_investigator
        assert resp['first_name'] == 'Jean-Luc', resp['first_name']
        assert resp['last_name'] == 'Picard', resp['last_name']
        assert resp['first_last'] == 'Jean-Luc Picard', resp['first_last']
        assert resp['last_first'] == 'Picard Jean-Luc', resp['last_first']
        assert resp['institution_name'] == 'Dana-Farber Cancer Institute', resp['institution_name']
        assert resp['staff_role'] == 'DFCI Principal Investigator', resp['staff_role']
        assert resp['email_address'] == 'correct email', resp['email_address']
        assert resp['is_overall_pi'] is False, resp['is_overall_pi']

        # no principal investigators exist at DFCI, BWH, or Beth Israel
        trial = {
            'principal_investigator': 'Janeway, Catherine',
            'staff_list': {
                'protocol_staff': [
                    {
                        "first_name": "Jean-Luc",
                        "last_name": "Picard",
                        "institution_name": "Dana-Farber Cancer Institute",
                        "staff_role": "Research Nurse",
                        "email_address": "incorrect email",
                    },
                    {
                        "first_name": "James",
                        "last_name": "Kirk",
                        "institution_name": "Dana-Farber Cancer Institute",
                        "staff_role": "Sub-Investigator",
                        "email_address": "incorrect email",
                    },
                    {
                        "first_name": "Catherine",
                        "last_name": "Janeway",
                        "institution_name": "MGH",
                        "staff_role": "Overall Principal Investigator",
                        "email_address": "correct email",
                    }
                ]
            }
        }

        summary = Summary(None, None, None, None)
        summary._get_dfci_investigator(trial)
        resp = summary.dfci_investigator
        assert resp['first_name'] == 'Catherine', resp['first_name']
        assert resp['last_name'] == 'Janeway', resp['last_name']
        assert resp['first_last'] == 'Catherine Janeway', resp['first_last']
        assert resp['last_first'] == 'Janeway Catherine', resp['last_first']
        assert resp['institution_name'] == 'MGH', resp['institution_name']
        assert resp['staff_role'] is None, resp['staff_role']
        assert resp['email_address'] == 'correct email', resp['email_address']
        assert resp['is_overall_pi'] is True, resp['is_overall_pi']

        # no principal investigators exist at DFCI
        trial = {
            'principal_investigator': 'Janeway, Catherine',
            'staff_list': {
                'protocol_staff': [
                    {
                        "first_name": "Jean-Luc",
                        "last_name": "Picard",
                        "institution_name": "Dana-Farber Cancer Institute",
                        "staff_role": "Research Nurse",
                        "email_address": "incorrect email",
                    },
                    {
                        "first_name": "James",
                        "last_name": "Kirk",
                        "institution_name": "Dana-Farber Cancer Institute",
                        "staff_role": "Sub-Investigator",
                        "email_address": "incorrect email",
                    },
                    {
                        "first_name": "Ed",
                        "last_name": "Mercer",
                        "institution_name": "Beth Israel Deaconess Medical Center",
                        "staff_role": "Overall Principal Investigator",
                        "email_address": "correct email",
                    },
                    {
                        "first_name": "Catherine",
                        "last_name": "Janeway",
                        "institution_name": "MGH",
                        "staff_role": "Overall Principal Investigator",
                        "email_address": "incorrect email",
                    }
                ]
            }
        }

        summary = Summary(None, None, None, None)
        summary._get_dfci_investigator(trial)
        resp = summary.dfci_investigator
        assert resp['first_name'] == 'Ed', resp['first_name']
        assert resp['last_name'] == 'Mercer', resp['last_name']
        assert resp['first_last'] == 'Ed Mercer', resp['first_last']
        assert resp['last_first'] == 'Mercer Ed', resp['last_first']
        assert resp['institution_name'] == 'Beth Israel Deaconess Medical Center', resp['institution_name']
        assert resp['staff_role'] is None, resp['staff_role']
        assert resp['email_address'] == 'correct email', resp['email_address']
        assert resp['is_overall_pi'] is False, resp['is_overall_pi']

        # no principal investigators exist at DFCI
        trial = {
            'principal_investigator': 'Janeway, Catherine',
            'staff_list': {
                'protocol_staff': [
                    {
                        "first_name": "Jean-Luc",
                        "last_name": "Picard",
                        "institution_name": "Dana-Farber Cancer Institute",
                        "staff_role": "Research Nurse",
                        "email_address": "incorrect email",
                    },
                    {
                        "first_name": "James",
                        "last_name": "Kirk",
                        "institution_name": "Dana-Farber Cancer Institute",
                        "staff_role": "Sub-Investigator",
                        "email_address": "incorrect email",
                    },
                    {
                        "first_name": "Ed",
                        "last_name": "Mercer",
                        "institution_name": "Brigham and Women's Hospital",
                        "staff_role": "Overall Principal Investigator",
                        "email_address": "correct email",
                    },
                    {
                        "first_name": "Catherine",
                        "last_name": "Janeway",
                        "institution_name": "MGH",
                        "staff_role": "Overall Principal Investigator",
                        "email_address": "incorrect email",
                    }
                ]
            }
        }

        summary = Summary(None, None, None, None)
        summary._get_dfci_investigator(trial)
        resp = summary.dfci_investigator
        assert resp['first_name'] == 'Ed', resp['first_name']
        assert resp['last_name'] == 'Mercer', resp['last_name']
        assert resp['first_last'] == 'Ed Mercer', resp['first_last']
        assert resp['last_first'] == 'Mercer Ed', resp['last_first']
        assert resp['institution_name'] == 'Brigham and Women\'s Hospital', resp['institution_name']
        assert resp['staff_role'] is None, resp['staff_role']
        assert resp['email_address'] == 'correct email', resp['email_address']
        assert resp['is_overall_pi'] is False, resp['is_overall_pi']


        # no overall principal investigator exists
        trial = {
            'principal_investigator': 'Kirk, James, T.',
            'staff_list': {
                'protocol_staff': [
                    {
                        "first_name": "Jean-Luc",
                        "last_name": "Picard",
                        "institution_name": "Dana-Farber Cancer Institute",
                        "staff_role": "Research Nurse",
                        "email_address": "incorrect email",
                    },
                    {
                        "first_name": "James",
                        "last_name": "Kirk",
                        "institution_name": "Dana-Farber Cancer Institute",
                        "staff_role": "Sub-Investigator",
                        "email_address": "incorrect email",
                    },
                    {
                        "first_name": "Catherine",
                        "last_name": "Janeway",
                        "institution_name": "MGH",
                        "staff_role": "Research Nurse",
                        "email_address": "correct email",
                    }
                ]
            }
        }

        summary = Summary(None, None, None, None)
        summary._get_dfci_investigator(trial)
        resp = summary.dfci_investigator
        assert resp is None, resp

        # no staff list exists
        summary = Summary(None, None, None, None)
        summary._get_dfci_investigator({})
        resp = summary.dfci_investigator
        assert resp is None, resp
