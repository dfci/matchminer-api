# imports
import logging

from matchminer.event_hooks.clinical import hide_name, clinical_replace, clinical_update, clinical_delete, clinical_insert, \
    align_other_clinical, align_matches_clinical
from matchminer.event_hooks.event_utils import dry_flag, entry_insert, entry_replace
from matchminer.event_hooks.genomic import negative_genomic, genomic_insert, align_matches_genomic
from matchminer.event_hooks.hipaa import hipaa_logging_item, hipaa_logging_resource
from matchminer.event_hooks.immunoprofile import immunoprofile_insert
from matchminer.event_hooks.public_stats import get_public_stats
from matchminer.event_hooks.trial_match import sort_trial_matches
from matchminer import settings
from matchminer.event_hooks.match import add_filter_run_id
from matchminer.miner import transform_filter_to_CTML, find_filter_matches, update_filter_post, \
    update_filter_pre
from matchminer.event_hooks.patient_view import patient_view_post
from matchminer.security import pre_get_restricted, team_restricted_item
from matchminer.event_hooks.status import status_insert
from matchminer.event_hooks.trial import trial_insert, trial_replace
from matchminer.event_hooks.user import email_user

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', )


def register_hooks(app):
    """
    Register global and resource level hooks for eve's auto generated
    endpoints.

    Documentation: https://docs.python-eve.org/en/stable/features.html
    :param app:
    :return:
    """

    ##############
    # Global
    ##############
    app.on_insert += dry_flag
    app.on_insert += entry_insert
    app.on_replace += entry_replace
    app.on_fetched_item += hipaa_logging_item
    app.on_fetched_resource += hipaa_logging_resource

    ###############
    # Endpoint hooks
    # Documentation: https://docs.python-eve.org/en/stable/features.html
    ###############
    # clinical
    app.on_insert_clinical += clinical_insert
    app.on_replace_clinical += clinical_replace
    app.on_update_clinical += clinical_update
    app.on_delete_item_clinical += clinical_delete
    app.on_fetched_item_clinical += align_matches_clinical
    app.on_fetched_item_clinical += align_other_clinical
    app.on_fetched_resource_clinical += hide_name

    # genomic
    app.on_fetched_resource_genomic += align_matches_genomic
    app.on_insert_genomic += genomic_insert
    app.on_insert_negative_genomic += negative_genomic

    # immunoprofile
    app.on_insert_immunoprofile += immunoprofile_insert

    # Disable team auth when in dev mode
    if settings.NO_AUTH is False:
        app.on_fetched_item_filter += team_restricted_item
        app.on_pre_GET_filter += pre_get_restricted
        app.on_fetched_item_match += team_restricted_item
        app.on_pre_GET_match += pre_get_restricted

    # match
    app.on_replace_match += add_filter_run_id

    # public_status
    app.on_fetched_resource_public_stats += get_public_stats

    # patient_view
    app.on_insert_patient_view += patient_view_post

    # filter
    app.on_insert_filter += transform_filter_to_CTML
    app.on_inserted_filter += find_filter_matches
    app.on_replace_filter += update_filter_pre
    app.on_replaced_filter += update_filter_post

    # trial
    app.on_insert_trial += trial_insert
    app.on_update_trial += trial_replace
    app.on_replace_trial += trial_replace

    # trial_match
    app.on_fetched_resource_trial_match += sort_trial_matches

    # status
    app.on_insert_status += status_insert

    # user
    app.on_inserted_user += email_user
    return app
