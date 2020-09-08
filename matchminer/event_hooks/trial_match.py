def sort_trial_matches(resource):
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
    current_rank = 0
    seen_protocol_nos = dict()
    if resource['_items'] and isinstance(resource['_items'][0]['sort_order'], list):
        resource['_items'] = sorted(resource['_items'], key=lambda x: (tuple(x['sort_order'][:-1]) + (1.0 / x['sort_order'][-1],)))
        for item in resource['_items']:
            if item['protocol_no'] not in seen_protocol_nos:
                if any([x < 0 for x in item['sort_order']]):
                    seen_protocol_nos[item['protocol_no']] = -1
                else:
                    seen_protocol_nos[item['protocol_no']] = current_rank
                    current_rank += 1
            item['sort_order'] = seen_protocol_nos[item['protocol_no']]
