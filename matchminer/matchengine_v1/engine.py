"""Copyright 2016 Dana-Farber Cancer Institute"""

from cerberus1 import schema_registry
import networkx as nx
import gc
import logging

from matchminer.matchengine_v1 import schema
from matchminer.matchengine_v1.validation import ConsentValidatorCerberus
from matchminer.matchengine_v1.utilities import *
from matchminer.matchengine_v1.sort import add_sort_order

# logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s: %(message)s', )

# modify schema for advanced recursive support (not yet supported in python-eve so it has to happen after the fact)
parent_schema_adv = schema.parent_schema.copy()
parent_schema_adv['children'] = {
    'type': 'list',
    'schema': {
        'type': 'dict',
        'schema': 'child_schema'
    }
}
parent_schema_adv['match'] = {
    'type': 'list',
    'schema': {
        'type': 'dict',
        'schema': 'yaml_match_schema'
    }
}
schema_registry.add('parent_schema', parent_schema_adv)
schema_registry.add('yaml_match_schema', schema.yaml_match_schema)
schema_registry.add('yaml_genomic_schema', schema.yaml_genomic_schema)
schema_registry.add('yaml_clinical_schema', schema.yaml_clinical_schema)
schema_registry.add('map', schema.map)


class MatchEngine(object):

    def __init__(self, db):
        # get the database.
        self.db = db

        # stores the complete list as easy lookup
        self.all_match = set(self.db.clinical.distinct('SAMPLE_ID'))

        # get mapping values between yml and db
        self.bootstrap_map()
        self.mapping = list(self.db.map.find())

        # add mmr/ms status mapping
        self.mapping.extend([
            {'key_old': 'MMR_STATUS', 'key_new': 'MMR_STATUS', 'values': {}},
            {'key_old': 'MS_STATUS', 'key_new': 'MMR_STATUS', 'values': {}}
        ])

    def bootstrap_map(self):
        """Loads the map into the database between yaml field names and their corresponding database field names"""

        # define the mapping
        key_map = {
            'AGE_NUMERICAL': 'BIRTH_DATE',
            'EXON': 'TRUE_TRANSCRIPT_EXON',
            'HUGO_SYMBOL': 'TRUE_HUGO_SYMBOL',
            'PROTEIN_CHANGE': 'TRUE_PROTEIN_CHANGE',
            'WILDCARD_PROTEIN_CHANGE': 'TRUE_PROTEIN_CHANGE',
            'ONCOTREE_PRIMARY_DIAGNOSIS': 'ONCOTREE_PRIMARY_DIAGNOSIS_NAME',
            'VARIANT_CLASSIFICATION': 'TRUE_VARIANT_CLASSIFICATION',
            'VARIANT_CATEGORY': 'VARIANT_CATEGORY',
            'CNV_CALL': 'CNV_CALL',
            'WILDTYPE': 'WILDTYPE',
            'GENDER': 'GENDER'
        }

        val_map = {
            'VARIANT_CATEGORY': {
                'Mutation': 'MUTATION',
                'Copy Number Variation': 'CNV',
                'Structural Variation': 'SV'
            },
            'CNV_CALL': {
                'Low Amplification': 'Gain',
                'High Amplification': 'High level amplification',
                'Homozygous Deletion': 'Homozygous deletion',
                'Heterozygous Deletion': 'Heterozygous deletion',
            },
            'WILDTYPE': {
                'true': True,
                'false': False
            }
        }

        # create collection
        mapping = []
        for old_key, new_key in list(key_map.items()):
            item = {
                'key_old': old_key,
                'key_new': new_key
            }
            if old_key in val_map:
                item['values'] = val_map[old_key]
            else:
                item['values'] = {}
            mapping.append(item)

        # add to db
        self.db.drop_collection("map")
        self.db.map.insert_many(mapping)

    @staticmethod
    def validate_yaml_format(data):
        """ check if yaml is in correct format

        :param data:
        :return:
        """
        # already loaded?
        if isinstance(data, dict):
            return 0, data

        # try to load
        try:
            data_json = yaml.safe_load(data)
            return 0, data_json
        except yaml.YAMLError as exc:
            return 1, exc

    def validate_yaml_data(self, data_json):
        """ Validates yaml specs

        :param data_json:
        :return:
        """

        v = ConsentValidatorCerberus(schema.parent_schema)
        v.validate(data_json)
        return v.errors

    @staticmethod
    def _test_type(data):
        ''' returns the type
        :param data:
        :return:
        '''

        # determine who this is.
        is_dict = isinstance(data, dict)
        is_list = isinstance(data, list)
        is_value = False
        if not is_dict and not is_list:
            is_value = True

        # return all these.
        return is_dict, is_list, is_value

    @staticmethod
    def create_match_tree(data):
        """
        Given json object of MATCH clause , the function returns a directed graph

        :param data: json match clause
        :return: diGraph match tree
        """

        key = list(data.keys())[0]
        value = data[key]
        global_node = 1
        g = nx.DiGraph()
        s = []
        s.append([0, global_node, key, value])

        while len(s) > 0:
            current = s.pop(0)
            parent = current[0]
            node = current[1]
            key = current[2]
            value = current[3]
            g.add_node(node)
            g.add_edges_from([(parent, node)])
            g.nodes[node]['type'] = key
            if isinstance(value, dict):
                g.nodes[node]['value'] = value
            elif isinstance(value, list):
                for i in range(0, len(value)):
                    global_node += 1
                    s.append([node, global_node, list(value[i].keys())[0], value[i][list(value[i].keys())[0]]])
        g.remove_node(0)
        return g

    def create_trial_tree(self, raw_data, no_validate=False):
        """ creates networkx tree of trial from a python dictionary
        :return:
        """

        # skip possibly.
        if not no_validate:

            # validate the schema.
            status, data = self.validate_yaml_format(raw_data)
            if status != 0:
                logging.error("invalid trial data")
                return 1, data

            # validate the schema.
            errors = self.validate_yaml_data(data)
            if len(errors) > 0:
                logging.error("schema error")
                return 2, errors

        else:
            data = raw_data

        # create the graph
        G = nx.DiGraph()

        # create the graph.
        self._recursive_create(None, data, G)
        self._annotate_match(G)

        # return the tree.
        return 0, G

    def run_query(self, node):
        """
        Runs genomic or clinical query against Mongo database and returns a set of sample ids that matched

        :param node: node location with the trial match tree
        :param db: database connection

        :returns
            matched_sample_ids: set of matched sample ids
            matched_genomic_info: genomic information regarding each match
        """

        matched_genomic_info = []

        # execute query against genomic table
        if node['type'] == 'genomic':

            item = node['value']

            # prepare genomic criteria
            g, neg, sv = self.prepare_genomic_criteria(item)

            # execute match
            if len(list(g.keys())) == 0:
                matched_sample_ids = list()
            else:

                if neg:
                    proj = {'SAMPLE_ID': 1}  # speeds up query
                else:
                    proj = {
                        'SAMPLE_ID': 1,
                        'TRUE_HUGO_SYMBOL': 1,
                        'TRUE_PROTEIN_CHANGE': 1,
                        'TRUE_VARIANT_CLASSIFICATION': 1,
                        'VARIANT_CATEGORY': 1,
                        'CNV_CALL': 1,
                        'WILDTYPE': 1,
                        'CHROMOSOME': 1,
                        'POSITION': 1,
                        'TRUE_CDNA_CHANGE': 1,
                        'REFERENCE_ALLELE': 1,
                        'TRUE_TRANSCRIPT_EXON': 1,
                        'CANONICAL_STRAND': 1,
                        'ALLELE_FRACTION': 1,
                        'TIER': 1,
                        'CLINICAL_ID': 1,
                        'MMR_STATUS': 1,
                        'ACTIONABILITY': 1,
                        '_id': 1
                    }

                    # record pathologist's chromosomal rearrangement comment for downstream manual analysis
                    if sv:
                        proj['STRUCTURAL_VARIANT_COMMENT'] = 1

                results = list(self.db.genomic.find(g, proj))

                # if a negative query was match, the formatted genomic alteration will reflect the trial criteria
                # and the genomic information will not be copied into the trial_match document
                if neg:

                    # If the yaml criterium was negative, then subtract the matched results from the total set
                    matched_sample_ids = self.all_match - set(x['SAMPLE_ID'] for x in results)
                    alteration, is_variant = format_not_match(g)

                    # add genomic alterations per sample id
                    matched_genomic_info = [{
                        'sample_id': sample_id,
                        'match_type': is_variant,
                        'genomic_alteration': alteration
                    } for sample_id in matched_sample_ids]

                else:
                    for item in results:

                        # format the genomic alteration that matched
                        alteration, is_variant = format_genomic_alteration(item, g)

                        # add genomic information and alterations that matched per sample id
                        genomic_info = {
                            'match_type': is_variant,
                            'genomic_alteration': alteration
                        }

                        # copy genomic document projection into match
                        for field in proj:
                            if field in item:
                                if field == '_id':
                                    genomic_info['genomic_id'] = item[field]
                                else:
                                    genomic_info[field.lower()] = item[field]

                        # add unique matches by sample id
                        matched_genomic_info.append(genomic_info)

                    matched_sample_ids = set(item['SAMPLE_ID'] for item in results)

        # execute query against clinical table
        elif node['type'] == 'clinical':

            item = node['value']

            # prepare clinical criteria
            c = self.prepare_clinical_criteria(item)

            # execute match
            if len(list(c.keys())) == 0:
                matched_sample_ids = list()
            else:
                matched_sample_ids = set(self.db.clinical.find(c).distinct('SAMPLE_ID'))

        else:
            logging.info("bad match tree")
            return

        # return a list of sample ids and match information
        return matched_sample_ids, matched_genomic_info

    def traverse_match_tree(self, g):
        """ Finds matches for a given match tree

        :param g: diGraph match tree
        :return: match set for a tree
        """

        tree_genomic = {}
        for node_id in list(nx.dfs_postorder_nodes(g, source=1)):

            # get node and its child
            node = g.nodes[node_id]
            successors = g.successors(node_id)

            # if leaf node then execute query
            if len(successors) == 0:
                matched_sample_ids, matched_genomic_info = self.run_query(node)

                node['matched_sample_ids'] = matched_sample_ids
                node['matched_genomic_info'] = matched_genomic_info

                for match in node['matched_genomic_info']:
                    if match['sample_id'] not in tree_genomic:
                        tree_genomic[match['sample_id']] = [match]
                    else:
                        tree_genomic[match['sample_id']].append(match)

            # else apply logic based on and/or
            else:

                node['matched_sample_ids'] = set([])
                node['matched_sample_ids'].update(g.nodes[successors[0]]['matched_sample_ids'])
                node['matched_genomic_info'] = g.nodes[successors[0]]['matched_genomic_info']

                for i in range(1, len(successors)):
                    s_list = g.nodes[successors[i]]['matched_sample_ids']

                    if node['type'] == 'and':
                        node['matched_sample_ids'].intersection_update(s_list)

                    elif node['type'] == 'or':
                        node['matched_sample_ids'].update(s_list)

        final_sample_ids = g.nodes[1]['matched_sample_ids']
        final_genomic_infos = [tree_genomic[i] for i in final_sample_ids]

        return final_sample_ids, final_genomic_infos

    def prepare_clinical_criteria(self, item):
        """
        Translates match criteria from yaml format into a Mongo query

        :param item: the match tree criteria for a given node in yaml format
        :return: Mongo query for clinical collection
        """

        c = {}

        # create the oncotree.
        onco_tree = build_oncotree()

        # only match by these keys
        map_keys = ["oncotree_primary_diagnosis", "age_numerical", "gender"]

        # all other keys are ignored when matching
        for key in list(item.keys()):
            if key.lower() not in map_keys:
                del item[key]

        for field in item:
            # this maps yaml field names to those stored in the database through the database collection "map"
            norm_field, _ = normalize_fields(self.mapping, field)
            txt = item[field]

            # this constructs the mongo query
            c = build_cquery(c, norm_field, txt)

        # stolen Jimbo's code for adding all the oncotree nodes
        if 'ONCOTREE_PRIMARY_DIAGNOSIS_NAME' in c:
            c['ONCOTREE_PRIMARY_DIAGNOSIS_NAME'] = self._search_oncotree_diagnosis(onco_tree, c)

        # translate yaml age restrictions into proper mongo query dates
        if 'BIRTH_DATE' in c:
            c['BIRTH_DATE'] = search_birth_date(c)

        return c

    def prepare_genomic_criteria(self, item):
        """
        Translates match criteria from yaml format into a Mongo query

        :param item: The match tree criteria for a given node in yaml format
        :return: Mongo query for genomic collection
        """

        g = {}
        track_neg = False
        track_sv = False
        wildtype = False

        # only map by these keys
        map_keys = ["hugo_symbol", "variant_category", "protein_change", "wildcard_protein_change",
                    "variant_classification", "exon", "cnv_call", "wildtype", "mmr_status", "ms_status"]

        # all other keys are ignored when matching
        for key in list(item.keys()):
            if key.lower() not in map_keys:
                del item[key]

            # determine if wildtype is specified by the trial. If not, query defaults to false
            if key.lower() == 'wildtype':
                wildtype = True

        for field, val in list(item.items()):

            # this maps the yaml field names to those stored in the database through the database collection "map"
            norm_field, norm_val = normalize_values(self.mapping, field, val)
            txt = norm_val

            # this constructs the mongo query
            key, txt, neg, sv = build_gquery(field, txt)

            # if any items in the yaml criteria are negative than the whole query is run negatively
            if neg and not track_neg:
                track_neg = True

            # keep track of if this query is on structural variants
            if sv and not track_sv:
                track_sv = True

            # update query
            g[norm_field] = {key: txt}

        # structural variants
        if track_sv:
            g = get_structural_variants(g)

        # If wildtype not specified, the query defaults to false
        if not wildtype:
            g = clean_query_for_msi(g)
            g = {'$and': [g, {'$or': [{'WILDTYPE': False}, {'WILDTYPE': {'$exists': False}}]}]}

        return g, track_neg, track_sv

    def find_trial_matches(self):
        """
        Iterates through all match clauses of all trials located in the database and matches patients to trials
        based on their clinical and genomic documents.

        :return: Dictionary containing matches
        """

        # all MRNs and trials in the database
        mrns = self.db.clinical.distinct('MRN')
        proj = {'protocol_no': 1, 'nct_id': 1, 'treatment_list': 1, '_summary': 1}
        all_trials = list(self.db.trial.find({}, proj))

        # create a map between sample id and MRN
        mrn_map = samples_from_mrns(self.db, mrns)

        # initialize trial matches
        trial_matches = []

        # for all trials check for matches on the dose, arm, and step levels and keep track of what is found
        for trial in all_trials:

            logging.info('Matching trial %s' % trial['protocol_no'])

            # If the trial is not open to accrual, all matches to all match trees in this trial will be marked closed
            trial_status = 'open'
            if '_summary' in trial:
                if 'status' in trial['_summary'] and isinstance(trial['_summary']['status'], list):
                    if 'value' in trial['_summary']['status'][0]:
                        if trial['_summary']['status'][0]['value'].lower() != 'open to accrual':
                            trial_status = 'closed'

            # STEP #
            for step in trial['treatment_list']['step']:
                if 'match' in step:
                    trial_matches = self._assess_match(mrn_map, trial_matches, trial, step, 'step', trial_status)

                # ARM #
                for arm in step['arm']:
                    if 'match' in arm:
                        trial_matches = self._assess_match(mrn_map, trial_matches, trial, arm, 'arm', trial_status)

                    # DOSE #
                    for dose in arm['dose_level']:
                        if 'match' in dose:
                            trial_matches = self._assess_match(mrn_map, trial_matches, trial, dose, 'dose',
                                                               trial_status)

        trial_match_df = pd.DataFrame.from_dict(trial_matches)

        # force garbage collector to remove unused object after conversion to df
        del trial_matches
        gc.collect()

        # sort
        logging.info('Sorting trial matches.')
        trial_matches_df = add_sort_order(trial_match_df)
        logging.info('Number of trial matches: %s' % str(trial_match_df.shape[0]))

        # add to db
        logging.info('Adding trial matches to database')
        add_matches(trial_matches_df, self.db)

    def _assess_match(self, mrn_map, trial_matches, trial, trial_segment, match_segment, trial_status):
        """
        Given a trial's match tree, finds all patients that matches to it and records the step, arm, or dose
        internal id that it matched to along with the genomic alteration that matched.

        :param mrn_map: Dictionary mapping patient sample ids to MRNs
        :param trial_matches: Dictionary containing the matches
        :param trial: Trial document
        :param trial_segment: Either the step, arm, or dose segment of the trial document
        :param match_segment: Marker indicating if segment is step, arm, or dose
        :param trial_status: Overall trial status. either open or closed.
        :return: Dictionary containing the matches
        """

        # get all matches
        match_tree = self.create_match_tree(trial_segment['match'][0])
        sample_ids, ginfos = self.traverse_match_tree(match_tree)

        clinical = []
        if sample_ids:
            cproj = {
                'SAMPLE_ID': 1,
                'ORD_PHYSICIAN_NAME': 1,
                'ORD_PHYSICIAN_EMAIL': 1,
                'ONCOTREE_PRIMARY_DIAGNOSIS_NAME': 1,
                'REPORT_DATE': 1,
                'VITAL_STATUS': 1,
                'FIRST_LAST': 1,
                'GENDER': 1,
                '_id': 1
            }
            clinical = list(self.db.clinical.find({'SAMPLE_ID': {'$in': list(sample_ids)}}, cproj))

        # add to master list if any sample ids matched
        for sample in ginfos:
            for alteration in sample:

                # add match document
                match = alteration
                match['mrn'] = mrn_map[alteration['sample_id']]
                match['match_level'] = match_segment
                match['trial_accrual_status'] = trial_status
                match['cancer_type_match'] = get_cancer_type_match(trial)
                match['coordinating_center'] = get_coordinating_center(trial)

                trial_keys = ['protocol_no', 'nct_id']
                for trial_key in trial_keys:
                    if trial_key in list(trial.keys()):
                        match[trial_key] = trial[trial_key]

                # copy clinical document
                if clinical:
                    for citem in clinical:
                        if citem['SAMPLE_ID'] == alteration['sample_id']:
                            for field in citem:
                                if field == '_id':
                                    match['clinical_id'] = citem[field]
                                else:
                                    match[field.lower()] = citem[field]

                # add internal id
                if match_segment == 'dose':
                    match['internal_id'] = str(trial_segment['level_internal_id'])
                    match['code'] = trial_segment['level_code']
                    if 'level_suspended' in trial_segment and trial_segment['level_suspended'].lower() == 'y':
                        match['trial_accrual_status'] = 'closed'
                elif match_segment == 'arm':
                    match['internal_id'] = str(trial_segment['arm_internal_id'])
                    match['code'] = str(trial_segment['arm_code'])
                    if 'arm_suspended' in trial_segment and trial_segment['arm_suspended'].lower() == 'y':
                        match['trial_accrual_status'] = 'closed'
                elif match_segment == 'step':
                    match['internal_id'] = str(trial_segment['step_internal_id'])
                    match['code'] = trial_segment['step_code']

                # add to trial_matches
                trial_matches.append(match)

        return trial_matches

    @staticmethod
    def _search_oncotree_diagnosis(onco_tree, c):
        """Add all the oncotree nodes """

        nodes = []
        tmpc = {'ONCOTREE_PRIMARY_DIAGNOSIS_NAME': {}}
        for key in list(c['ONCOTREE_PRIMARY_DIAGNOSIS_NAME'].keys()):

            # loop through all diagnoses
            diagnoses = c['ONCOTREE_PRIMARY_DIAGNOSIS_NAME'][key]
            if not isinstance(diagnoses, list):
                diagnoses = [diagnoses]

            for txt in diagnoses:
                if txt.endswith("_LIQUID_") or txt.endswith("_SOLID_"):

                    # build the nodes for liquid.
                    node1 = oncotreenx.lookup_text(onco_tree, "Lymph")
                    node2 = oncotreenx.lookup_text(onco_tree, "Blood")

                    nodes1 = list(nx.dfs_tree(onco_tree, node1))
                    nodes2 = list(nx.dfs_tree(onco_tree, node2))
                    nodes = list(set(nodes1).union(set(nodes2)))

                    # if its really solid take the inverse.
                    if txt == "_SOLID_":
                        all_nodes = set(list(onco_tree.nodes()))
                        tmp_nodes = all_nodes - set(nodes)
                        nodes = list(tmp_nodes)

                else:
                    # get tree node.
                    node = oncotreenx.lookup_text(onco_tree, txt)

                    # get its children.
                    if onco_tree.has_node(node):
                        # list of nodes.
                        nodes = list(nx.dfs_tree(onco_tree, node))

                        # replace it with free text.
                nodes_txt = [onco_tree.node[n]['text'] for n in nodes]

                if key == '$eq':
                    key = '$in'
                    tmpc['ONCOTREE_PRIMARY_DIAGNOSIS_NAME'][key] = nodes_txt
                elif key == '$ne':
                    key = '$nin'
                    tmpc['ONCOTREE_PRIMARY_DIAGNOSIS_NAME'][key] = nodes_txt
                elif key == '$in':
                    if '$in' in tmpc['ONCOTREE_PRIMARY_DIAGNOSIS_NAME']:
                        tmpc['ONCOTREE_PRIMARY_DIAGNOSIS_NAME']['$in'] += nodes_txt
                    else:
                        tmpc['ONCOTREE_PRIMARY_DIAGNOSIS_NAME']['$in'] = nodes_txt
                elif key == '$nin':
                    if '$nin' in tmpc['ONCOTREE_PRIMARY_DIAGNOSIS_NAME']:
                        tmpc['ONCOTREE_PRIMARY_DIAGNOSIS_NAME']['$nin'] += nodes_txt
                    else:
                        tmpc['ONCOTREE_PRIMARY_DIAGNOSIS_NAME']['$nin'] = nodes_txt

        # remove duplicates
        for k in tmpc['ONCOTREE_PRIMARY_DIAGNOSIS_NAME']:
            tmpc['ONCOTREE_PRIMARY_DIAGNOSIS_NAME'][k] = list(set(tmpc['ONCOTREE_PRIMARY_DIAGNOSIS_NAME'][k]))

        return tmpc['ONCOTREE_PRIMARY_DIAGNOSIS_NAME']

    def _recursive_create(self, parent_id, data, G):
        child_id_set = ['protocol_id', 'arm_internal_id', 'level_internal_id', 'step_internal_id']
        key_set = set(['treatment_list', 'step', 'arm', 'dose_level'])

        if parent_id is None:
            n = G.add_node(0)
            cur_name = 0
            G.graph['nidx'] = 1

        else:
            cur_name = G.graph['nidx']
            n = G.add_node(cur_name)
            G.graph['nidx'] += 1

            # connect to its parent.
            G.add_edge(parent_id, cur_name)

        # Add all other key/value to node
        for key, value in list(data.items()):
            if key in child_id_set:
                G.nodes[cur_name]['node_id'] = value
            if key not in key_set:
                # add the value.
                G.nodes[cur_name][key] = value

        # Add children level nodes to tree recursively
        for key in data:
            if key in key_set:
                if key == 'treatment_list':
                    list_val = data[key]['step']
                else:
                    list_val = data[key]

                for child_data in list_val:
                    self._recursive_create(cur_name, child_data, G)

    def _annotate_match(self, G):

        # loop over each node.
        for n in G.nodes():

            # skip no matchables.
            if 'match' not in G.nodes[n]:
                continue

            # create the match-tree.
            content = {'match': G.nodes[n]['match']}
            match_tree = self.create_match_tree(content)

            # embed it in trial tree.
            G.nodes[n]['match_tree'] = match_tree
