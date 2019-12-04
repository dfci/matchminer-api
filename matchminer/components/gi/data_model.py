gi_gold_standard_truth = {
    'mrn': {'type': 'string', 'required': True},
    'oncologist': {'type': 'string', 'required': False},
    'alterations': {'allow_unknown': True, 'required': False},
    'gi_report_date': {'type': 'string', "nullable": True},
    'review_date': {'type': 'string', 'nullable': True, 'required': False},
    'reviewers': {'type': 'string', 'nullable': True, 'required': False},

    # clinical data
    'sample_id': {'type': 'string', 'required': False},
    'provider_name': {'type': 'string', 'required': False},
    'provider_npi': {'type': 'integer', 'required': False},
    'clinical_id': {'type': 'string', 'required': False},
    'patient_name': {'type': 'string', 'required': False},
    'name': {'type': 'string', 'required': False},
    'patient_initials': {'type': 'string', 'required': False},
    'tumor_type': {'type': 'string', 'required': False},
    'tumor_type_meta': {'type': 'string', 'required': False, 'nullable': True},
    'disease_center': {'type': 'string', 'required': False},
    'physician': {'type': 'string', 'required': False},
    'report_date': {'type': 'string', 'required': False},
    'block_number': {'type': 'string', 'required': False},
    'panel_version': {'type': 'integer', 'required': False},
    'report_version': {'type': 'integer', 'required': False},
    'biopsy_site': {'type': 'string', 'required': False},
    'biopsy_site_type': {'type': 'string', 'required': False},
    'qc_result': {'type': 'string', 'required': False},
    'mean_sample_coverage': {'type': 'integer', 'required': False},
    'tumor_purity_per': {'type': 'float', 'required': False},
    'pdf_layout_version': {'type': 'integer', 'required': False},

    # genomic data
    'num_tier1_variants': {'type': 'integer', 'required': False},
    'num_tier2_variants': {'type': 'integer', 'required': False},
    'num_tier3_variants': {'type': 'integer', 'required': False},
    'num_tier4_variants': {'type': 'integer', 'required': False},
    'num_tier1_SV_variants': {'type': 'integer', 'required': False},
    'num_tier2_SV_variants': {'type': 'integer', 'required': False},
    'num_tier3_SV_variants': {'type': 'integer', 'required': False},
    'num_tier4_SV_variants': {'type': 'integer', 'required': False},
    'num_cnvs': {'type': 'integer', 'required': False},
    'num_actionable_cnvs': {'type': 'integer', 'required': False},
    'num_investigational_cnvs': {'type': 'integer', 'required': False},
    'num_cnv_regions': { 'type': 'integer', 'required': False},
    'num_actionable_cnv_regions': { 'type': 'integer', 'required': False},
    'num_investigational_cnv_regions': { 'type': 'integer', 'required': False},
    'mutation_df': {'allow_unknown': True, 'required': False},
    'cnv_df': {'allow_unknown': True, 'required': False},
    'sv_gene': {'allow_unknown': True, 'nullable': True},
    'filename': {'type': 'string'},
    'sv_fda_therapies': {'type': 'list', 'schema': {'allow_unknown': True}, 'required': False, 'nullable': True},
    'sv_offlabel_therapies': {'type': 'list', 'schema': {'allow_unknown': True}, 'required': False, 'nullable': True},
    'sv_comment': {'type': 'string', 'nullable': True},

    # mutational signature data
    'mmr_status': {'type': 'string', 'required': False},
    'pole_status': {'type': 'string', 'required': False},

    # mutational burden data
    'tmb': {'type': 'float', 'required': False},
    'all_profile_percentile': {'type': 'integer', 'required': False},
    'tumor_type_percentile': {'type': 'integer', 'required': False},
    'num_oncopanel': {'type': 'integer', 'required': False},
    'num_tumor_type_oncopanel': {'type': 'integer', 'required': False},

    # therapy data
    'sig_fda_therapies': {'type': 'list', 'schema': {'allow_unknown': True}, 'required': False},
    'sig_offlabel_therapies': {'type': 'list', 'schema': {'allow_unknown': True}, 'required': False},
    'summary': {'allow_unknown': True},

    # trial match data
    'sig_trial_matches': {'type': 'list', 'schema': {'allow_unknown': True}, 'required': False},
    'mutation_trial_matches': {'allow_unknown': True, 'required': False},
    'cnv_trial_matches': {'allow_unknown': True, 'required': False},
    'tmb_trial_matches': {'allow_unknown': True, 'required': False},
    'actionable_trial_matches': {'type': 'list', 'schema': {'allow_unknown': True}, 'required': False},
    'tier4_trial_matches': {'type': 'list', 'schema': {'allow_unknown': True}, 'required': False},

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
    'sv_trial_matches': {'allow_unknown': True, 'required': False},
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

    "prelim_report_generated": {'type': 'boolean', 'required': False},
    "final_report_generated": {'type': 'boolean', 'required': False},
    "sign_out_date": {'type': 'integer', 'required': False},
    "archived": {'type': 'boolean', 'required': False},
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
