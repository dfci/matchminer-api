gi_gold_standard_truth = {
    'mrn': {'type': 'string', 'required': True},
    'oncologist': {'type': 'string', 'required': True},
    'alterations': {'allow_unknown': True, 'required': True},
    'gi_report_date': {'type': 'string'},
    'review_date': {'type': 'string', 'nullable': True, 'required': True},
    'reviewers': {'type': 'string', 'nullable': True, 'required': True},

    # clinical data
    'sample_id': {'type': 'string', 'required': True},
    'provider_name': {'type': 'string', 'required': True},
    'provider_npi': {'type': 'integer', 'required': True},
    'clinical_id': {'type': 'string', 'required': True},
    'patient_name': {'type': 'string', 'required': True},
    'name': {'type': 'string', 'required': True},
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
    'num_tier1_SV_variants': {'type': 'integer', 'required': True},
    'num_tier2_SV_variants': {'type': 'integer', 'required': True},
    'num_tier3_SV_variants': {'type': 'integer', 'required': True},
    'num_tier4_SV_variants': {'type': 'integer', 'required': True},
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
    'mrn_is_deceased': {'type': 'boolean'},

    # signatures
    'apobec_status': {'type': 'string', 'required': False},
    'apobec_sig_offlabel_therapies': {'type': 'list', 'required': False},
    'temo_trial_matches': {'type': 'list', 'required': False},
    'temo_sig_offlabel_therapies': {'type': 'list', 'required': False},
    'temo_sig_fda_therapies': {'type': 'list', 'required': False},
    'temozolomide_status': {'type': 'string', 'required': False},
    'tobacco_trial_matches': {'type': 'list', 'required': False},
    'tobacco_sig_offlabel_therapies': {'type': 'list', 'required': False},
    'tobacco_status': {'type': 'string', 'required': False},
    'tobacco_sig_fda_therapies': {'type': 'list', 'required': False},
    'uva_trial_matches': {'type': 'list', 'required': False},
    'uva_status': {'type': 'string', 'required': False},
    'uva_sig_fda_therapies': {'type': 'list', 'required': False},
    'uva_sig_offlabel_therapies': {'type': 'list', 'required': False},
    'apobec_sig_fda_therapies': {'type': 'list', 'required': False},
    'apobec_trial_matches': {'type': 'list', 'required': False},
    'pole_trial_matches': {'type': 'list', 'required': False},
    'pole_sig_offlabel_therapies': {'type': 'list', 'required': False},
    'pole_sig_fda_therapies': {'type': 'list', 'required': False},

    # sv
    'sv_trial_matches': {'allow_unknown': True, 'required': True},
    'sv_df': {'type': 'list', 'required': False},

    "apobec_fda_therapies": {'type': 'list', 'required': False},
    "apobec_offlabel_therapies": {'type': 'list', 'required': False},
    "block_no": {'type': 'string', 'required': False},
    "cnv_records": {'type': 'list', 'required': False},
    "mutation_records": {'type': 'list', 'required': False},
    "oncopanel_report_date": {'type': 'string', 'required': False},
    "pole_fda_therapies": {'type': 'list', 'required': False},
    "pole_offlabel_therapies": {'type': 'list', 'required': False},
    "sv_records": {'type': 'list', 'required': False},
    "temozolomide_fda_therapies": {'type': 'list', 'required': False},
    "temozolomide_offlabel_therapies": {'type': 'list', 'required': False},
    "tobacco_fda_therapies": {'type': 'list', 'required': False},
    "tobacco_offlabel_therapies": {'type': 'list', 'required': False},
    "trial_matches": {'type': 'dict', 'required': False},
    "uva_fda_therapies": {'type': 'list', 'required': False},
    "uva_offlabel_therapies": {'type': 'list', 'required': False},

    "prelim_report_generated": {'type': 'boolean', 'required': False}
}

gi_final_kb_schema = {

    # autopopulated columns
    'filename': {'type': 'string'},
    'initials': {'type': 'string'},
    'firstName': {'type': 'string'},
    'lastName': {'type': 'string'},
    'sampleId': {'type': 'string'},
    'mrn': {'type': 'string'},
    'ordPhysicianName': {'type': 'string'},
    'ProviderName': {'type': 'string'},
    'dateAdded': {'type': 'integer'},

    # manually populated columns
    'clinicalStatus': {'type': 'string'},
    'orderForMeeting':  {'type': 'string'},
    'reportSentToProviderDate': {'type': 'integer', 'nullable': True},

    # google form populated columns
    'formReviewed': {'type': 'boolean'},
    'meetingDate': {'type': 'integer', 'nullable': True},
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
    'formActive': {'type': 'boolean'},
    'emailRead': {'type': 'string'}
}

gi_kb1_schema = {
    'gene': {'type': 'string'},
    'variantCategory': {'type': 'string'},
    'variantDetails': {'type': 'string', 'nullable': True},
    'reviewer': {'type': 'string'},
    'dateAdded': {'type': 'integer', 'nullable': True},
    'dateRemoved': {'type': 'integer', 'nullable': True},
    'exclude': {'type': 'boolean', 'default': False},
    'geneClass': {'type': 'string', 'nullable': True}
}

gi_kb2_schema = {

    # autopopulated columns
    'gene': {'type': 'string'},
    'variantCategory': {'type': 'string'},
    'variantClassification': {'type': 'string'},
    'genomicChange': {'type': 'string'},
    'nucleotideChange': {'type': 'string'},
    'proteinChange': {'type': 'string'},
    'exon': {'type': 'integer', 'nullable': True},
    'transcript': {'type': 'string'},
    'tier1Count': {'type': 'integer', 'nullable': True},
    'tier2Count': {'type': 'integer', 'nullable': True},
    'tier3Count': {'type': 'integer', 'nullable': True},
    'tier4Count': {'type': 'integer', 'nullable': True},
    'dateAdded': {'type': 'integer', 'nullable': True},
    'assignedReviewer': {'type': 'string'},
    'cosmicLink': {'type': 'string'},
    'clinvarLink': {'type': 'string'},
    'unprotLink': {'type': 'string'},
    'oncokbLink': {'type': 'string'},
    'civicLink': {'type': 'string', 'nullable': True},
    'jaxLink': {'type': 'string', 'nullable': True},
    'myCancerGenomeLink': {'type': 'string', 'nullable': True},
    'formLink': {'type': 'string', 'default': ''},

    # manually populated columns
    'oncogenic': {'type': 'string'},
    'function': {'type': 'string'},
    'comments': {'type': 'string'},
    'pmids': {'type': 'string'},
    'needsToBeDiscussed': {'type': 'boolean', 'default': False},
    'discrepancyWithCAMDComment': {'type': 'boolean', 'default': False},

    # autopopulated after review columns
    'dateReviewed': {'type': 'integer', 'nullable': True},
    'reviewer': {'type': 'string'},

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
    'mutationClass': {'type': 'string', 'nullable': True},
    'cancerType': {'type': 'string'},
    'oncotreeCode': {'type': 'string', 'nullable': True},
    'FDAApprovedTherapy': {'type': 'string', 'nullable': True},
    'offLabelTherapy': {'type': 'string', 'nullable': True},
    'translationalResearch': {'type': 'string', 'nullable': True},
    'dateUpdated': {'type': 'integer'},
    'dateAdded': {'type': 'integer'}
}

gi_provider_kb_schema = {
    'lastName': {'type': 'string'},
    'firstName': {'type': 'string'},
    'middleInitial': {'type': 'string', 'nullable': True},
    'pilot': {'type': 'boolean', 'default': False},
    'npi': {'type': 'string'},
    'dateAdded': {'type': 'integer'}
}
