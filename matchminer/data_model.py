status_schema = {
    'last_update': {
        'type': 'datetime',
        'required': True
    },
    'new_clinical': {
        'type': 'integer',
        'required': True
    },
    'updated_clinical': {
        'type': 'integer',
        'required': False
    },
    'new_genomic': {
        'type': 'integer',
        'required': True,
        'nullable': True
    },
    'updated_genomic': {
        'type': 'integer',
        'required': False,
        'nullable': True
    },
    'silent': {
        'type': 'boolean',
        'required': True
    },
    'backup_path': {
        'type': 'string',
        'readonly': True
    },
    'data_push_id': {
        'type': 'string',
        'required': True
    },
    'test_name': {
        'type': 'string',
        'required': False
    },
    'deleted': {
        'type': 'integer',
        'required': False,
        'nullable': True
    }
}

import_log_schema = {
    'new_samples': {
        'type': 'list',
        'required': False
    },
    'updated_samples': {
        'type': 'list',
        'required': False
    },
    'deleted_samples': {
        'type': 'list',
        'required': False
    },
    'new_samples_count': {
        'type': 'integer',
        'required': False
    },
    'updated_samples_count': {
        'type': 'integer',
        'required': False
    },
    'deleted_samples_count': {
        'type': 'integer',
        'required': False
    },
    'test_name': {
        'type': 'string',
        'required': False
    },
    'data_push_id': {
        'type': 'string',
        'required': False
    }
}

user_log_schema = {
    'service': {
        'type': 'string',
        'required': True
    },
    'action': {
        'type': 'string',
        'allowed': ["add", "update", "delete"]
    },
    'user': {
        'type': 'dict',
        'schema': {},
        'allow_unknown': True
    }
}

user_schema = {
    'first_name': {
        'type': 'string',
        'required': True
    },
    'last_name': {
        'type': 'string',
        'required': True
    },
    'title': {
        'type': 'string',
        'required': True
    },
    'email': {
        'type': 'string',
        'required': True
    },
    'token': {
        'type': 'string',
        'required': False,
        'readonly': True
    },
    'oncore_token': {
        'type': 'string',
        'required': False,
        'readonly': True
    },
    'user_name': {
        'type': 'string',
        'required': True
    },
    'teams': {
        'type': 'list',
        'required': True,
        'schema': {
            'type': 'objectid',
            'data_relation': {
                'resource': 'team',
                'field': '_id',
                'embeddable': True
            }
        },
    },
    'last_auth': {
        'type': 'datetime',
        'readonly': True
    },
    'roles': {
        'type': 'list',
        'schema': {
            'type': 'string'
        },
        'required': True
    },
    'silent': {
        'type': 'boolean',
        'required': False
    },
}


def default_temporary():
    return True


filter_schema = {
    'TEAM_ID': {'type': 'objectid', 'required': True},
    'USER_ID': {'type': 'objectid', 'required': True},
    'genomic_filter': {
        'type': 'dict',
        'schema': {},
        'allow_unknown': True
    },
    'clinical_filter': {
        'type': 'dict',
        'schema': {},
        'allow_unknown': True
    },
    'match': {
        'type': 'list',
        'allow_unknown': True
    },
    'label': {
        'type': 'string'
    },
    'description': {
        'type': 'string',
        'readonly': True
    },
    'protocol_id': {
        'type': 'string'
    },
    'test_name': {
        'type': 'string'
    },
    'badgeColor': {
        'type': 'string'
    },
    'badgeTextColor': {
        'type': 'string'
    },
    'status': {
        'type': 'integer',
        'required': True
    },
    'num_matches': {
        'type': 'integer'
    },
    'num_pairs': {
        'type': 'integer'
    },
    'num_samples': {
        'type': 'integer'
    },
    'num_clinical': {
        'type': 'integer'
    },
    'num_genomic': {
        'type': 'integer'
    },
    'num_genomic_samples': {
        'type': 'integer'
    },
    'temporary': {
        'type': 'boolean',
        'required': True,
    },
    'EMAIL': {
        'type': 'boolean',
        'required': False,
    },
    'filter_hash': {
        'type': 'string',
    },
    'enrollment': {
        'type': 'dict',
        'schema': {
            'x_axis': {
                'type': 'list',
                'schema': {'type': 'datetime'}
            },
            'y_axis': {
                'type': 'list',
                'schema': {'type': 'integer'}
            }
        }
    }
}

clinical_schema = {
    'ALT_MRN': {'type': 'string'},
    'MRN': {'type': 'string', 'required': True},
    'POWERPATH_PATIENT_ID': {'type': 'string'},
    'PATIENT_ID': {'type': 'string'},
    'SAMPLE_ID': {
        'type': 'string',
        'unique': True
    },
    'data_push_id': {'type': 'string', 'required': False, 'nullable': True},

    'GENDER': {'type': 'string', 'required': True},
    'LAST_NAME': {'type': 'string', 'required': True},
    'FIRST_NAME': {'type': 'string', 'required': True},
    'FIRST_LAST': {'type': 'string', 'readonly': True},
    'LAST_FIRST': {'type': 'string', 'readonly': True},
    'BIRTH_DATE': {'type': 'datetime', 'required': True},
    'COLLECTION_DATE': {'type': 'datetime', 'required': False, 'nullable': True},
    'BIRTH_DATE_INT': {'type': 'integer', 'required': False},
    'VITAL_STATUS': {'type': 'string', 'required': True, 'allowed': ['alive', 'deceased', None], 'nullable': True},
    'LAST_VISIT_DATE': {'type': 'datetime'},

    'TOTAL_ALIGNED_READS': {'type': 'integer', 'required': False},
    'PCT_TARGET_BASE': {'type': 'float', 'required': False},
    'MEAN_SAMPLE_COVERAGE': {'type': 'integer', 'required': False},
    'DISEASE_CENTER_DESCR': {'type': 'string', 'nullable': True, 'required': False},
    'ONCOTREE_BIOPSY_SITE_TYPE': {'type': 'string', 'nullable': True},
    'ORI_PATH_DIAGNOSIS': {'type': 'string', 'required': False, 'nullable': True},
    'IP_DIAGNOSIS': {'type': 'string', 'required': False, 'nullable': True},
    'PANEL_TEST_IND': {'type': 'string', 'required': False},
    'PLATE_NAME': {'type': 'string', 'required': False},

    'ONCOTREE_BIOPSY_SITE': {'type': 'string', 'nullable': True},
    'ONCOTREE_BIOPSY_SITE_NAME': {'type': 'string', 'nullable': True},
    'ONCOTREE_BIOPSY_SITE_META': {'type': 'string', 'required': False, 'nullable': True},
    'ONCOTREE_BIOPSY_SITE_COLOR': {'type': 'string', 'required': False, 'nullable': True},
    'ONCOTREE_PRIMARY_DIAGNOSIS': {'type': 'string', 'required': True, 'nullable': True},
    'ONCOTREE_PRIMARY_DIAGNOSIS_NAME': {'type': 'string', 'required': True, 'nullable': True},
    'ONCOTREE_PRIMARY_DIAGNOSIS_META': {'type': 'string', 'nullable': True, 'required': False},
    'ONCOTREE_PRIMARY_DIAGNOSIS_COLOR': {'type': 'string', 'required': False},
    'ORD_PHYSICIAN_NAME': {'type': 'string', 'required': False},
    'ORD_PHYSICIAN_NPI': {'type': 'integer', 'nullable': True, 'required': False},
    'ORD_PHYSICIAN_EMAIL': {'type': 'string', 'nullable': True, 'required': True},
    'PATHOLOGIST_NAME': {'type': 'string', 'nullable': True, 'required': True},

    'PANEL_VERSION': {'type': 'integer', 'required': True},
    'REPORT_COMMENT': {'type': 'string', 'nullable': True, 'required': False},
    'DATE_RECEIVED_AT_SEQ_CENTER': {'type': 'datetime', 'required': False, 'nullable': True},
    'REPORT_DATE': {
        'type': 'datetime',
        'required': True,
        'nullable': True
    },
    'REPORT_VERSION': {'type': 'integer', 'nullable': True, 'required': True},
    'TEST_TYPE': {'type': 'string', 'required': False},

    'BLOCK_NUMBER': {'type': 'string', 'nullable': True, 'required': False},
    'QC_RESULT': {'type': 'string', 'required': False},
    'CNV_RESULTS': {'type': 'string', 'required': False},
    'SNV_RESULTS': {'type': 'string', 'required': False},

    'QUESTION1_YN': {'type': 'string', 'consented': True, 'required': False},
    'QUESTION2_YN': {'type': 'string', 'required': False},
    'QUESTION3_YN': {'type': 'string', 'required': False},
    'QUESTION4_YN': {'type': 'string', 'required': False},
    'QUESTION5_YN': {'type': 'string', 'required': False},
    'TEST_NAME': {'type': 'string', 'required': True},
    'CRIS_YN': {'type': 'string', 'required': False},
    'HASH_VITALS_OMITTED': {'type': 'string', 'required': False},
    'CONSENT_17000': {'type': 'string', 'required': False},

    'TOTAL_READS': {'type': 'integer', 'required': False},
    'TUMOR_PURITY_PERCENT': {'type': 'float', 'required': False, 'nullable': True},

    'TUMOR_MUTATIONAL_BURDEN_PER_MEGABASE': {'type': 'float', 'nullable': True, 'required': False},
    'CANCER_TYPE_PERCENTILE': {'type': 'float', 'nullable': True, 'required': False},
    'ALL_PROFILE_PERCENTILE': {'type': 'float', 'nullable': True, 'required': False},
    'MMR_STATUS': {
        'type': 'string',
        'nullable': True,
        'required': False,
        'allowed': [
            'Cannot assess',
            'Indeterminate (see note)',
            'Proficient (MMR-P / MSS)',
            'Deficient (MMR-D / MSI-H)',
            None
        ]
    },
    'METAMAIN_COUNT': {'type': 'integer', 'nullable': True, 'required': False},
    'CASE_COUNT': {'type': 'integer', 'nullable': True, 'required': False},
    'PDF_LAYOUT_VERSION': {
        'type': 'integer',
        'allowed': [1, 2, 3]
    },

    'FILTER': {
        'type': 'list',
        'schema': {
            'type': 'objectid',
            'required': False,
            'data_relation': {
                'resource': 'filter',
                'field': '_id',
                'embeddable': True
            },
        },
        'readonly': True
    },
    'ENROLLED': {
        'type': 'list',
        'schema': {
            'type': 'objectid',
            'required': False,
            'data_relation': {
                'resource': 'filter',
                'field': '_id',
                'embeddable': True
            },
        },
        'readonly': True
    }
}

val_stderr = {
    "value": {
        'type': 'float',
        'required': True,
        'nullable': True
    },
    "stderr": {
        'type': 'float',
        'required': True,
        'nullable': True
    },
    "percentile_tumor": {
        'type': 'integer',
        'required': True,
        'nullable': True
    },
    "percentile_total": {
        'type': 'integer',
        'required': True,
        'nullable': True
    }
}

ip_biomarker_schema = {
    'type': 'dict',
    'schema': {
        'it': {
            'type': 'dict',
            'schema': val_stderr
        },
        'tsi': {
            'type': 'dict',
            'schema': val_stderr
        },
        'it_tsi': {
            'type': 'dict',
            'schema': val_stderr
        }
    }
}

immunoprofile_schema = {
    "sample_id": {
        'type': 'string',
        'unique': True,
        'required': True
    },
    "biomarkers": {
        'type': 'dict',
        'schema': {
            "cd8": ip_biomarker_schema,
            "pd1": ip_biomarker_schema,
            "cd8_pd1": ip_biomarker_schema,
            "foxp3": ip_biomarker_schema
        }
    },
    "pdl1": {
        'type': 'dict',
        'schema': {
            "summary": {
                'type': 'dict',
                'required': True,
                'nullable': True,
                'schema': {
                    'pdl1_mal': {
                        'type': 'string',
                        'required': False,
                        'nullable': True
                    },
                    'pdl1_inf': {
                        'type': 'string',
                        'required': False,
                        'nullable': True,
                    },
                    'pdl1_mal_inf': {
                        'type': 'string',
                        'required': False,
                        'nullable': True,
                    },
                    'pdl1_undef': {
                        'type': 'string',
                        'required': False,
                        'nullable': True,
                    },
                    'interpretation_comment': {
                        'type': 'string',
                        'required': True,
                        'nullable': False
                    },
                    'interpretation_reference': {
                        'type': 'string',
                        'required': True,
                        'nullable': True
                    }
                }
            },
            'scores': {
                'type': 'dict',
                'required': True,
                'schema': {
                    'tps': {
                        'type': 'dict',
                        'schema': val_stderr
                    },
                    'cps': {
                        'type': 'dict',
                        'schema': val_stderr
                    },
                    'ic': {
                        'type': 'dict',
                        'schema': val_stderr
                    },
                    'ica': {
                        'type': 'dict',
                        'schema': {
                            "value": {
                                'type': 'float',
                                'required': True,
                                'nullable': True
                            },
                            "percentile_tumor": {
                                'type': 'integer',
                                'required': True,
                                'nullable': True
                            },
                            "percentile_total": {
                                'type': 'integer',
                                'required': True,
                                'nullable': True
                            }
                        }
                    }
                }
            }
        }
    },
    'email': {
        'type': 'boolean',
        'required': True,
        'nullable': True
    },
    'report_version': {
        'type': 'integer',
        'required': True,
        'nullable': False
    },
    'panel_biomarkers': {
        'type': 'list',
        'required': True,
        'nullable': True
    },
    'clinical_id': {
        'type': 'objectid',
        'required': False,
        'data_relation': {
            'resource': 'clinical',
            'field': '_id',
            'embeddable': True
        },
    },
    'failed_sign_out': {
        'type': 'boolean',
        'required': True,
        'nullable': False
    },
    "version": {
        'type': 'integer',
        'required': True
    },
    'percentile': {
        'type': 'dict',
        'required': True,
        'nullable': True,
        'schema': {
            'tumor': {
                'type': 'integer',
            },
            'total': {
                'type': 'integer',
            },
            'tsi_tumor': {
                'type': 'integer',
            },
            'tsi_total': {
                'type': 'integer',
            },
        }
    }
}

genomic_schema = {
    # identifiers
    'CLINICAL_ID': {
        'type': 'objectid',
        'required': True,
        'data_relation': {
            'resource': 'clinical',
            'field': '_id',
            'embeddable': True
        },
    },
    'SAMPLE_ID': {'type': 'string', 'required': True},

    # global variables
    'VARIANT_CATEGORY': {
        'type': 'string',
        'allowed': ['MUTATION', 'CNV', 'SV', 'SIGNATURE']
    },
    'WILDTYPE': {
        'type': 'boolean',
        'required': True,
        'allowed': [True, False]
    },
    'TRUE_HUGO_SYMBOL': {'type': 'string'},

    # mutation variables.
    'BEST': {'type': 'boolean'},
    'VARIANT_TYPE': {'type': 'string', 'required': False},
    'PATHOGENICITY_RESERACH': {'type': 'string', 'required': False},
    'PATHOGENICITY_RESEARCH': {'type': 'string', 'required': False},
    'ANNOTATION_TOOL_NAME': {'type': 'string', 'required': False},
    'GNOMAD_FREQUENCY': {'type': 'string', 'required': False},
    'MAX_GNOMAD_FREQUENCY_VEP': {'type': 'string', 'required': False},
    'PATHOGENICITY_PATHOLOGIST': {'type': 'string', 'required': False},
    'VARIANT_ID': {'type': 'integer', 'required': False},
    'PIPELINE_VERSION': {'type': 'float', 'required': False},
    'ALLELE_RATIO': {'type': 'string', 'required': False},
    'READ': {'type': 'float', 'required': False},
    'READ_COUNT_VARIANT': {'type': 'float', 'required': False},
    'SEQ': {'type': 'string', 'required': False},
    'GENE': {'type': 'string', 'required': False},
    'ARM': {'type': 'string', 'required': False},
    'BAND': {'type': 'string', 'required': False},
    'ALLELE_FRACTION': {'type': 'float'},
    'ALTERNATE_ALLELE': {'type': 'string'},
    'TRUE_CDNA_CHANGE': {'type': 'string'},
    'TRUE_CDNA_TRANSCRIPT_ID': {'type': 'string'},
    'TRUE_ENTREZ_ID': {'type': 'string'},
    'TRUE_PROTEIN_CHANGE': {'type': 'string'},
    'TRUE_TRANSCRIPT_EXON': {'type': 'integer'},
    'TRUE_VARIANT_CLASSIFICATION': {'type': 'string'},
    'TRUE_STRAND': {'type': 'string'},
    'BESTEFFECT_CDNA_CHANGE': {'type': 'string'},
    'BESTEFFECT_CDNA_TRANSCRIPT_ID': {'type': 'string'},
    'BESTEFFECT_ENTREZ_ID': {'type': 'string'},
    'BESTEFFECT_HUGO_SYMBOL': {'type': 'string'},
    'BESTEFFECT_PROTEIN_CHANGE': {'type': 'string'},
    'BESTEFFECT_TRANSCRIPT_EXON': {'type': 'integer'},
    'BESTEFFECT_VARIANT_CLASSIFICATION': {'type': 'string'},
    'CANONICAL_CDNA_CHANGE': {'type': 'string'},
    'CANONICAL_CDNA_TRANSCRIPT_ID': {'type': 'string'},
    'CANONICAL_ENTREZ_ID': {'type': 'string'},
    'CANONICAL_HUGO_SYMBOL': {'type': 'string'},
    'CANONICAL_PROTEIN_CHANGE': {'type': 'string'},
    'CANONICAL_STRAND': {'type': 'string'},
    'CANONICAL_TRANSCRIPT_EXON': {'type': 'integer'},
    'CANONICAL_VARIANT_CLASSIFICATION': {'type': 'string'},
    'CHROMOSOME': {'type': 'string'},
    'POSITION': {'type': 'integer'},
    'COVERAGE': {'type': 'integer'},
    'REFERENCE_ALLELE': {'type': 'string'},
    'REFERENCE_GENOME': {'type': 'string'},
    'TIER': {
        'type': 'integer',
        'allowed': [1, 2, 3, 4]
    },
    'TRANSCRIPT_SOURCE': {'type': 'string'},
    'SOMATIC_STATUS': {'type': 'string'},

    # CNV variables.
    'CNV_CALL': {'type': 'string'},
    'CNV_BAND': {'type': 'string'},
    'CNV_ARM': {'type': 'string'},
    'CNV_HUGO_SYMBOL': {'type': 'string'},

    # structural variables.
    'STRUCTURAL_VARIANT_COMMENT': {'type': 'string'},

    'CYTOBAND': {'type': 'string'},
    'GENETIC_EVENT': {
        'type': 'string',
        'allowed': ['Arm level', 'Chromosomal level'],
        'nullable': True
    },
    'COPY_COUNT': {'type': 'integer'},
    'ACTIONABILITY': {
        'type': 'string',
        'allowed': ['actionable', 'investigational']
    },
    'CNV_ROW_ID': {'type': 'integer'},
    'MMR_STATUS': {
        'type': 'string',
        'nullable': True,
        'allowed': [
            'Cannot assess',
            'Indeterminate (see note)',
            'Proficient (MMR-P / MSS)',
            'Deficient (MMR-D / MSI-H)'
        ]
    },
    'TABACCO_STATUS': {'type': 'string', 'allowed': ['Yes', 'No', 'Cannot assess', 'insufficient variants'],
                       'nullable': True},
    'TEMOZOLOMIDE_STATUS': {'type': 'string', 'allowed': ['Yes', 'No', 'Cannot assess', 'insufficient variants'],
                            'nullable': True},
    'POLE_STATUS': {'type': 'string', 'allowed': ['Yes', 'No', 'Cannot assess', 'insufficient variants'],
                    'nullable': True},
    'APOBEC_STATUS': {'type': 'string', 'allowed': ['Yes', 'No', 'Cannot assess', 'insufficient variants'],
                      'nullable': True},
    'UVA_STATUS': {'type': 'string', 'allowed': ['Yes', 'No', 'Cannot assess', 'insufficient variants'],
                   'nullable': True},

    "EVENT_ID": {'type': 'integer', 'nullable': True},
    "STRUCTURAL_VARIANT_TYPE": {'type': 'string', 'nullable': True},
    "LEFT_PARTNER_CHROMOSOME": {'type': 'string', 'nullable': True},
    "LEFT_PARTNER_POSITION": {'type': 'integer', 'nullable': True},
    "LEFT_PARTNER_STRAND": {'type': 'string', 'nullable': True},
    "LEFT_PARTNER_GENE": {'type': 'string', 'nullable': True},
    "LEFT_PARTNER_BAND": {'type': 'string', 'nullable': True},
    "LEFT_PARTNER_EXON_INTRON": {'type': 'string', 'nullable': True},
    "LEFT_PARTNER_EXON_INTRON_NUM": {'type': 'integer', 'nullable': True},
    "RIGHT_PARTNER_CHROMOSOME": {'type': 'string', 'nullable': True},
    "RIGHT_PARTNER_POSITION": {'type': 'integer', 'nullable': True},
    "RIGHT_PARTNER_STRAND": {'type': 'string', 'nullable': True},
    "RIGHT_PARTNER_GENE": {'type': 'string', 'nullable': True},
    "RIGHT_PARTNER_BAND": {'type': 'string', 'nullable': True},
    "RIGHT_PARTNER_EXON_INTRON": {'type': 'string', 'nullable': True},
    "RIGHT_PARTNER_EXON_INTRON_NUM": {'type': 'integer', 'nullable': True},
    'TEST_NAME': {'type': 'string', 'required': False},

    'BESTEFFECT_REFSEQ_TRANSCRIPT_ID': {'type': 'string', 'required': False},
    'BESTEFFECT_ENSEMBL_TRANSCRIPT_ID': {'type': 'string', 'required': False},
    "CANONICAL_REFSEQ_TRANSCRIPT_ID": {'type': 'string', 'required': False},
    "CANONICAL_ENSEMBL_TRANSCRIPT_ID": {'type': 'string', 'required': False},
    "TRUE_REFSEQ_TRANSCRIPT_ID": {'type': 'string', 'required': False},
    "TRUE_ENSEMBL_TRANSCRIPT_ID": {'type': 'string', 'required': False},
}

for key in genomic_schema:
    if 'nullable' not in genomic_schema[key]:
        genomic_schema[key]['nullable'] = True
    if 'allowed' in genomic_schema[key]:
        genomic_schema[key]['allowed'].append(None)

match_schema = {
    'TEAM_ID': {'type': 'objectid', 'required': True},
    'USER_ID': {'type': 'objectid', 'required': True},
    'FILTER_STATUS': {'type': 'integer'},
    'MATCH_STATUS': {'type': 'integer'},
    'FILTER_ID': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'filter',
            'field': '_id',
            'embeddable': True
        },
    },
    'CLINICAL_ID': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'clinical',
            'field': '_id',
            'embeddable': True
        },
    },
    'VARIANTS': {
        'type': 'list',
        'schema': {
            'type': 'objectid',
            'data_relation': {
                'resource': 'genomic',
                'field': '_id',
                'embeddable': True
            },
        }
    },
    'MMID': {
        'type': 'string'
    },
    'PATIENT_MRN': {
        'type': 'string'
    },
    'ONCOTREE_PRIMARY_DIAGNOSIS_NAME': {
        'type': 'string'
    },
    'ONCOTREE_BIOPSY_SITE_TYPE':{
        'type': 'string'
    },
    'TRUE_HUGO_SYMBOL': {
        'type': 'string'
    },
    'TIER': {
        'required': False,
        'nullable': True
    },
    'ALLELE_FRACTION': {
        'type': 'float',
        'nullable': True
    },
    'VARIANT_CATEGORY': {
        'type': 'string'
    },
    'FILTER_NAME': {
        'type': 'string'
    },
    'REPORT_DATE': {
        'type': 'datetime'
    },
    'ENROLLED': {
        'type': 'boolean',
    },
    'EMAIL': {
        'type': 'boolean',
        'required': False,
    },
    'EMAIL_BODY': {
        'type': 'string',
        'nullable': True
    },
    'EMAIL_SUBJECT': {
        'type': 'string',
        'nullable': True
    },
    'LABEL': {
        'type': 'string',
        'nullable': True
    },
    'EMAIL_ADDRESS': {
        'type': 'string',
        'nullable': True
    },
    'QUERY_HASH': {
        'type': 'string',
        'required': False,
        'nullable': True
    },
    'PROTOCOL_ID': {
        'type': 'string',
        'required': False,
        'nullable': True
    },
    '_me_id': {
        'type': 'string',
        'required': False,
        'nullable': True
    },
    'clinical_id': {
        'type': 'objectid',
        'required': True,
        'nullable': True
    },
    'hash': {
        'type': 'string',
        'required': True,
        'nullable': True
    },
    'is_disabled': {
        'type': 'boolean',
        'required': True,
    },
    'data_push_id': {
        'type': 'string',
        'required': False,
        'nullable': True
    },
    'sample_id': {
        'type': 'string',
        'required': False
    },
    'sort_order': {
        'type': 'list',
        'nullable': True,
        'required': False
    },
}

hipaa_transaction = {
    'user_id': {
        'type': 'string'
    },
    'patient_id': {
        'type': 'string'
    },
    'phi': {
        'type': 'list',
        'schema': {
            'type': 'string'
        }
    },
    'reason': {
        'type': 'string',
    },
    'timestamp': {
        'type': 'datetime'
    }
}

team = {
    "name": {"type": "string"},
}

facet_schema = {
    'type' : 'dict',
    'schema' : {
        'id': {
            'type': 'integer',
            'required': True,
            'empty': False
        },
            'value': {
            'type': 'string',
            'required': True,
            'empty': False
        },
    }
}


parent_schema = {
    'last_updated': {
        'type': 'string',
        'default': ''
    },
    'curated_on': {
        'type': 'string',
        'default': ''
    },
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
    'cancer_center_current_accrual': {
        'type': 'integer',
        'default': 0
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
                            'allowed': ['Y', 'N']
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
    },
    '_summary': {
        'type': 'dict',
        'allow_unknown': {
            'type': 'list',
            'schema': {
                "investigator": {'type': 'string'},
                "age_summary": {'type': 'string'},
                "nct_number": {'type': 'string'},
                "disease_status": {'type': 'list', 'schema': {'type': 'string'}},
                "protocol_number": {'type': 'string'},
                "accrual_goal": {'type': 'integer'},
                "tumor_types": {'type': 'list', 'schema': {'type': 'string'}},
                "genes": {'type': 'list', 'schema': {'type': 'string'}},
                "coordinating_center": {'type': 'string'},
                "sponsor": {'type': 'string'},
                "phase_summary": {'type': 'string'},
                "disease_center": {'type': 'string'},
                "drugs": {'type': 'list', 'schema': {'type': 'string'}},
                "variants": {'type': 'list', 'schema': {'type': 'string'}},
                'status': {
                    'type': 'list',
                    'schema': facet_schema
                },
                'phase': {
                    'type': 'list',
                    'schema': facet_schema
                },
                'site': {
                    'type': 'list',
                    'schema': facet_schema
                },
                'drug': {
                    'type': 'list',
                    'schema': facet_schema
                },
                'management_group': {
                    'type': 'list',
                    'schema': facet_schema
                },
                'age': {
                    'type': 'list',
                    'schema': facet_schema
                }
            }
        }
    }
}

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
    },
    'gender': {
        'type': 'string',
        'required': False,
        'allowed': ['Male', 'Female', 'X']
    },
    'tmb_numerical': {
        'type': 'string',
    }
}

yaml_genomic_schema = {
    'hugo_symbol': {
        'type': 'string',
        'required': False,
        'nullable': True
    },
    'protein_change': {
        'type': 'string',
    },
    'variant_category': {
        'type': 'string',
        'allowed': ['Mutation', 'Copy Number Variation', 'Structural Variation', 'Any Variation',
                    '!Mutation', '!Copy Number Variation', '!Structural Variation']
    },
    'wildtype': {
        'type': 'boolean',
        'required': False,
        'allowed': [True, False]
    },
    'cnv_call':{
        'type': 'string',
        'required': False,
        'allowed': ["Low Amplification", "High Amplification", "Homozygous Deletion", "Heterozygous Deletion",
                    "!Low Amplification", "!High Amplification", "!Homozygous Deletion", "!Heterozygous Deletion"]
    },
    'wildcard_protein_change':{
        'type': 'string',
        'required': False,
    },
    'exon': {
        'type': 'integer',
        'required': False,
    },
    'variant_classification':{
        'type': 'string',
        'required': False,
        'allowed': ['In_Frame_Del', 'In_Frame_Ins', 'Missense_Mutation', 'Nonsense_Mutation', 'Nonstop_Mutation',
                    'Del_Ins', 'Frameshift', 'Frame_Shift_Del','Frame_Shift_Ins', 'Frameshift_mutation',
                    'Inframe_Indel', 'Initiator_Codon', 'Intron', 'intron', 'Intron_mutation',
                    'Missense and Splice_Region', 'RNA', 'Silent', 'Splice_Acceptor', 'Splice_Donor', 'Splice_Region',
                    'Splice_Site', 'Splice_Lost', 'Translation_Start_Site', 'coding_sequence', 'intergenic_variant',
                    'protein_altering', 'splice site_mutation', 'stop_retained', 'synonymous', "3'UTR", "3_prime_UTR"
                    "5'Flank", "5'UTR", "5'UTR_mutation", "5_prime_UTR", "!Missense_Mutation"]
    },
    'fusion_partner_hugo_symbol':{
        'type': 'string',
        'required': False,
    },
    'display_name': {
        'type': 'string',
        'required': False
    },
    'mmr_status': {
        'type': 'string',
        'required': False,
        'allowed': ['MMR-Proficient', 'MMR-Deficient']
    },
    'ms_status': {
        'type': 'string',
        'required': False,
        'allowed': ['MSI-H', 'MSI-L', 'MSS']
    },
    'pole_signature': {
        'type': 'string',
        'required': False,
        'allowed': ['Yes', 'No']
    },
    'tobacco_signature': {
         'type': 'string',
         'required': False,
         'allowed': ['Yes', 'No']
    },
    'apobec_signature': {
         'type': 'string',
         'required': False,
         'allowed': ['Yes', 'No']
    },
    'uva_signature': {
        'type': 'string',
        'required': False,
        'allowed': ['Yes', 'No']
    },
    'temozolomide_signature': {
        'type': 'string',
        'required': False,
        'allowed': ['Yes', 'No']
    },
    'tier': {
        'type': 'list',
        'required': False,
        'allowed': ['1', '2', '3', '4']
    }
}


response_schema = {
    'match_id': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'match',
            'field': '_id',
            'embeddable': True
        },
    },
    'notification_id': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'user',
            'field': '_id',
            'embeddable': True
        },
    },
    'match_status': {'type': 'string', 'required': True},
    'time_clicked': {'type': 'datetime', 'required': True},
    'expiry_date': {'type': 'datetime', 'required': True},
    'ip_address': {'type': 'string', 'required': True},
    'allow_update': {'type': 'boolean', 'required': True},
    'return_url': {'type': 'string', 'required': True},
    'response_text': {'type': 'string', 'required': True},
    'status': {'type': 'string', 'required': True},
    'clinical_trial_id': {'type': 'string', 'required': True},
    'response_recorded': {'type': 'string', 'required': True},
    'deferred_contact': {
        'type': 'dict',
        'schema': {
            'name': {'type': 'string', 'required': True},
            'email': {'type': 'string', 'required': True}
        }
    }
}


email_schema = {
    'email_from': {'type': 'string', 'required': True},
    'email_to': {'type': 'string', 'required': True},
    'subject': {'type': 'string', 'required': True},
    'body': {'type': 'string', 'required': True},
    'sent': {'type': 'boolean', 'default': False},
    'cc': {'type': 'list', 'schema': {'type': 'string'}, 'required': True},
    'num_failures': {'type': 'integer', 'default': 0},
    'errors': {'type': 'list', 'schema': {'type': 'string'}, 'default': []}
}

dashboard_schema = {
    'active_filter_data_set': {'type': 'list', 'required': False},
    'active_user_data_set': {'type': 'list', 'required': False},
    'inactive_user_data_set': {'type': 'list', 'required': False},
    'mm_data_set': {'type': 'list', 'required': False},
}

public_stats_schema = {
    'num_clinical_trials': {'type': 'integer'},
    'num_patients': {'type': 'integer'}
}

trial_match_schema = {
    'mrn': {'type': 'string'},
    'sample_id': {'type': 'string'},
    'first_last': {'type': 'string'},
    'protocol_no': {'type': 'string'},
    'genomic_alteration': {'type': 'string', 'readonly': True},
    'trial_accrual_status': {'type': 'string', 'allowed': ['open', 'closed']},
    'trial_curation_level_status': {'type': 'string', 'required': False},
    'match_level': {'type': 'string', 'allowed': ['step', 'arm', 'dose']},
    'code': {'type': 'string'},
    'internal_id': {'type': 'string'},
    'ord_physician_name': {'type': 'string', 'nullable': True},
    'ord_physician_email': {'type': 'string', 'nullable': True},
    'vital_status': {'type': 'string', 'allowed': ['alive', 'deceased'], 'nullable': True},
    'oncotree_primary_diagnosis_name': {'type': 'string', 'nullable': True},
    'true_hugo_symbol': {'type': 'string', 'nullable': True},
    'true_protein_change': {'type': 'string', 'nullable': True},
    'true_variant_classification': {'type': 'string', 'nullable': True},
    'variant_category': {'type': 'string', 'nullable': True, 'allowed': ['MUTATION', 'CNV', 'SV']},
    'report_date': {'type': 'datetime', 'nullable': True},
    'chromosome': {'type': 'string', 'nullable': True},
    'position': {'type': 'integer', 'nullable': True},
    'true_cdna_change': {'type': 'string', 'nullable': True},
    'reference_allele': {'type': 'string', 'nullable': True},
    'true_transcript_exon': {'type': 'string', 'nullable': True},
    'canonical_strand': {'type': 'string', 'nullable': True},
    'allele_fraction': {'type': 'float', 'nullable': True},
    'cnv_call': {'type': 'string', 'nullable': True},
    'wildtype': {'type': 'boolean', 'nullable': True},
    'match_type': {'type': 'string', 'allowed': ['variant', 'gene']},
    'tier': {'type': 'integer', 'allowed': [1, 2, 3, 4]},
    'clinical_id': {'type': 'objectid'},
    'genomic_id': {'type': 'objectid'},
    'sort_order': {'type': 'integer'},
    'trial_summary_status': {'type': 'string', 'required': False},
    'show_in_ui': {'type': 'boolean', 'required': False},
    'is_disabled': {'type': 'boolean', 'required': False}
}

negative_genomic_schema = {
    'clinical_id': {'type': 'objectid', 'data_relation': {'resource': 'clinical'}, 'required': True},
    'sample_id': {'type': 'string', 'required': True},
    'true_hugo_symbol': {'type': 'string', 'required': True},
    'true_transcript_exon': {'type': 'integer', 'nullable': True},
    'true_codon': {'type': 'integer', 'nullable': True},
    'coverage': {'type': 'float', 'required': True, 'nullable': True},
    'coverage_type': {'type': 'string', 'allowed': ['PN', 'PLC', 'NPLC'], 'required': True},
    'panel': {'type': 'string', 'required': True},
    'roi_type': {'type': 'string', 'required': True, 'allowed': ['C', 'R', 'M', 'G', 'E', None], 'nullable': True},
    'entire_gene': {'type': 'boolean', 'readonly': True},
    'show_exon': {'type': 'boolean', 'readonly': True},
    'show_codon': {'type': 'boolean', 'readonly': True},
    'TEST_NAME': {'type': 'string', 'required': False}
}

patient_view_schema = {
    'mrn': {'type': 'string'},
    'protocol_no': {'type': 'string'},
    'user_id': {'type': 'objectid', 'data_relation': {'resource': 'user'}, 'readonly': True},
    'user_first_name': {'type': 'string', 'readonly': True},
    'user_last_name': {'type': 'string', 'readonly': True},
    'user_user_name': {'type': 'string', 'readonly': True},
    'user_email': {'type': 'string', 'readonly': True},
    'num_views_match_list': {'type': 'integer', 'readonly': True},
    'num_views_details_list': {'type': 'integer', 'readonly': True},
    'view_date': {'type': 'datetime', 'readonly': True},
    'filter_label': {'type': 'string', 'nullable': True},
    'filter_protocol_no': {'type': 'string', 'nullable': True},
    'requires_manual_review': {'type': 'boolean', 'default': False},
    'from_details': {'type': 'boolean', 'required': False, 'nullable': True},
    'filter_match': {'type': 'boolean', 'required': False, 'nullable': True}
}

enrollment_schema = {
    'mrn': {'type': 'string', 'required': True},
    'protocol_no': {'type': 'string', 'required': True, 'nullable': True},
    'user_user_name': {'type': 'string'},
    'user_first_name': {'type': 'string'},
    'user_last_name': {'type': 'string'},
    'requires_manual_review': {'type': 'boolean', 'default': False},
    'has_onstudy_date': {'type': 'boolean', 'default': True},
    'consent_date': {'type': 'datetime', 'nullable': True},
    'onstudy_date': {'type': 'datetime', 'nullable': True},
    'ontreatment_date': {'type': 'datetime', 'nullable': True},
    'filter_label': {'type': 'string', 'nullable': True},
    'filter_protocol_no': {'type': 'string', 'nullable': True}
}
