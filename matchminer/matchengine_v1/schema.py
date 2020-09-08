"""Copyright 2016 Dana-Farber Cancer Institute"""

yaml_match_schema = {
    'and': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': 'yaml_match_schema'
        }
    },
    'or': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': 'yaml_match_schema'
        }
    },
    'genomic': {
        'type': 'dict',
        'schema': 'yaml_genomic_schema'
    },
    'clinical': {
        'type': 'dict',
        'schema': 'yaml_clinical_schema'
    }
}

yaml_clinical_schema = {
    'oncotree_primary_diagnosis': {
        'type': 'string',
        'required': False
    },
    'age_numerical': {
        'type': 'string',
    },
    'er_status': {
        'type': 'string',
        'required': False,
        'allowed': ['Positive', 'Negative', 'Unknown']
    },
    'pr_status': {
        'type': 'string',
        'required': False,
        'allowed': ['Positive', 'Negative', 'Unknown']
    },
    'her2_status': {
        'type': 'string',
        'required': False,
        'allowed': ['Positive', 'Negative', 'Unknown']
    },
    "disease_status": {
         "type": "list",
         "required": False,
         'allowed': ['Untreated', 'Localized', 'Locally Advanced', 'Metastatic', 'Advanced', 'Recurrent',
                      'Refractory', 'Unresectable', "Early Stage"]
    },
    'molecular_marker_other': {
         "type": "list",
         "required": False
    },
    'number_prior_lines_therapy_allowed': {
         "type": "string",
         "required": False,
         'allowed': ['Unknown', 'Any', '1', '2', '3', '4', '5', '>=1', '>=2', '>=3', '>=4', '>=5',
                     '<=1', '<=2', '<=3', '<=4', '<=5']
    },
    'active_brain_metastases_allowed': {
         "type": "string",
         "required": False,
         'allowed': ['Yes', 'No']
    },
    'brca1_germline_mutation': {
         "type": "string",
         "required": False,
         'allowed': ['Positive', 'Negative']
    }

}

yaml_genomic_schema = {
    'hugo_symbol': {
        'type': 'string',
        'required': True
    },
    'protein_change': {
        'type': 'string',
    },
    'variant_category': {
        'type': 'string',
        'required': True,
        'allowed': ['Mutation', 'Copy Number Variation', 'Structural Variation', 'Any Variation', 'Signature',
                    '!Mutation', '!Copy Number Variation', '!Structural Variation', '!Signature']
    },
    'wildtype': {
        'type': 'boolean',
        'required': False,
        'allowed': [True, False]
    },
    'cnv_call':{
       'type': 'string',
        'required': False,
    },
    'wildcard_protein_change':{
        'type': 'string',
        'required': False,
    },
    'exon':{
        'type': 'integer',
        'required': False,
    },
    'variant_classification':{
        'type': 'string',
        'required': False,
        'allowed': ['In_Frame_Del', 'In_Frame_Ins', 'Missense_Mutation', 'Nonsense_Mutation', 'Nonstop_Mutation',
                    'Del_Ins', 'Frameshift', 'Frame_Shift_Del', 'Frame_Shift_Ins', 'Frameshift_mutation',
                    'Inframe_Indel', 'Initiator_Codon', 'Intron', 'intron', 'Intron_mutation',
                    'Missense and Splice_Region', 'RNA', 'Silent', 'Splice_Acceptor', 'Splice_Donor', 'Splice_Region',
                    'Splice_Site', 'Splice_Lost', 'Translation_Start_Site', 'coding_sequence', 'intergenic_variant',
                    'protein_altering', 'splice site_mutation', 'stop_retained', 'synonymous', "3'UTR", "3_prime_UTR"
                    "5'Flank", "5'UTR", "5'UTR_mutation", "5_prime_UTR"]
    },
    'fusion_partner_hugo_symbol':{
        'type': 'string',
        'required': False,
    },
    'display_name': {
        'type': 'string',
        'required': False
    },
}

parent_schema = {
    'protocol_no': {
        'type': 'string',
        'required': True
    },
    'protocol_id': {
        'type': 'integer',
        'required': True,
        'unique': True
    },
    'principal_investigator': {
        'type': 'string',
        'required': True
    },
    'principal_investigator_institution': {
        'type': 'string',
        'required': False
    },
    'primary_study_contact_email': {
        'type': 'string',
        'required': False
    },
    'primary_study_contact': {
        'type': 'string',
        'required': False
    },
    'nct_link': {
        'type': 'string',
        'required': False
    },
    'lead_study_coordinator': {
        'type': 'string',
        'required': False
    },
    'management_group_primary': {
        'type': 'string',
        'required': False
    },
    'coordinating_center': {
        'type': 'string',
        'required': False
    },
    'nct_purpose': {
        'type': 'string',
        'required': False
    },
    'lead_study_coordinator_email': {
        'type': 'string',
        'required': False
    },
    'short_title': {
        'type': 'string',
        'required': True
    },
    'long_title': {
        'type': 'string',
        'required': True
    },
    'nct_id': {
        'type': 'string',
        'required': True
    },
    'age': {
        'type': 'string',
        'required': True
    },
    'phase': {
        'type': 'string',
        'required': True
    },
    'data_table4': {
        'type': 'string',
        'required': True
    },
    'protocol_type': {
        'type': 'string',
        'required': True
    },
    'protocol_target_accrual': {
        'type': 'integer',
        'required': True
    },
    'cancer_center_accrual_goal_upper': {
        'type': 'integer',
        'required': True
    },
    'program_area_list': {
        'type': 'dict',
        'required': True,
        'schema': {
            'program_area': {
                'type': 'list',
                'required': True,
                'schema': {
                    "type": "dict",
                    'schema': {
                        'program_area_name': {
                        'type': 'string',
                        'required': True
                        },
                        'is_primary': {
                            'type': 'string',
                            'required': False,
                            'allowed' : ['Y', 'N']
                        }
                    }
                }
            }
        }
    },
    'site_list': {
        'type': 'dict',
        'required': True,
        'schema': {
            'site': {
                'type': 'list',
                'required': True,
                'schema': {
                    "type": "dict",
                    "schema": {
                        "site_name": {
                            "type": "string",
                            "required": True
                        },
                        "site_status": {
                            "type": "string",
                            "required": True
                        },
                        "uses_cancer_center_irb": {
                            "type": "string",
                            "required": True
                        },
                        "coordinating_center": {
                            "type": "string",
                            "required": True
                        }
                    }
                }
            }
        }
    },
    'management_group_list': {
        'type': 'dict',
        'required': True,
        'schema': {
            'management_group': {
                'type': 'list',
                'required': True,
                'schema': {
                    "type": "dict",
                    "schema": {
                        "management_group_name": {
                            "type": "string",
                            "required": True
                        },
                        "is_primary": {
                            "type": "string",
                            "required": True,
                            'allowed': ['Y', 'N']
                        }
                    }
                }
            }
        }
    },
    'treatment_list': {
        'type': 'dict',
        'required': True,
        'normalized': 'trial',
        'schema': {
            'step': {
                'type': 'list',
                'required': True,
                'schema': {
                    "type": "dict",
                    "schema": {
                        'match': {
                            'type': 'list',
                            'schema': {},
                            'allow_unknown': True,
                            'match': True
                        },
                        "step_internal_id": {
                            "type": "integer",
                            "required": True
                        },
                        "step_code": {
                            "type": "string",
                            "required": True
                        },
                        "step_type": {
                            "type": "string",
                            "required": True
                        },
                        "arm": {
                            "type": "list",
                            "required": False,
                            "schema": {
                                "type": "dict",
                                "schema": {
                                    'match': {
                                        'type': 'list',
                                        'schema': {},
                                        'allow_unknown': True,
                                        'match': True
                                    },
                                    "arm_internal_id": {
                                        "type": "integer",
                                        "required": True
                                    },
                                    "arm_code": {
                                        "type": "string",
                                        "required": True
                                    },
                                    "arm_description": {
                                        "type": "string",
                                        "required": True
                                    },
                                    "arm_suspended": {
                                        "type": "string",
                                        "required": True
                                    },
                                    "dose_level": {
                                        "type": "list",
                                        "required": False,
                                        "schema": {
                                            "type": "dict",
                                            "schema": {
                                                'match': {
                                                    'type': 'list',
                                                    'schema': {},
                                                    'allow_unknown': True,
                                                    'match': True
                                                },
                                                "level_internal_id": {
                                                    "type": "integer",
                                                    "required": True
                                                },
                                                "level_code": {
                                                    "type": "string",
                                                    "required": True
                                                },
                                                "level_description": {
                                                    "type": "string",
                                                    "required": True
                                                },
                                                "level_suspended": {
                                                    "type": "string",
                                                    "required": True
                                                },
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    'drug_list': {
        'type': 'dict',
        'required': False,
        'schema': {
            'drug': {
                'type': 'list',
                'required': False,
                'schema': {
                    "type": "dict",
                    "schema": {
                        "drug_name": {
                            "type": "string",
                            "required": False
                        }
                    }
                }
            }
        }
    },
    'oncology_group_list': {
        'type': 'dict',
        'required': True,
        'schema': {
            'oncology_group': {
                'type': 'list',
                'required': True,
                'schema': {
                    "type": "dict",
                    "schema": {
                        "group_name": {
                            "type": "string",
                            "required": True
                        },
                        "is_primary": {
                            "type": "string",
                            "required": True
                        }
                    }
                }
            }
        }
    },
    'disease_site_list': {
        'type': 'dict',
        'required': False,
        'schema': {
            'disease_site': {
                'type': 'list',
                'required': True,
                'schema': {
                    "type": "dict",
                    "schema": {
                        "disease_site_name": {
                            "type": "string",
                            "required": True
                        },
                        "disease_site_code": {
                            "type": "string",
                            "required": True
                        }
                    }
                }
            }
        }
    },
    'staff_list': {
        'type': 'dict',
        'required': True,
        'schema': {
            'protocol_staff': {
                'type': 'list',
                'required': True,
                'schema': {
                    "type": "dict",
                    "schema": {
                        "first_name": {
                            "type": "string",
                            "required": True
                        },
                        "last_name": {
                            "type": "string",
                            "required": True
                        },
                        "middle_name": {
                            "type": "string",
                            "required": True
                        },
                        "npi": {
                            "type": "string",
                            "required": True
                        },
                        "institution_name": {
                            "type": "string",
                            "required": True
                        },
                        "staff_role": {
                            "type": "string",
                            "required": True
                        },
                        "start_date": {
                            "type": "integer",
                            "required": True,
                            "nullable": True
                        },
                        "stop_date": {
                            "type": "integer",
                            "required": True,
                            "nullable": True
                        },
                        "phone_no": {
                            "type": "string",
                            "required": False,
                            "nullable": True
                        },
                        "email_address": {
                            "type": "string",
                            "required": False,
                            "nullable": True
                        },
                    }
                }
            }
        }
    },
    'sponsor_list': {
        'type': 'dict',
        'required': True,
        'schema': {
            'sponsor': {
                'type': 'list',
                'required': True,
                'schema': {
                    "type": "dict",
                    "schema": {
                        "sponsor_name": {
                            "type": "string",
                            "required": True
                        },
                        "sponsor_protocol_no": {
                            "type": "string",
                            "required": True
                        },
                        "is_principal_sponsor": {
                            "type": "string",
                            "required": True
                        },
                        "sponsor_roles": {
                            "type": "string",
                            "required": True
                        }
                    }
                }
            }
        }
    },
    'stage': {
        'type': 'list',
        'required': False
    },
    'status': {
        'type': 'string',
        'required': False
    },
    'summary': {
        'type': 'string',
        'required': False
    },
    'oncpro_link': {
        'type': 'string',
        'required': False
    },
    'title': {
        'type': 'string',
        'required': False
    },
    'prior_treatment_requirements': {
        'type': 'list',
        'schema': {
            'type': 'string',
        },
        'required': False,
        'empty': True
    },
    'match': {
        'type': 'list',
        'schema': {},
        'allow_unknown': True,
        'match': True
    }
}

map = {
    'key_old': {
        'type': 'string'
    },
    'key_new': {
        'type': 'string'
    },
    'values': {
        'type': 'dict',
        'schema': {
            'type': 'string'
        }
    }
}