import logging

from matchminer.elasticsearch import *
from matchminer.matchengine_v1.engine import MatchEngine
from matchminer.trial_search import Summary, Autocomplete


def insert_data_other(trial_tree, node_id, n, other):

    # set valid keys
    valid_keys = {'phase', 'status', 'age'}
    fields = {'site_list': ['site_name', 'coordinating_center'],
              'management_group_list': ['management_group_name', 'is_primary']}
    institute_name = 'Dana-Farber Cancer Institute'
    closed_status = ['Closed to Accrual', 'Suspended', 'Terminated']

    # add other values
    for key, val in trial_tree.nodes[n].items():

        # skip hidden.
        if key[0] == '_' or key not in valid_keys:
            continue

        # bootstrap
        if key not in other:
            other[key] = []

        # search for key
        found = False
        for x in other[key]:
            if x['value'] == val:
                x['id'].append(node_id)
                found = True
                break

        # add it otherwise.
        if not found:
            other[key].append({'value': val, 'id': [node_id]})

    # populate disease center and Study Site (special because only once)
    for key in fields:
        try:
            val = next(iter(trial_tree.nodes[n][key].keys()))
            # iterate through the list
            for name in trial_tree.nodes[n][key][val]:
                # check if primary site or coordinating center
                if name[fields[key][1]] == 'N':
                    continue
                value = name[fields[key][0]]
                other[val] = [{'value': value, 'id': [node_id]}]
        except KeyError:
            pass

    # Get Dana Farber accrual status. Overrides overall status, unless overall status is closed.
    try:
        site_status = ''
        for sites in trial_tree.nodes[n]['site_list']['site']:
            site_name = sites['site_name']
            if site_name == institute_name:
                site_status = sites['site_status']

        if other['status'] not in closed_status and site_status != '':
            other['status'] = [{'value': site_status, 'id': [node_id]}]
    except KeyError:
        pass

    # populate Drug names
    try:
        if trial_tree.nodes[n]['drug_list']:
            for drugs in trial_tree.nodes[n]['drug_list']['drug']:
                if 'drug' not in other:
                    other['drug'] = []
                other['drug'].append({'value': drugs['drug_name'], 'id': node_id})
    except KeyError:
        pass


def insert_data_clinical(data_dict, tree_node, node_id):

    # loop over every value.
    for key, val in tree_node.items():

        # bootstrap
        if key not in data_dict:
            data_dict[key] = []

        # search for key
        found = False
        for x in data_dict[key]:
            if x['value'] == val:
                x['id'].append(node_id)
                found = True
                break

        # add value to dictionary.
        if not found:
            data_dict[key].append({'value': val, 'id': [node_id]})


def trial_insert(items):
    build_trial_elasticsearch_fields(items)

    for item in items:
        put_prepared_trial_in_elasticsearch(prepare_for_es(item))

    return items


def build_trial_elasticsearch_fields(items):
    """
    Create '_elasticsearch,' '_suggest' and '_summary' fields on trial documents.

    Normalize oncotree diagnoses fields using 'normalized' collection in db

    :param items:
    :return:
    """
    # get database connection.
    db = database.get_db()

    # loop over each item.
    for item in items:

        # build tree.
        me = MatchEngine(db)
        status, trial_tree = me.create_trial_tree(item, no_validate=True)

        # look at every node.
        genomic = {}
        clinical = {}
        other = {}
        for n in trial_tree.nodes():

            # get parent.
            if 'node_id' not in trial_tree.nodes[n]:
                continue

            node_id = trial_tree.nodes[n]['node_id']

            # look for multi-level nodes (right now its only match).
            if 'match_tree' in trial_tree.nodes[n]:
                # compress categories.
                mt = trial_tree.nodes[n]['match_tree']
                for x in mt:
                    if mt.nodes[x]['type'] == 'genomic':
                        insert_data_genomic(genomic, mt.nodes[x]['value'], node_id)
                    if mt.nodes[x]['type'] == 'clinical':
                        insert_data_clinical(clinical, mt.nodes[x]['value'], node_id)

            # add the other nodes.
            insert_data_other(trial_tree, node_id, n, other)

        # create _summary, _suggest, and _elasticsearch fields
        summary = Summary(clinical, genomic, other, trial_tree)
        item['_summary'] = summary.create_summary(item)

        autocomplete = Autocomplete(item)
        item['_suggest'], item['_elasticsearch'], item['_summary']['primary_tumor_types'] = \
            autocomplete.add_autocomplete()

        logging.info("trial inserted " + item['protocol_no'])

    logging.info("inserting trials to elasticsearch " + str([item.setdefault("protocol_no") for item in items]))


def trial_replace(item, original):
    remove_trial_from_elasticsearch_by_es_id(item.setdefault("protocol_no"))
    logging.info(f"trial updated {item['protocol_no']}")
    trial_insert([item])


def insert_data_genomic(data_dict, tree_node, node_id):

    # deal with other genomics
    for key, val in tree_node.items():

        # dont need to compress this.
        if key == "wildtype":
            continue

        # modify to special wildtype facet
        if 'wildtype' in tree_node and key == "hugo_symbol":
            key = "wildtype_%s" % key
            val = "wt %s" % val

        # bootstrap
        if key not in data_dict:
            data_dict[key] = []

        # search for key.
        found = False
        for x in data_dict[key]:
            if x['value'] == val:
                x['id'].append(node_id)
                found = True
                break

        # add value to dictionary.
        if not found:
            data_dict[key].append({'value': val, 'id': [node_id]})
