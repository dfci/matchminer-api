import oncotreenx
import pandas as pd
import networkx as nx

from matchminer.settings import TUMOR_TREE
from matchengine.engine import MatchEngine
from database import get_db


class Summary:

    def __init__(self, clinical, genomic, other, trial_tree):

        self.clinical = clinical
        self.genomic = genomic
        self.other = other
        self.trial_tree = trial_tree

        self.genes = []
        self.nonsynonymous_genes = []
        self.nonsynonymous_wt_genes = []
        self.tumor_types = []
        self.disease_status = []
        self.disease_center = ''
        self.dfci_investigator = None
        self.mmr = []
        self.ms = []
        self.hr = []
        self.sigs = []
        self.status = []

        self.summary_dict = {
            'age': '',
            'phase': '',
            'nct_id': '',
            'protocol_no': '',
            'principal_investigator': '',
            'cancer_center_accrual_goal_upper': '',
            'center': '',
            'sponsor': '',
            'drugs': '',
            'site': ''
        }

    def _get_genes(self):
        """
        Separates genes, wildtype genes, and their synonymous into separate summary lists fo ElasticSearch querying
        """

        if 'hugo_symbol' in self.genomic:
            genes = [gene['value'] for gene in self.genomic['hugo_symbol']]
            self.genes.extend(genes)
            self.nonsynonymous_genes = genes
        if 'wildtype_hugo_symbol' in self.genomic:
            wt_genes = [wt['value'] for wt in self.genomic['wildtype_hugo_symbol']]
            self.genes.extend(wt_genes)
            self.nonsynonymous_wt_genes = wt_genes

    def _get_tumor_types(self):
        """
        Prepends hormone receptor status to the tumor types
        """

        hrs_map = {'Positive': '+', 'Negative': '-'}
        for n in self.trial_tree.nodes():
            # look for multi-level nodes (right now its only match).
            if 'match_tree' in self.trial_tree.node[n]:
                # compress categories.
                mt = self.trial_tree.node[n]['match_tree']
                for x in mt:

                    er = False
                    pr = False
                    her = False
                    if mt.node[x]['type'] == 'clinical':
                        node = mt.node[x]['value']
                        if 'oncotree_primary_diagnosis' in mt.node[x]['value']:

                            if node['oncotree_primary_diagnosis'][0] != '!':

                                badge = node['oncotree_primary_diagnosis']
                                if 'er_status' in node and node['er_status'] != 'Unknown':
                                    er = True
                                    badge += ' ER%s' % hrs_map[node['er_status']]

                                if 'pr_status' in node and node['pr_status'] != 'Unknown':
                                    pr = True
                                    if er:
                                        badge += '/PR%s' % hrs_map[node['pr_status']]
                                    else:
                                        badge += ' PR%s' % hrs_map[node['pr_status']]

                                if 'her2_status' in node and node['her2_status'] != 'Unknown':
                                    if not er and not pr:
                                        badge += ' HER2%s' % hrs_map[node['her2_status']]
                                    else:
                                        badge += '/HER2%s' % hrs_map[node['her2_status']]

                                self.tumor_types.append(badge)

    def _get_disease_status(self):
        """
        Create a summary list of all disease statuses
        """

        if 'disease_status' in self.clinical:
            for dis in self.clinical['disease_status']:
                self.disease_status += dis['value']

    def _get_disease_center(self):
        """
        Create a summary list of all disease centers
        """

        if 'management_group' in self.other:
            self.disease_center = self.other['management_group'][0]['value'].replace(
                'DF/HCC TPETT', 'DF/HCC Early Drug Discovery Center (EDDC)').replace(
                'DF/HCC EDDC', 'DF/HCC Early Drug Discovery Center (EDDC)'
            )

    def _get_misc_fields(self, item):
        """
        Generic rules for creating summary lists of several miscellaneous fields

        :param item: ```dictionary``` Trial details
        """

        for field in self.summary_dict.keys():
            if field in item:
                self.summary_dict[field] = item[field]

        self.summary_dict['principal_investigator'] = self.summary_dict['principal_investigator'].title()

        if 'site_list' in item and 'site' in item['site_list']:
            centers = [site['site_name'] for site in item['site_list']['site'] if site['coordinating_center'] == "Y"]
            if len(centers) > 0:
                self.summary_dict['site'] = centers[0]
                self.summary_dict['center'] = centers[0]

        if 'sponsor_list' in item and 'sponsor' in item['sponsor_list']:
            sponsors = [s['sponsor_name'] for s in item['sponsor_list']['sponsor'] if s['is_principal_sponsor'] == "Y"]
            if len(sponsors) > 0:
                self.summary_dict['sponsor'] = sponsors[0]

        if 'drug_list' in item and 'drug' in item['drug_list']:
            self.summary_dict['drugs'] = [drug['drug_name'].replace('(', '').replace(')', '')
                                          for drug in item['drug_list']['drug']]

    def _get_dfci_investigator(self, item):
        """
        Create DFCI Investigator entry

        :param item: Trial document
        """

        if 'staff_list' not in item or 'protocol_staff' not in item['staff_list']:
            return

        # return DFCI site principal investigator
        for staff in item['staff_list']['protocol_staff']:
            if staff['staff_role'] == 'Site Principal Investigator' and \
                    staff['institution_name'] == 'Dana-Farber Cancer Institute':
                self.dfci_investigator = parse_dfci_investigator(staff, item['principal_investigator'])
                return

        # if not present, return DFCI overall principal investigator
        for staff in item['staff_list']['protocol_staff']:
            if staff['staff_role'] == 'Overall Principal Investigator' and \
                    staff['institution_name'] == 'Dana-Farber Cancer Institute':
                self.dfci_investigator = parse_dfci_investigator(staff, item['principal_investigator'])
                return

        # if not present, return overall principal investigator at BWH or Beth Israel
        for staff in item['staff_list']['protocol_staff']:
            if staff['staff_role'] == 'Overall Principal Investigator' and \
                    staff['institution_name'] in ["Brigham and Women's Hospital",
                                                  "Beth Israel Deaconess Medical Center"]:
                self.dfci_investigator = parse_dfci_investigator(staff, item['principal_investigator'], dfci=False)
                return

        # if not present, return overall principal investigator, regardless of affiliated institution
        for staff in item['staff_list']['protocol_staff']:
            if staff['staff_role'] == 'Overall Principal Investigator':
                self.dfci_investigator = parse_dfci_investigator(staff, item['principal_investigator'], dfci=False)
                return

    def _get_signatures(self, item):
        """
        Creates hormone receptor status and mutational signature summary lists

        :param item: Trial document
        """

        m = MatchEngine(get_db())
        for step in item['treatment_list']['step']:
            if 'match' in step:
                g = m.create_match_tree(step['match'][0])
                pmt = ParseMatchTree(g)
                signatures = pmt.extract_signatures()
                self.mmr.extend(signatures[0])
                self.ms.extend(signatures[1])
                self.sigs.extend(signatures[2])
                self.hr.extend(pmt.extract_hr_status())

            if 'arm' in step:
                for arm in step['arm']:
                    if 'match' in arm:
                        g = m.create_match_tree(arm['match'][0])
                        pmt = ParseMatchTree(g)
                        signatures = pmt.extract_signatures()
                        self.mmr.extend(signatures[0])
                        self.ms.extend(signatures[1])
                        self.sigs.extend(signatures[2])
                        self.hr.extend(pmt.extract_hr_status())

                    if 'dose_level' in arm:
                        for dose in arm['dose_level']:
                            if 'match' in dose:
                                g = m.create_match_tree(dose['match'][0])
                                pmt = ParseMatchTree(g)
                                signatures = pmt.extract_signatures()
                                self.mmr.extend(signatures[0])
                                self.ms.extend(signatures[1])
                                self.sigs.extend(signatures[2])
                                self.hr.extend(pmt.extract_hr_status())

    def _get_status(self):
        """
        Get trial status

        :param item: Trial info
        """

        if 'status' in self.other:
            self.status = self.other['status']
            self.status[0]['value'] = self.other['status'][0]['value']. \
                replace('OPEN TO ACCRUAL', 'Open to Accrual'). \
                replace('CLOSED TO ACCRUAL', 'Closed to Accrual'). \
                replace('IRB STUDY CLOSURE', 'IRB Study Closure'). \
                replace('SUSPENDED', 'Suspended')

    def create_summary(self, item):
        """
        Creates the summary object for each trial

        :param item: ```Dictionary``` Entire trial collection
        :param clinical: ```Dictionary``` Aggregated clinical information
        :param other: ```Dictionary``` Aggregated metadata
        """

        self._get_genes()
        self._get_tumor_types()
        self._get_disease_status()
        self._get_disease_center()
        self._get_misc_fields(item)
        self._get_dfci_investigator(item)
        self._get_signatures(item)
        self._get_status()

        item = {
            'mmr_status': list(set(self.mmr)),
            'ms_status': list(set(self.ms)),
            'mutational_signatures': list(set(self.mmr + self.ms + self.sigs)),
            'dfci_investigator': self.dfci_investigator,
            'investigator': self.summary_dict['principal_investigator'],
            'protocol_number': self.summary_dict['protocol_no'],
            'coordinating_center': self.summary_dict['center'],
            'sponsor': self.summary_dict['sponsor'],
            'phase_summary': self.summary_dict['phase'],
            'genes': list(set(self.genes)),
            'disease_status': list(set(self.disease_status)),
            'tumor_types': list(set(self.tumor_types)),
            'drugs': list(set(self.summary_dict['drugs'])),
            'nct_number': self.summary_dict['nct_id'],
            'disease_center': self.disease_center.strip(),
            'accrual_goal': self.summary_dict['cancer_center_accrual_goal_upper'],
            'age_summary': self.summary_dict['age'],
            'nonsynonymous_genes': self.nonsynonymous_genes,
            'nonsynonymous_wt_genes': self.nonsynonymous_wt_genes,
            'short_title': item['short_title'],
            'hormone_receptor_status': list(set(self.hr)),
            'status': self.status,
            'site': self.summary_dict['site']
        }

        return item


class Autocomplete:

    def __init__(self, item):
        """
        Creates data for ElasticSearch's autocomplete index

        :param item: Trial info:
                    - treatment_list: Nested dictionary containing all match criteria
                    - summary:        Summary object created by the API
        """
        self.summary = item['_summary']
        self.treatment_list = item['treatment_list']

        self.vdict = {
            'variants': [],
            'wts': [],
            'svs': [],
            'cnvs': [],
            'exclusions': []
        }
        self.genes = []
        self.cancer_type_dict = dict()
        self.m = MatchEngine(get_db())

    @staticmethod
    def _get_cancer_type_weight(cancer_type, hierarchy='default'):
        """
        Sets the weights for ElasticSearch autocompletion on cancer types. Cancer type terms
        are split so that autocomplete suggestions will populate regardless of which word in the
        multi-word cancer type string is initially input. Higher weighted terms will populate the
        top of the autocomplete dropdown list.

        :param cancer_type: Text to display in the autocomplete dropdown list.
        :param hierarchy: Weight to give the text.
        :return: Dictionary specifying ElasticSearch rules.
        """

        weight_dict = {'primary': 10, 'default': 5, 'bucket': 20}
        if cancer_type == 'All Solid Tumors' or cancer_type == 'All Liquid Tumors':
            hierarchy = 'bucket'

        return {
            'input': list(set([cancer_type] + [i for i in cancer_type.split() if len(i) > 3])),
            'output': cancer_type,
            'weight': weight_dict[hierarchy]
        }

    @staticmethod
    def _get_variants_weight(variant, esrule='variants'):
        """
        Sets the weights for ElasticSearch autocompletion on gene variants. Higher weighted terms will populate the
        top of the autocomplete dropdown list.

        :param variant: Text to display in the autocomplete dropdown list.
        :param esrule: Type of variant. This will determine the ElasticSearch parameters.
        :return: Dictionary specifying ElasticSearch rules.
        """

        weight_dict = {
            'variants': 1,
            'wts': 5,
            'svs': 3,
            'cnvs': 3
        }
        return {'input': variant, 'weight': weight_dict[esrule]}

    @staticmethod
    def _get_investigator_suggest(investigator, dfci_investigator):
        """
        Creates a list of investigators from the _summary field of the trial collection
        """

        iin = []
        iout = ''
        ispl = [i.strip() for i in investigator.split(',')]
        if len(ispl) == 1:
            iin = [ispl[0]]
            iout = investigator
        elif len(ispl) >= 2:
            iin = [ispl[0], ispl[1]]
            iout = '%s %s' % (ispl[1], ispl[0])

        dfci_in = []
        dfci_out = ''
        if dfci_investigator is not None and 'first_name' in dfci_investigator:
            dfci_in.append(dfci_investigator['first_name'].strip())
            dfci_out += dfci_investigator['first_name'].strip()
        if dfci_investigator is not None and 'last_name' in dfci_investigator:
            dfci_in.append(dfci_investigator['last_name'].strip())
            dfci_out += ' %s' % dfci_investigator['last_name'].strip()

        inv_suggest = [{
            'input': [i for i in iin if i != ''],
            'output': iout
        }]
        if dfci_out != iout and dfci_out != '':
            inv_suggest.append({
                'input': dfci_in,
                'output': dfci_out.strip()
            })

        return inv_suggest

    @staticmethod
    def _get_tumor_types_search(ct_suggest):
        """
        Maps special cancer type text output to the values stored in the ElasticSearch index.

        :param ct_suggest: Cancer type text to display.
        :return: Cancer type text stored in th ElasticSearch index, which we will query.
        """

        tts = []
        for ct in ct_suggest:
            if 'output' in ct and ct['output'] == 'All Solid Tumors':
                tts.append('_SOLID_')
            elif 'output' in ct and ct['output'] == 'All Liquid Tumors':
                tts.append('_LIQUID_')
            else:
                tts.append(ct['output'])

        return tts

    def _extract_data_from_match(self, match):
        """
        Extract Cancer Type, Gene, and Variant data from the given match tree
        """

        g = self.m.create_match_tree(match)
        pmt = ParseMatchTree(g)
        for key, value_list in pmt.extract_cancer_types().items():
            if key not in self.cancer_type_dict:
                self.cancer_type_dict[key] = list()
            for item in value_list:
                if item not in self.cancer_type_dict[key]:
                    self.cancer_type_dict[key].append(item)
        self.genes.extend(pmt.extract_genes())
        vdict_tmp = pmt.extract_variants()
        for k, v in self.vdict.iteritems():
            v.extend(vdict_tmp[k])

    def add_autocomplete(self):
        """
        Recursively iterates through the treatment list and creates a list of genes contained within.

        :return: Nested dictionary containing all genes referenced within this trial
        """

        for step in self.treatment_list['step']:
            if 'match' in step:
                self._extract_data_from_match(step['match'][0])

            if 'arm' in step:
                for arm in step['arm']:
                    if 'match' in arm:
                        self._extract_data_from_match(arm['match'][0])

                    if 'dose_level' in arm:
                        for dose in arm['dose_level']:
                            if 'match' in dose:
                                self._extract_data_from_match(dose['match'][0])

        if not self.cancer_type_dict:
            self.cancer_type_dict = {
                'diagnoses': [],
                'primary_cancer_types': [],
                'cancer_types_expanded': [],
                'excluded_cancer_types': []
            }

        weighted_cancer_types = []
        for ct in self.cancer_type_dict['primary_cancer_types']:
            suggestion = self._get_cancer_type_weight(ct, hierarchy='primary')
            weighted_cancer_types.append(suggestion)

        for ct in set(self.cancer_type_dict['cancer_types_expanded']) - set(
                self.cancer_type_dict['primary_cancer_types']):
            suggestion = self._get_cancer_type_weight(ct, hierarchy='default')
            weighted_cancer_types.append(suggestion)

        weighted_variants = {}
        for key in ['variants', 'cnvs', 'svs', 'wts']:
            weighted_variants[key] = []
            for v in set(self.vdict[key]):
                suggestion = self._get_variants_weight(v, esrule=key)
                weighted_variants[key].append(suggestion)

        suggestors = {
            "cancer_type_suggest": weighted_cancer_types,
            "hugo_symbol_suggest": {"input": list(set(self.genes))},
            "variant_suggest": [i for i in weighted_variants['variants'] if not i['input'].endswith('any')],
            "wildtype_suggest": weighted_variants['wts'],
            "cnv_suggest": weighted_variants['cnvs'],
            "sv_suggest": weighted_variants['svs'],
            "protocol_no_suggest": {'input': self.summary['protocol_number']},
            "disease_center_suggest": {
                'input': [i.replace('(', '').replace(')', '') for i in self.summary['disease_center'].split()],
                'output': self.summary['disease_center']
            },
            'disease_status_suggest': {'input': self.summary['disease_status']},
            'drug_suggest': {'input': [i.title() for i in self.summary['drugs']]},
            'investigator_suggest': self._get_investigator_suggest(self.summary['investigator'],
                                                                   self.summary['dfci_investigator']),
            'mmr_status_suggest': {'input': self.summary['mmr_status'] + self.summary['ms_status'] + self.summary['mutational_signatures']},
            'nct_number_suggest': {'input': self.summary['nct_number']}
        }

        searchers = {
            "tumor_types": list(set(self._get_tumor_types_search(weighted_cancer_types))),
            "genes": list(set(self.genes)),
            "variants": list(set([i['input'] for i in weighted_variants['variants']])),
            "wildtype_genes": list(set([i['input'] for i in weighted_variants['wts']])),
            "cnv_genes": list(set([i['input'] for i in weighted_variants['cnvs']])),
            "sv_genes": list(set([i['input'] for i in weighted_variants['svs']])),
            "exclusion_genes": list(set(self.vdict['exclusions'])),
            "protocol_no": self.summary["protocol_number"],
            "drugs": self.summary["drugs"],
            "age": self.summary["age_summary"],
            "phase": self.summary["phase_summary"],
            "disease_status": self.summary["disease_status"],
            "nct_number": self.summary["nct_number"],
            "disease_center": self.summary["disease_center"],
            "mmr_status": self.summary["mmr_status"] + self.summary['mutational_signatures'],
            "ms_status": self.summary["ms_status"],
            "mutational_signatures": self.summary["mutational_signatures"],
            "investigator": [i['output'] for i in suggestors['investigator_suggest']],
            "short_title": self.summary["short_title"]
        }

        return suggestors, searchers, parse_primary_cancer_types(self.cancer_type_dict['primary_cancer_types'])


class ParseMatchTree:

    def __init__(self, g):
        """
        :param g: DiGraph match tree
        """
        self.g = g

    def extract_genes(self):
        """
        Returns all genes located in the matchtree

        :return: List of gene names
        """

        genes = []

        # iterate through the graph
        for node_id in list(nx.dfs_postorder_nodes(self.g, source=1)):
            node = self.g.node[node_id]
            if node['type'] == 'genomic':
                if 'hugo_symbol' in node['value']:

                    gene = node['value']['hugo_symbol']

                    if 'wildtype' in node['value'] and node['value']['wildtype'] is True:
                        continue

                    variant = None
                    for k in ['protein_change', 'wildcard_protein_change']:
                        if k in node['value']:
                            variant = node['value'][k].replace('p.', '')

                    if variant and variant.startswith('!'):
                        continue
                    if 'variant_category' in node['value'] and node['value']['variant_category'].startswith('!'):
                        continue

                    if node['value']['hugo_symbol'] not in genes:
                        genes.append(gene)

        return genes

    def extract_variants(self):
        """
        Returns all variants located in the matchtree

        :return: List of variants
        """

        cnvs = []
        fusions = []
        variants = []
        wildtypes = []
        exclusions = []

        # iterate through the graph
        for node_id in list(nx.dfs_postorder_nodes(self.g, source=1)):
            node = self.g.node[node_id]
            if node['type'] == 'genomic':
                if 'hugo_symbol' in node['value']:

                    gene = node['value']['hugo_symbol']

                    if 'wildtype' in node['value'] and node['value']['wildtype'] is True:
                        wt = '%s wt' % gene
                        wildtypes.append(wt)
                        continue

                    if 'variant_category' in node['value'] and node['value'][
                        'variant_category'] == 'Structural Variation':
                        sv = '%s SV' % gene
                        fusions.append(sv)
                        continue

                    if 'variant_category' in node['value'] and node['value'][
                        'variant_category'] == 'Copy Number Variation':
                        cnv = '%s CNV' % gene
                        cnvs.append(cnv)
                        continue

                    if 'protein_change' not in node['value'] and 'wildcard_protein_change' not in node['value']:
                        variant = '%s any' % gene
                        if not variant.startswith('!') and \
                                ('variant_category' not in node['value'] or
                                 ('variant_category' in node['value'] and not
                                 node['value']['variant_category'].startswith('!'))):
                            variants.append(variant)
                        elif (variant.startswith('!') or
                              ('variant_category' in node['value'] and
                               node['value']['variant_category'].startswith('!')) and variant not in exclusions):
                            exclusions.append(variant.replace('!', '').replace(' any', ''))
                    else:
                        for k in ['protein_change', 'wildcard_protein_change']:
                            if k in node['value']:
                                v = node['value'][k].replace('p.', '')
                                variant = '%s %s' % (gene, v)

                                if v.startswith('!') and variant not in exclusions:
                                    exclusions.append(variant.replace('!', ''))
                                elif 'variant_category' in node['value'] and node['value'][
                                    'variant_category'].startswith('!'):
                                    exclusions.append(variant.replace('!', ''))
                                else:
                                    if variant not in variants:
                                        variants.append(variant)

        variant_dict = {
            'variants': variants,
            'cnvs': cnvs,
            'svs': fusions,
            'wts': wildtypes,
            'exclusions': exclusions
        }
        return variant_dict

    def extract_cancer_types(self):
        """
        Returns all cancer types located in the match tree

        :param g: DiGraph match tree
        :return: List of cancer types
        """

        diagnoses = []
        cancer_types_expanded = []
        primary_cancer_types = []
        excluded_cancer_types = []
        onco_tree = oncotreenx.build_oncotree(file_path=TUMOR_TREE)
        liquid_children_txt, solid_children_txt = expand_liquid_oncotree(onco_tree)

        # iterate through the graph
        for node_id in list(nx.dfs_postorder_nodes(self.g, source=1)):
            node = self.g.node[node_id]
            if node['type'] == 'clinical':
                if 'oncotree_primary_diagnosis' in node['value']:

                    diagnosis = node['value']['oncotree_primary_diagnosis']

                    n = oncotreenx.lookup_text(onco_tree, diagnosis.replace('!', ''))
                    children = list(nx.dfs_tree(onco_tree, n))

                    if diagnosis == '_SOLID_':
                        children_txt = solid_children_txt
                        primary_parent = 'All Solid Tumors'
                        parents_txt = ['All Solid Tumors']
                    elif diagnosis == '_LIQUID_':
                        children_txt = liquid_children_txt
                        primary_parent = 'All Liquid Tumors'
                        parents_txt = ['All Liquid Tumors']
                    else:
                        children_txt = [onco_tree.node[nn]['text'] for nn in children]

                        if n is not None:
                            parents, parents_txt, primary_parent = get_parents(onco_tree, n)
                        else:
                            parents_txt = []
                            primary_parent = ''

                    diagnoses.append(diagnosis)
                    if diagnosis.startswith('!'):
                        excluded_cancer_types.append(diagnosis.replace('!', ''))
                        excluded_cancer_types.extend(children_txt)
                    else:
                        primary_tumors = get_primary_tumors()
                        cancer_types_expanded.append(parse_diagnosis(diagnosis))
                        cancer_types_expanded.extend(children_txt)
                        cancer_types_expanded.extend([i for i in parents_txt if i.split()[0] not in primary_tumors])
                        primary_cancer_types.append(primary_parent)

        return {
            'diagnoses': list(set(i for i in diagnoses if i.strip() != 'root')),
            'cancer_types_expanded': list(set(i for i in cancer_types_expanded if i.strip() != 'root')),
            'primary_cancer_types': list(set(i for i in primary_cancer_types if i.strip() != 'root')),
            'excluded_cancer_types': list(set(i for i in excluded_cancer_types if i.strip() != 'root'))
        }

    def extract_signatures(self):
        """
        Returns all mutational signatures located in the trial match tree g
        APOBEC, UVA, Temozolomide, POLE and TMB are treated as mutational signatures for convenience in the UI

        :return: List of mutational signatures
        """

        mmr = []
        ms = []
        sigs = []
        sig_mapping = {
            'tobacco_signature': 'Tobacco Signature',
            'uva_signature': 'UVA Signature',
            'temozolomide_signature': 'Temozolomide Signature',
            'apobec_signature': 'APOBEC Signature',
            'pole_signature': 'POLE Signature'
        }

        # iterate through the graph
        for node_id in list(nx.dfs_postorder_nodes(self.g, source=1)):
            node = self.g.node[node_id]
            if node['type'] == 'genomic':
                if 'mmr_status' in node['value']:
                    mmr.append(node['value']['mmr_status'])
                if 'ms_status' in node['value']:
                    ms.append(node['value']['ms_status'])
                for sig in sig_mapping.keys():
                    if sig in node['value']:
                        sigs.append(sig_mapping[sig])
            elif node['type'] == 'clinical':
                if 'tmb_numerical' in node['value']:
                    sigs.append('Tumor Mutational Burden')

        return mmr, ms, sigs

    def extract_hr_status(self):
        """
        Returns HER2, ER, and PR statuses

        :return: List of mutational signatures
        """

        hr_status = []
        for node_id in list(nx.dfs_postorder_nodes(self.g, source=1)):
            node = self.g.node[node_id]
            if node['type'] == 'clinical':

                if 'her2_status' in node['value']:
                    hr_status.append('HER2 %s' % node['value']['her2_status'])

                if 'er_status' in node['value']:
                    hr_status.append('ER %s' % node['value']['er_status'])

                if 'pr_status' in node['value']:
                    hr_status.append('PR %s' % node['value']['pr_status'])

        return hr_status


# --------- #
# Utilities #
# --------- #
def parse_dfci_investigator(staff, overall_pi, dfci=True):
    """
    :param staff: DFCI principal investigator staff info from trial document staff_list.
    :param overall_pi: Overall trial principal investigator in format Lastname, FirstName, MiddleName
    :param dfci: True if the staff member is from DFCI, else false.
    :return:
    {
        'name': First Last,
        'staff_role': Role,
        'institute': Institute
    }
    """
    required_fields = ['first_name', 'last_name', 'staff_role', 'institution_name', 'email_address']
    for field in required_fields:
        if field not in staff:
            staff[field] = ''

    if dfci:
        staff_role = 'DFCI Principal Investigator'
    else:
        staff_role = None

    is_overall_pi = False
    overall_pi = overall_pi.split(',')
    overall_pi_last = overall_pi[0]
    overall_pi_first = overall_pi[1]
    if overall_pi_first.strip() == staff['first_name'].strip() and \
            overall_pi_last.strip() == staff['last_name'].strip():
        is_overall_pi = True

    return {
        'first_name': staff['first_name'],
        'last_name': staff['last_name'],
        'first_last': '%s %s' % (staff['first_name'], staff['last_name']),
        'last_first': '%s %s' % (staff['last_name'], staff['first_name']),
        'staff_role': staff_role,
        'institution_name': staff['institution_name'],
        'email_address': staff['email_address'],
        'is_overall_pi': is_overall_pi
    }


def expand_liquid_oncotree(onco_tree):
    """
    Expand the _LIQUID_ oncotree node to all of its children

    :param onco_tree: Digraph of the Oncotree
    :returns liquid_children: All liquid tumor types in the Oncotree
             solid_children: All tumor types in the Oncotree minus "liquid_children"
    """

    # build the nodes for liquid.
    node1 = oncotreenx.lookup_text(onco_tree, "Lymph")
    node2 = oncotreenx.lookup_text(onco_tree, "Blood")

    nodes1 = list(nx.dfs_tree(onco_tree, node1))
    nodes2 = list(nx.dfs_tree(onco_tree, node2))
    nodes = list(set(nodes1).union(set(nodes2)))

    primary_tumors = get_primary_tumors()

    liquid_children_codes = []
    for n in nodes:
        liquid_children_codes.extend(list(nx.dfs_tree(onco_tree, n)))

    liquid_children = [onco_tree.node[nn]['text'] for nn in liquid_children_codes
                       if onco_tree.node[nn]['text'].strip() not in primary_tumors]

    # solid nodes are all other nodes
    all_nodes = set(list(onco_tree.nodes()))
    tmp_nodes = all_nodes - set(nodes)
    solid_children_codes = list(tmp_nodes)
    solid_children = [onco_tree.node[nn]['text'] for nn in solid_children_codes
                      if onco_tree.node[nn]['text'].strip() not in primary_tumors]

    return liquid_children, solid_children


def get_parents(onco_tree, node):
    """
    Retrive all parents of a given onco tree node

    :param onco_tree: Oncotree directed graph object
    :param node: Location within the oncotree
    :return: List of all parents
    """

    if not node:
        return [], []

    predecessors = onco_tree.predecessors(node)
    parents_txt = [onco_tree.node[n]['text'] for n in predecessors]
    check = onco_tree.predecessors(predecessors[0])

    if check and 'root' not in check:
        pr, pa, primary_parent = get_parents(onco_tree, predecessors[0])
        predecessors.extend(pr)
        parents_txt.extend(pa)
    else:
        primary_parent = parents_txt[0]

    return predecessors, parents_txt, primary_parent


def parse_diagnosis(diagnosis):
    """
    Replaces all solid and all liquid diagnoses text with text formatted for the UI

    :param diagnosis: ```string``` diaganosis text as stored in the database
    :return: ```string```
    """
    return diagnosis.replace('_SOLID_', 'All Solid Tumors').replace('_LIQUID_', 'All Liquid Tumors')


def parse_primary_cancer_types(cts):
    """
    Formats primary cancer type text for the UI
    """
    return [i.split('(')[0].strip() if not i.strip() == 'All Solid Tumors' and not i.strip() == 'All Liquid Tumors'
            else i for i in cts]


def get_primary_tumors():
    """
    Returns a list of all primary tumor types
    """
    oncotree_df = pd.read_csv(TUMOR_TREE, sep='\t')
    return [i.split('(')[0].strip() for i in oncotree_df.primary.unique().tolist()]
