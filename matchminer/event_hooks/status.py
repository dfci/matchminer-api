import logging

from matchminer.event_hooks.statistics import add_dashboard_row
from matchminer.miner import start_filter_run


def status_insert(items):
    """
    # TODO remove endpoint and have services call rerun_filters endpoint with flag set
    to indiciate datapush run
    Re runs all filters (created in UI)
    :param items:
    :return:
    """

    for item in items:
        logging.info("recieved status post")

        # adds a row to the MatchMiner Stats
        # dashboard datatable for the new CAMD update
        if not item['silent']:
            add_dashboard_row(item)


