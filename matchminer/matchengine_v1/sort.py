"""Copyright 2016 Dana-Farber Cancer Institute"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s', )


def add_sort_order(trial_match_df):
    """
    Aggregate all the trial matches by MRN and provide a sort order using the following logic:
    (1) First sort by tier
    (2) Then sort by match_type (variant > gene)
    (3) Then sort by cancer type (specific cancer type > all solid/liquid)
    (4) Then sort by coordinating center (DFCI > MGH)
    (5) Then sort by reverse protocol number (high > low)

    :param trial_matches: List of trial match dictionaries
    :return: List of trial match dictionaries with two additional columns:
        (1) sort_order: Order in which to display the matches
        (2) freq: Frequency with which this trial match appears throughout the entire patient cohort
    """

    if len(trial_match_df.index) == 0:
        return trial_match_df

    f1 = (trial_match_df['vital_status'] == 'alive')
    f2 = (trial_match_df['trial_accrual_status'] == 'open')
    f3 = (trial_match_df['genomic_alteration'].str.strip().str.title() != 'Structural Variation')
    all_sample_ids = trial_match_df.sample_id.unique().tolist()
    master_sort_order = {}

    for sample_id in all_sample_ids:
        f4 = (trial_match_df['sample_id'] == sample_id)
        df = trial_match_df[f1 & f2 & f3 & f4]
        matches = list(df.T.to_dict().values())

        # The sort order dictionary keeps track of the priority for each sort category for each match
        # Index 0 is sorted by tier with values 0 to 7
        # Index 1 is sorted by match type with values 0 to 1
        # Index 2 is sorted by cancer type match with values 0 to 2
        # Index 3 is sorted by coordinating center with values 0 to 1
        # Index 4 is sorted by reverse protocol number
        sort_order = {}

        for match in matches:

            idx = (match['sample_id'], match['protocol_no'])
            if idx not in sort_order:
                sort_order[idx] = []

            sort_order = sort_by_tier(match, sort_order)
            sort_order = sort_by_match_type(match, sort_order)
            sort_order = sort_by_cancer_type(match, sort_order)
            sort_order = sort_by_coordinating_center(match, sort_order)

        sort_order = sort_by_reverse_protocol_no(matches, sort_order)

        # for k, v in sort_order.iteritems():
        #     print '%s | %s' % (k, v)

        master_sort_order = final_sort(sort_order, master_sort_order)

    trial_match_df['sort_order'] = trial_match_df.apply(lambda x: master_sort_order[(x['sample_id'], x['protocol_no'])]
                                                        if (x['sample_id'], x['protocol_no']) in master_sort_order
                                                        else -1, axis=1)
    return trial_match_df


def sort_by_tier(match, sort_order):
    """
    Highest priority sorting
    """

    idx = (match['sample_id'], match['protocol_no'])

    if 'mmr_status' in match and pd.notnull(match['mmr_status']):
        sort_order[idx] = add_sort_value(sort_value=0,
                                         priority=0,
                                         sort_order_li=sort_order[idx])

    elif 'tier' in match and match['tier'] == 1:
        sort_order[idx] = add_sort_value(sort_value=1,
                                         priority=0,
                                         sort_order_li=sort_order[idx])

    elif 'tier' in match and match['tier'] == 2:
        sort_order[idx] = add_sort_value(sort_value=2,
                                         priority=0,
                                         sort_order_li=sort_order[idx])

    elif 'variant_category' in match and match['variant_category'] == 'CNV':
        sort_order[idx] = add_sort_value(sort_value=3,
                                         priority=0,
                                         sort_order_li=sort_order[idx])

    elif 'tier' in match and match['tier'] == 3:
        sort_order[idx] = add_sort_value(sort_value=4,
                                         priority=0,
                                         sort_order_li=sort_order[idx])

    elif 'tier' in match and match['tier'] == 4:
        sort_order[idx] = add_sort_value(sort_value=5,
                                         priority=0,
                                         sort_order_li=sort_order[idx])

    elif 'wildtype' in match and match['wildtype'] is True:
        sort_order[idx] = add_sort_value(sort_value=6,
                                         priority=0,
                                         sort_order_li=sort_order[idx])

    else:
        sort_order[idx] = add_sort_value(sort_value=7,
                                         priority=0,
                                         sort_order_li=sort_order[idx])

    return sort_order


def sort_by_match_type(match, sort_order):
    """
    Second highest priority sorting
    """

    idx = (match['sample_id'], match['protocol_no'])

    if 'match_type' in match and match['match_type'] == 'variant':
        sort_order[idx] = add_sort_value(sort_value=0,
                                         priority=1,
                                         sort_order_li=sort_order[idx])

    elif 'match_type' in match and match['match_type'] == 'gene':
        sort_order[idx] = add_sort_value(sort_value=1,
                                         priority=1,
                                         sort_order_li=sort_order[idx])
    else:
        sort_order[idx] = add_sort_value(sort_value=2,
                                         priority=1,
                                         sort_order_li=sort_order[idx])

    return sort_order


def sort_by_cancer_type(match, sort_order):
    """
    Third highest priority sorting
    """

    idx = (match['sample_id'], match['protocol_no'])

    if 'cancer_type_match' in match and match['cancer_type_match'] == 'specific':
        sort_order[idx] = add_sort_value(sort_value=0,
                                         priority=2,
                                         sort_order_li=sort_order[idx])

    elif 'cancer_type_match' in match and match['cancer_type_match'] == 'all_solid':
        sort_order[idx] = add_sort_value(sort_value=1,
                                         priority=2,
                                         sort_order_li=sort_order[idx])

    elif 'cancer_type_match' in match and match['cancer_type_match'] == 'all_liquid':
        sort_order[idx] = add_sort_value(sort_value=1,
                                         priority=2,
                                         sort_order_li=sort_order[idx])

    else:
        sort_order[idx] = add_sort_value(sort_value=2,
                                         priority=2,
                                         sort_order_li=sort_order[idx])

    return sort_order


def sort_by_coordinating_center(match, sort_order):
    """
    Fourth highest priority sorting
    """

    idx = (match['sample_id'], match['protocol_no'])

    if 'coordinating_center' in match and match['coordinating_center'] == 'Dana-Farber Cancer Institute':
        sort_order[idx] = add_sort_value(sort_value=0,
                                         priority=3,
                                         sort_order_li=sort_order[idx])
    else:
        sort_order[idx] = add_sort_value(sort_value=1,
                                         priority=3,
                                         sort_order_li=sort_order[idx])

    return sort_order


def sort_by_reverse_protocol_no(matches, sort_order):
    """
    Lowest priority sorting
    """

    rev_prot_no_sort = sorted(matches, key=lambda k: int(k['protocol_no'].split('-')[0]))
    i = 0

    for match in rev_prot_no_sort[::-1]:

        if len(sort_order[(match['sample_id'], match['protocol_no'])]) == 4:
            sort_order[(match['sample_id'], match['protocol_no'])].append(i)
            i += 1

    return sort_order


def final_sort(sort_order, master_sort_order):

    cols = ['tier', 'match_type', 'cancer_type', 'coordinating_center', 'rev_protocol_no']
    sort_order_df = pd.DataFrame(list(sort_order.values()), columns=cols, index=list(sort_order.keys()))
    sort_order_df.sort_values(by=cols, axis=0, ascending=True, inplace=True)

    j = 0
    for idx, row in sort_order_df.iterrows():
        master_sort_order[idx] = j
        j += 1

    return master_sort_order


def add_sort_value(sort_value, priority, sort_order_li):
    """
    Adds the sort value, independent of the logic required to assess and determine that value.
    Accepts the lowest sort_value when there are multiple matches.

    :param sort_value: Integer value that determines sort order
    :param priority: Integer that determines which column to assign the sort value
        (e.g. tier, match_type, etc.)
    :param sort_order_li: The match-specific sort order list so far
    """

    if len(sort_order_li) >= priority + 1:

        if sort_value < sort_order_li[priority]:
            sort_order_li[priority] = sort_value
    else:
        sort_order_li.append(sort_value)

    return sort_order_li
