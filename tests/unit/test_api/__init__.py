from bson.objectid import ObjectId

demo_resps = [
    {"_id": ObjectId("57e5680821dc022b0f90b485"), "notification_id": ObjectId("57e5680821dc022b0f90b484"),
     "status": "yes", "clinical_trial_id": "", "match_id": ObjectId("57e5680821dc022b0f90b483"),
     "match_status": "Eligible", "expiry_date": "Wed, 01 Jan 2020 05:00:00 GMT", "allow_update":
         True, "response_text": "Thank you!\n\nYour response has been recorded and submitted to MatchMiner and the "
                                "clinical trial study team. A member of the study team will follow-up with additional"
                                " screening questions.\n\nMRN: XXXXXX (Redacted for Security Purposes)\nClinical "
                                "Trial 13-615\nResponse Recorded: Potentially Eligible, interested in enrolling.",
     "return_url": "test_url/#/response/57e5680821dc022b0f90b485?no_ml=true",
     "response_recorded": "Potentially Eligible, interested in enrolling."},

    {"_id": ObjectId("57e5680821dc022b0f90b486"), "notification_id": ObjectId("57e5680821dc022b0f90b484"),
     "status": "no", "clinical_trial_id": "", "match_id": ObjectId("57e5680821dc022b0f90b483"),
     "match_status": "Not Eligible", "expiry_date": "Wed, 01 Jan 2020 05:00:00 GMT", "allow_update": True,
     "response_text": "Thank you!\n\nYour response has been recorded and submitted to MatchMiner and the clinical trial"
                      " study team.\n\nMRN: XXXXXX (Redacted for Security Purposes)\nClinical Trial 13-615\nRespon"
                      "se Recorded: Not Eligible.",
     "return_url": "test_url/#/response/57e5680821dc022b0f90b486?no_ml=true", "response_recorded": "Not Eligible."},

    {"_id": ObjectId("57e5680821dc022b0f90b487"), "notification_id": ObjectId("57e5680821dc022b0f90b484"),
     "status": "deferred", "clinical_trial_id": "", "match_id": ObjectId("57e5680821dc022b0f90b483"),
     "match_status": "Deferred", "deferred_contact": {"name": "Jane Doe", "email": "janedoe@test.com"},
     "expiry_date": "Wed, 01 Jan 2020 05:00:00 GMT", "allow_update": True,
     "response_text": "Thank you!\n\nYour response has been recorded and submitted to MatchMiner and the clinical trial"
                      " study team. If your patient's status changes in the future, please contact janedoe@test.com for"
                      " future trial enrollment.\n\nMRN: XXXXXX (Redacted for Secur,ity Purposes)\nClinical Trial "
                      "13-615\nResponse Recorded: Eligible, but not at this time.",
     "return_url": "test_url/#/response/57e5680821dc022b0f90b487?no_ml=true",
     "response_recorded": "Eligible, but not at this time."},

    {"_id": ObjectId("57e5680821dc022b0f90b488"), "notification_id": ObjectId("57e5680821dc022b0f90b484"),
     "status": "deceased", "clinical_trial_id": "", "match_id": ObjectId("57e5680821dc022b0f90b483"),
     "match_status": "Deceased", "expiry_date": "Wed, 01 Jan 2020 05:00:00 GMT", "allow_update": True,
     "response_text": "Thank you!\n\nYour response has been recorded and submitted to MatchMiner and the clinical trial"
                      " study team.\n\nMRN: XXXXXX (Redacted for Security Purposes)\nClinical Trial 13-615\nRespon"
                      "se Recorded: Patient is deceased.\n\nNote: You have indicated that this patient is deceased. To "
                      "update this information within EPIC, you must send email to: test@test.com."
                      " Please include the patient name, MRN, date of birth, and date of death in your email.",
     "return_url": "test_url/#/response/57e5680821dc022b0f90b488?no_ml=true",
     "response_recorded": "Patient is deceased."}
]

trial2 = {
    'protocol_no': 'test-trial-2',
    'treatment_list': {
        'step': [
            {
                'match': [
                    {
                        'and': [
                            {
                                'or': [
                                    {
                                        'genomic': {
                                            'hugo_symbol': 'PTEN',
                                            'variant_category': 'Copy Number Variation',
                                            'cnv_call': 'Homozygous Deletion'
                                        }
                                    },
                                    {
                                        'genomic': {
                                            'hugo_symbol': 'BRCA1',
                                            'variant_category': 'Structural Variation'
                                        }
                                    },
                                    {
                                        'genomic': {
                                            'hugo_symbol': 'BRAF',
                                            'wildcard_protein_change': '!V600',
                                            'variant_category': 'Mutation'
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
}

trial = {
    'protocol_no': 'test-trial',
    'treatment_list': {
        'step': [
            {
                'match': [
                    {
                        'and': [
                            {
                                'or': [
                                    {
                                        'genomic': {
                                            'hugo_symbol': 'BRAF',
                                            'protein_change': 'p.V600E',
                                            'variant_category': 'Mutation'
                                        }
                                    },
                                    {
                                        'genomic': {
                                            'hugo_symbol': 'BRAF',
                                            'protein_change': 'p.V600K',
                                            'variant_category': 'Mutation'
                                        }
                                    },
                                    {
                                        'genomic': {
                                            'hugo_symbol': 'EGFR',
                                            'wildtype': True
                                        }
                                    }
                                ]
                            },
                            {
                                'genomic': {
                                    'wildtype': True
                                }
                            },
                            {
                                'genomic': {
                                    'hugo_symbol': 'KRAS'
                                }
                            }
                        ]
                    },
                    {
                        'and': [
                            {
                                'or': [
                                    {
                                        'genomic': {
                                            'hugo_symbol': 'PTEN',
                                            'variant_category': 'Copy Number Variation',
                                            'cnv_call': 'Homozygous Deletion'
                                        }
                                    },
                                    {
                                        'genomic': {
                                            'hugo_symbol': 'BRCA1',
                                            'variant_category': 'Structural Variation'
                                        }
                                    },
                                    {
                                        'genomic': {
                                            'hugo_symbol': 'BRAF',
                                            'wildcard_protein_change': '!V600',
                                            'variant_category': 'Mutation'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'and': [
                            {
                                'or': [
                                    {
                                        'genomic': {
                                            'hugo_symbol': 'BRAF',
                                            'protein_change': 'p.V600E',
                                            'variant_category': '!Mutation'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'and': [
                            {
                                'or': [
                                    {
                                        'genomic': {
                                            'hugo_symbol': "None",
                                            'mmr_status': 'MMR-D'
                                        }
                                    },
                                    {
                                        'genomic': {
                                            'hugo_symbol': "None",
                                            'ms_status': 'MSI-H'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'and': [
                            {
                                'or': [
                                    {
                                        'genomic': {
                                            'hugo_symbol': 'BRAF',
                                            'protein_change': 'p.V600K',
                                            'variant_category': 'Mutation'
                                        }
                                    },
                                    {
                                        'genomic': {
                                            'hugo_symbol': 'EGFR',
                                            'variant_categry': 'Mutation'
                                        }
                                    },
                                    {
                                        'genomic': {
                                            'hugo_symbol': 'PTEN',
                                            'variant_category': 'Copy Number Variation'
                                        }
                                    },
                                    {
                                        'genomic': {
                                            'hugo_symbol': '!KRAS',
                                            'variant_category': 'Mutation'
                                        }
                                    },
                                    {
                                        'genomic': {
                                            'hugo_symbol': 'NRAS',
                                            'variant_category': '!Mutation'
                                        }
                                    },
                                    {
                                        'genomic': {
                                            'hugo_symbol': 'NTRK1',
                                            'wildtype': True
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'and': [
                            {
                                'or': [
                                    {
                                        'clinical': {
                                            'her2_status': 'Negative',
                                            'pr_status': 'Positive',
                                            'er_status': 'Negative'
                                        }
                                    }
                                ]
                            },
                            {
                                'genomic': {
                                    'hugo_symbol': 'EGFR',
                                    'variant_category': 'Mutation'
                                }
                            }
                        ]
                    }
                ]
            },
            {
                'arm': [
                    {
                        'match': [
                            {
                                'genomic': {
                                    'hugo_symbol': 'PIK3CA'
                                }
                            }
                        ]
                    },
                    {
                        'dose_level': [
                            {
                                'match': [
                                    {
                                        'and': [
                                            {
                                                'genomic': {
                                                    'hugo_symbol': 'PTEN'
                                                }
                                            },
                                            {
                                                'clinical': {
                                                    'oncotree_primary_diagnosis': 'Melanoma'
                                                }
                                            },
                                            {
                                                'clinical': {
                                                    'oncotree_primary_diagnosis': '!Melanoma'
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
}

match_tree_example = {
    'or': [
        {
            'clinical': {
                'hugo_symbol': 'test'
            }
        },
        {
            'clinical': {
                'age_numerical': '>=18',
                'oncotree_primary_diagnosis': 'Ocular Melanoma'
            }
        }
    ]
}

match_tree_example2 = {
    'or': [
        {
            'clinical': {
                'age_numerical': '>=18',
                'oncotree_primary_diagnosis': '_SOLID_'
            }
        }
    ]
}

match_tree_example3 = {
    'or': [
        {
            'clinical': {
                'age_numerical': '>=18',
                'oncotree_primary_diagnosis': '_LIQUID_'
            }
        }
    ]
}
