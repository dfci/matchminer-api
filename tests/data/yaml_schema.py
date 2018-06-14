yaml_test_json = {
    "protocol_no": "00-001",
    "protocol_id": 0001,
    "principal_investigator": "pi",
    "long_title": "title",
    "short_title": "title",
    "status": "CLOSED TO ACCRUAL",
    "nct_id": "id",
    "age": "age",
    "phase": "I",
    "data_table4": "word",
    "protocol_type": "word",
    "protocol_target_accrual": 0,
    "cancer_center_accrual_goal_upper": 0,
    "site_list": {
        "site": [
            {
                "site_name": "site",
                "site_status": "CLOSED TO ACCRUAL",
                "uses_cancer_center_irb": "Y",
                "coordinating_center": "N"
            }
        ]
    },
    "treatment_list": {
        "step": [
            {
                "arm": [
                    {
                        "dose_level": [
                            {
                                "level_internal_id": 001,
                                "level_code": "code",
                                "level_description": "description",
                                "level_suspended": "Y",
                            }
                        ],
                        "arm_internal_id": 002,
                        "arm_code": "code",
                        "arm_description": "description",
                        "arm_suspended": "N"
                    },
                    {
                        "dose_level": [

                        ],
                        "arm_internal_id": 003,
                        "arm_code": "code",
                        "arm_description": "description",
                        "arm_suspended": "Y"
                    }
                ],
                "step_internal_id": 004,
                "step_code": "code",
                "step_type": "type"
            }
        ]
    },
    "oncology_group_list": {
        "oncology_group": [
            {
                "group_name": "group",
                "is_primary": "N"
            }
        ]
    },
    "drug_list": {
        "drug": [
            {
                "drug_name": "drug"
            }
        ]
    },
    "staff_list": {
        "protocol_staff": [
            {
                "first_name": "name",
                "last_name": "name",
                "middle_name": "name",
                "npi": "",
                "institution_name": "name",
                "staff_role": "role",
                "start_date": 0,
                "stop_date": 0
            }
        ]
    },
    "sponsor_list": {
        "sponsor": [
            {
                "sponsor_name": "sponsor",
                "sponsor_protocol_no": "sponsor",
                "is_principal_sponsor": "Y",
                "sponsor_roles": "sponsor"
            }
        ]
    },
    "disease_site_list": {
        "disease_site": [
            {
                "disease_site_name": "name",
                "disease_site_code": 0
            }
        ]
    },
    "program_area_list": {
        "program_area": [
            {
                "program_area_name": "name",
                "is_primary": "N"
            }
        ]
    },
    "management_group_list": {
        "management_group": [
            {
                "management_group_name": "name",
                "is_primary": "Y"
            }
        ]
    }
}
