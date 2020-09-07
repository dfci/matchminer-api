import logging
from matchminer.event_hooks.statistics import add_dashboard_row
from matchminer.miner import start_filter_run


def status_insert(items):
    """
    Re runs all filters (created in UI)
    :param items:
    :return:
    """
    dpi = None
    silent = False
    for item in items:

        # log this.
        logging.info("recieved pre-status post")

        if 'data_push_id' in item and item['data_push_id']:
            dpi = item['data_push_id']

        # adds a row to the MatchMiner Stats
        # dashboard datatable for the new CAMD update
        if not item['silent']:
            add_dashboard_row(item)
        else:
            silent = True

    if not silent:
        start_filter_run(silent=silent, datapush_id=dpi)
