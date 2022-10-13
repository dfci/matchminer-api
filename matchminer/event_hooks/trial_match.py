from flask import current_app as app


def sort_trial_matches(trial_matches):
    """
    In Matchengine V2, the sort order field is an array which delivers each dimension of the sort as an index.
    This function will sort each protocol's match reasons according to this criteria:

    MMR > Tier 1 > Tier 2 > CNV > Tier 3 > Tier 4 > wild type
    Variant-level  > gene-level
    Exact cancer match > all solid/liquid
    Co-ordinating center: DFCI > others
    Reverse protocol number: high > low

    There is also a field show_in_ui which determines whether a match document
    is viewable in the UI.
    """
    db = app.data.driver.db

    current_rank = 1
    seen_protocol_nos = dict()
    if trial_matches['_items'] and isinstance(trial_matches['_items'][0]['sort_order'], list):

        # get status of protocols. if trial is closed, don't count in ranking
        query = {"protocol_no": {"$in": [item['protocol_no'] for item in trial_matches['_items']]}}
        protocols = list(db.trial.find(query, {"_summary.status.value": 1, "protocol_no": 1}))
        protocol_statuses = {p['protocol_no']:p['_summary']['status'][0]['value'].lower() for p in protocols}

        trial_matches['_items'] = sorted(trial_matches['_items'], key=lambda x: (tuple(x['sort_order'][:-1]) + (1.0 / x['sort_order'][-1],)))
        for match in trial_matches['_items']:
            if match['protocol_no'] not in seen_protocol_nos:
                if any([x < 0 for x in match['sort_order']]) or \
                        protocol_statuses[match['protocol_no']] != 'open to accrual':
                    seen_protocol_nos[match['protocol_no']] = -1
                else:
                    seen_protocol_nos[match['protocol_no']] = current_rank
                    current_rank += 1
            match['sort_order'] = seen_protocol_nos[match['protocol_no']]
