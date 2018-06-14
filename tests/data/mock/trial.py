# -*- coding: utf-8 -*-
on_trial = {
    "last_updated": "date",
    "curated_on": "date",
    "drug_list": {
        "drug": [
            {
                "drug_name": "drug"
            },
            {
                "drug_name": "drug"
            },
            {
                "drug_name": "drug"
            },
            {
                "drug_name": "drug"
            },
            {
                "drug_name": "drug"
            }
        ]
    },
    "status": "Open to Accrual",
    "prior_treatment_requirements": ["sentence"],
    "site_list": {
        "site": [
            {
                "site_status": "status",
                "uses_cancer_center_irb": "Y",
                "site_name": "name",
                "coordinating_center": "N"
            },
            {
                "site_status": "status",
                "uses_cancer_center_irb": "Y",
                "site_name": "name",
                "coordinating_center": "Y"
            }
        ]
    },
    "nct_purpose": "sentence",
    "oncology_group_list": {
        "oncology_group": [
            {
                "is_primary": "N",
                "group_name": "name"
            },
            {
                "is_primary": "N",
                "group_name": "name"
            }
        ]
    },
    "treatment_list": {
        "step": [
            {
                "step_internal_id": 01,
                "step_code": "code",
                "step_type": "type",
                "arm": [
                    {
                        "arm_suspended": "N",
                        "arm_code": "code",
                        "dose_level": [
                            {
                                "level_description": "description",
                                "level_suspended": "Y",
                                "level_code": "code",
                                "level_internal_id": 02
                            },
                            {
                                "level_description": "description",
                                "level_suspended": "Y",
                                "level_code": "code",
                                "level_internal_id": 03
                            },
                            {
                                "level_description": "description",
                                "level_suspended": "N",
                                "level_code": "code",
                                "level_internal_id": 04
                            },
                            {
                                "level_description": "description",
                                "level_suspended": "Y",
                                "level_code": "code",
                                "match": [
                                    {
                                        "and": [
                                            {
                                                "and": [
                                                    {
                                                        "or": [
                                                            {
                                                                "genomic": {
                                                                    "hugo_symbol": "MET",
                                                                    "cnv_call": "High Amplification",
                                                                    "variant_category": "Copy Number Variation"
                                                                }
                                                            },
                                                            {
                                                                "genomic": {
                                                                    "hugo_symbol": "MET",
                                                                    "variant_category": "Mutation",
                                                                    "protein_change": "p.V941L"
                                                                }
                                                            }
                                                        ]
                                                    },
                                                    {
                                                        "genomic": {
                                                            "hugo_symbol": "MET",
                                                            "variant_category": "Mutation",
                                                            "protein_change": "!p.Y1248C"
                                                        }
                                                    },
                                                    {
                                                        "genomic": {
                                                            "hugo_symbol": "MET",
                                                            "variant_category": "Mutation",
                                                            "protein_change": "!p.Y1248H"
                                                        }
                                                    }
                                                ]
                                            },
                                            {
                                                "clinical": {
                                                    "age_numerical": ">=18",
                                                    "oncotree_primary_diagnosis": "_SOLID_"
                                                }
                                            }
                                        ]
                                    }
                                ],
                                "level_internal_id": 04
                            },
                            {
                                "level_description": "description",
                                "level_suspended": "Y",
                                "level_code": "code",
                                "level_internal_id": 05
                            },
                            {
                                "level_description": "description",
                                "level_suspended": "Y",
                                "level_code": "code",
                                "level_internal_id": 06
                            },
                            {
                                "level_description": "description",
                                "level_suspended": "Y",
                                "level_code": "code",
                                "match": [
                                    {
                                        "and": [
                                            {
                                                "and": [
                                                    {
                                                        "or": [
                                                            {
                                                                "genomic": {
                                                                    "hugo_symbol": "MET",
                                                                    "cnv_call": "High Amplification",
                                                                    "variant_category": "Copy Number Variation"
                                                                }
                                                            },
                                                            {
                                                                "genomic": {
                                                                    "hugo_symbol": "MET",
                                                                    "variant_category": "Mutation",
                                                                    "protein_change": "p.L1213V"
                                                                }
                                                            }
                                                        ]
                                                    },
                                                    {
                                                        "genomic": {
                                                            "hugo_symbol": "MET",
                                                            "variant_category": "Mutation",
                                                            "protein_change": "!p.Y1248C"
                                                        }
                                                    },
                                                    {
                                                        "genomic": {
                                                            "variant_classification": "Splice_Site",
                                                            "hugo_symbol": "MET",
                                                            "exon": 14,
                                                            "variant_category": "Mutation"
                                                        }
                                                    }
                                                ]
                                            },
                                            {
                                                "clinical": {
                                                    "age_numerical": ">=18",
                                                    "oncotree_primary_diagnosis": "_SOLID_"
                                                }
                                            }
                                        ]
                                    }
                                ],
                                "level_internal_id": 07
                            },
                            {
                                "level_description": "description",
                                "level_suspended": "Y",
                                "level_code": "code",
                                "level_internal_id": 10
                            },
                            {
                                "level_description": "description",
                                "level_suspended": "Y",
                                "level_code": "code",
                                "level_internal_id": 11
                            }
                        ],
                        "arm_description": "description",
                        "arm_internal_id": 12
                    },
                    {
                        "arm_suspended": "Y",
                        "arm_code": "code",
                        "dose_level": [
                            {
                                "level_description": "description",
                                "level_suspended": "Y",
                                "level_code": "code",
                                "level_internal_id": 12
                            }
                        ],
                        "arm_description": "description",
                        "arm_internal_id": 13
                    }
                ]
            }
        ]
    },
    "nct_link": "url",
    "cancer_center_accrual_goal_upper": 1,
    "phase": "I",
    "oncpro_link": "url",
    "long_title": "title",
    "sponsor_list": {
        "sponsor": [
            {
                "is_principal_sponsor": "Y",
                "sponsor_roles": "sponsor",
                "sponsor_name": "sponsor",
                "sponsor_protocol_no": ""
            }
        ]
    },
    "protocol_type": "type",
    "nct_id": "id",
    "data_table4": "word",
    "program_area_list": {
        "program_area": [
            {
                "is_primary": "N",
                "program_area_name": "name"
            },
            {
                "is_primary": "N",
                "program_area_name": "name"
            }
        ]
    },
    "protocol_id": 0001,
    "principal_investigator": "PI",
    "disease_site_list": {
        "disease_site": [
            {
                "disease_site_name": "name",
                "disease_site_code": "code"
            },
            {
                "disease_site_name": "name",
                "disease_site_code": "code"
            },
            {
                "disease_site_name": "name",
                "disease_site_code": "code"
            }
        ]
    },
    "short_title": "title",
    "management_group_list": {
        "management_group": [
            {
                "is_primary": "N",
                "management_group_name": "name"
            }
        ]
    },
    "age": "age",
    "staff_list": {
        "protocol_staff": []
    },
    "protocol_no": "01-001",
    "protocol_target_accrual": 1,
    "match": [
        {
            "clinical": {
                "disease_status": [
                    "Advanced",
                    "Locally Advanced",
                    "Metastatic"
                ]
            }
        }
    ]
}