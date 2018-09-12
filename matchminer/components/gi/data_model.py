gikb_schema = {
    'mrn': {'type': 'string', 'required': True},
    'name': {'type': 'string', 'required': True},
    'sample_id': {'type': 'string', 'required': True},
    'prelim_report_generated': {'type': 'boolean'},
    'final_report_generated': {'type': 'boolean'},
    'trial_matches': {'allow_unknown': True},
    'provider_name': {'type': 'string'},
    'provider_npi': {'type': 'integer'},
    'gi_report_date': {'type': 'string'},
    'mrn_is_deceased': {'type': 'boolean'}
}

gi_gold_standard_truth = {
    'mrn': {'type': 'string', 'required': True},
    'oncologist': {'type': 'string', 'required': True},
    'alterations': {'allow_unknown': True, 'required': True},
    'gi_report_date': {'type': 'string'},
    'review_date': {'type': 'string', 'nullable': True, 'required': True},
    'reviewers': {'type': 'string', 'nullable': True, 'required': True},

    # clinical data
    'sample_id': {'type': 'string', 'required': True},
    'clinical_id': {'type': 'string', 'required': True},
    'patient_name': {'type': 'string', 'required': True},
    'patient_initials': {'type': 'string', 'required': True},
    'tumor_type': {'type': 'string', 'required': True},
    'tumor_type_meta': {'type': 'string', 'required': True, 'nullable': True},
    'disease_center': {'type': 'string', 'required': True},
    'physician': {'type': 'string', 'required': True},
    'report_date': {'type': 'string', 'required': True},
    'block_number': {'type': 'string', 'required': True},
    'panel_version': {'type': 'integer', 'required': True},
    'report_version': {'type': 'integer', 'required': True},
    'biopsy_site': {'type': 'string', 'required': True},
    'biopsy_site_type': {'type': 'string', 'required': True},
    'qc_result': {'type': 'string', 'required': True},
    'mean_sample_coverage': {'type': 'integer', 'required': True},
    'tumor_purity_per': {'type': 'float', 'required': True},
    'pdf_layout_version': {'type': 'integer', 'required': True},

    # genomic data
    'num_tier1_variants': {'type': 'integer', 'required': True},
    'num_tier2_variants': {'type': 'integer', 'required': True},
    'num_tier3_variants': {'type': 'integer', 'required': True},
    'num_tier4_variants': {'type': 'integer', 'required': True},
    'num_cnvs': {'type': 'integer', 'required': True},
    'num_actionable_cnvs': {'type': 'integer', 'required': True},
    'num_investigational_cnvs': {'type': 'integer', 'required': True},
    'num_cnv_regions': { 'type': 'integer', 'required': True},
    'num_actionable_cnv_regions': { 'type': 'integer', 'required': True},
    'num_investigational_cnv_regions': { 'type': 'integer', 'required': True},
    'mutation_df': {'allow_unknown': True, 'required': True},
    'cnv_df': {'allow_unknown': True, 'required': True},
    'sv_gene': {'allow_unknown': True, 'nullable': True},
    'filename': {'type': 'string'},
    'sv_fda_therapies': {'type': 'list', 'schema': {'allow_unknown': True}, 'required': True, 'nullable': True},
    'sv_offlabel_therapies': {'type': 'list', 'schema': {'allow_unknown': True}, 'required': True, 'nullable': True},
    'sv_comment': {'type': 'string', 'nullable': True},

    # mutational signature data
    'mmr_status': {'type': 'string', 'required': True},
    'pole_status': {'type': 'string', 'required': True},

    # mutational burden data
    'tmb': {'type': 'float', 'required': True},
    'all_profile_percentile': {'type': 'integer', 'required': True},
    'tumor_type_percentile': {'type': 'integer', 'required': True},
    'num_oncopanel': {'type': 'integer', 'required': True},
    'num_tumor_type_oncopanel': {'type': 'integer', 'required': True},

    # therapy data
    'sig_fda_therapies': {'type': 'list', 'schema': {'allow_unknown': True}, 'required': True},
    'sig_offlabel_therapies': {'type': 'list', 'schema': {'allow_unknown': True}, 'required': True},
    'summary': {'allow_unknown': True},

    # trial match data
    'sig_trial_matches': {'type': 'list', 'schema': {'allow_unknown': True}, 'required': True},
    'mutation_trial_matches': {'allow_unknown': True, 'required': True},
    'cnv_trial_matches': {'allow_unknown': True, 'required': True},
    'actionable_trial_matches': {'type': 'list', 'schema': {'allow_unknown': True}, 'required': True},
    'tier4_trial_matches': {'type': 'list', 'schema': {'allow_unknown': True}, 'required': True},

    # misc
    'is_unreviewed': {'type': 'boolean'},
    'display_caveat': {'type': 'boolean'},
    'mrn_is_deceased': {'type': 'boolean'}
}

gi_final_reports_schema = {

    # autopopulated columns
    'filename': {'type': 'string', 'readonly': True},
    'initials': {'type': 'string', 'readonly': True},
    'firstName': {'type': 'string', 'readonly': True},
    'lastName': {'type': 'string', 'readonly': True},
    'sampleId': {'type': 'string', 'readonly': True},
    'mrn': {'type': 'string', 'readonly': True},
    'ordPhysicianName': {'type': 'string', 'readonly': True},
    'ProviderName': {'type': 'string', 'readonly': True},

    # manually populated columns
    'clinicalStatus': {'type': 'string'},
    'orderForMeeting':  {'type': 'integer'},
    'reportSentToProviderDate': {'type': 'datetime'},

    # google form populated columns
    'formReviewed': {'type': 'boolean'},
    'meetingDate': {'type': 'datetime'},
    'meetingTitles': {'type': 'string'},
    'meetingNames': {'type': 'string'},
    'includeSV': {'type': 'string'},
    'summaryStatement1': {'type': 'string'},
    'summaryStatement2': {'type': 'string'},
    'summaryStatement3': {'type': 'string'},
    'summaryStatement4': {'type': 'string'},
    'summaryComment1': {'type': 'string'},
    'summaryComment2': {'type': 'string'},
    'summaryComment3': {'type': 'string'},
    'summaryComment4': {'type': 'string'},
    'reportEditsNeeded': {'type': 'boolean'},
    'reportEdits': {'type': 'string'},
    'translationalResearchOpportunity': {'type': 'string'},
    'formTriggerId': {'type': 'string'},
    'formActive': {'type': 'boolean'}
}

gi_kb1_schema = {
    'gene': {'type': 'string'},
    'variantCategory': {'type': 'string'},
    'variantDetails': {'type': 'string', 'nullable': True},
    'reviewer': {'type': 'string'},
    'dateAdded': {'type': 'datetime'},
    'dateRemoved': {'type': 'datetime', 'nullable': True},
    'exclude': {'type': 'boolean', 'default': False},
    'gene_class': {'type': 'string', 'nullable': True}
}

gi_kb2_schema = {

    # autopopulated columns
    'gene': {'type': 'string', 'readonly': True},
    'variantCategory': {'type': 'string', 'readonly': True},
    'variantClassification': {'type': 'string', 'readonly': True},
    'genomicChange': {'type': 'string', 'readonly': True},
    'nucleotideChange': {'type': 'string', 'readonly': True},
    'proteinChange': {'type': 'string', 'readonly': True},
    'exon': {'type': 'integer', 'readonly': True},
    'transcript': {'type': 'string', 'readonly': True},
    'tier1Count': {'type': 'string', 'readonly': True},
    'tier2Count': {'type': 'string', 'readonly': True},
    'tier3Count': {'type': 'string', 'readonly': True},
    'tier4Count': {'type': 'string', 'readonly': True},
    'dateAdded': {'type': 'datetime', 'readonly': True},
    'assignedReviewer': {'type': 'string', 'readonly': True},
    'cosmicLink': {'type': 'string', 'readonly': True},
    'clinvarLink': {'type': 'string', 'readonly': True},
    'unprotLink': {'type': 'string', 'readonly': True},
    'oncokbLink': {'type': 'string', 'readonly': True},
    'civicLink': {'type': 'string', 'nullable': True, 'readonly': True},
    'jaxLink': {'type': 'string', 'nullable': True, 'readonly': True},
    'formLink': {'type': 'string', 'default': 'not yet', 'readonly': True},

    # manually populated columns
    'oncogenic': {'type': 'string'},
    'function': {'type': 'string'},
    'comments': {'type': 'string'},
    'pmids': {'type': 'string'},
    'needsToBeDiscussed': {'type': 'boolean', 'default': False},
    'discrepancyWithCAMDComment': {'type': 'boolean', 'default': False},

    # autopopulated after review columns
    'dateReviewed': {'type': 'datetime', 'readonly': True},
    'reviewer': {'type': 'string', 'readonly': True},

    # trigger columns
    'formTriggerId': {'type': 'string'},
    'formActive': {'type': 'boolean'},

    # manually populated by KSG
    'commentCAMD': {'type': 'string', 'nullable': True}
}

gi_kb3_schema = {
    'gene': {'type': 'string'},
    'variantCategory': {'type': 'string'},
    'variantDetails': {'type': 'string', 'nullable': True},
    'mutationClassification': {'type': 'string', 'nullable': True},
    'cancerType': {'type': 'string'},
    'oncotreeCode': {'type': 'string', 'nullable': True},
    'FDAApprovedTherapy': {'type': 'string', 'nullable': True},
    'offLabelTherapy': {'type': 'string', 'nullable': True},
    'translationalResearch': {'type': 'string', 'nullable': True},
    'dateUpdated': {'type': 'datetime'}
}

gi_providers_schema = {
    'lastName': {'type': 'string'},
    'firstName': {'type': 'string'},
    'middleInitial': {'type': 'string', 'nullable': True},
    'pilot': {'type': 'boolean', 'default': False},
    'npi': {'type': 'string'}
}