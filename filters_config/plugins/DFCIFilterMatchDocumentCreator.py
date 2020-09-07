from __future__ import annotations

from typing import TYPE_CHECKING, List

from matchengine.internals.plugin_helpers.plugin_stub import TrialMatchDocumentCreator

if TYPE_CHECKING:
    from matchengine.internals.typing.matchengine_types import TrialMatch, MatchReason, ClinicalID
    from matchengine.internals.engine import MatchEngine
    from typing import Dict


class DFCIFilterMatchDocumentCreator(TrialMatchDocumentCreator):
    def results_transformer(self: MatchEngine, results: Dict[ClinicalID, List[MatchReason]]):
        for clinical_id, reasons in results.items():
            self.cache.docs[clinical_id]['FILTER_ID'] = self.cache.docs[clinical_id]['_id']

            # get all genomic ids
            variants = []
            for reason in reasons:
                if reason.__class__.__name__ == 'ExtendedMatchReason':
                    variants.append(reason.reference_id)

            # The code below will attach genomic information to the output match document
            # from one matching genomic document. This is because the UI only displays
            # information from the first matching genomic document in the VARIANTS array.
            # A better solution should be rebuilt.
            sorted_variants = sorted(variants)
            self.cache.docs[clinical_id]['VARIANTS'] = sorted_variants

            if len(sorted_variants) > 0:
                genomic = list(self.db_ro.genomic.find({'_id': sorted_variants[0]}))

                if len(genomic) > 0:
                    genomic = genomic[0]
                    if "TRUE_HUGO_SYMBOL" in genomic and 'TRUE_HUGO_SYMBOL' not in self.cache.docs[clinical_id]:
                        self.cache.docs[clinical_id]['TRUE_HUGO_SYMBOL'] = genomic['TRUE_HUGO_SYMBOL']
                    if "VARIANT_CATEGORY" in genomic and 'VARIANT_CATEGORY' not in self.cache.docs[clinical_id]:
                        self.cache.docs[clinical_id]['VARIANT_CATEGORY'] = genomic['VARIANT_CATEGORY']
                    if "TIER" in genomic and 'TIER' not in self.cache.docs[clinical_id]:
                        self.cache.docs[clinical_id]['TIER'] = genomic['TIER']
                    if "ALLELE_FRACTION" in genomic and 'ALLELE_FRACTION' not in self.cache.docs[clinical_id]:
                        self.cache.docs[clinical_id]['ALLELE_FRACTION'] = genomic['ALLELE_FRACTION']
                    if "TEST_NAME" in genomic and 'TEST_NAME' not in self.cache.docs[clinical_id]:
                        self.cache.docs[clinical_id]['TEST_NAME'] = genomic['TEST_NAME']

                    # RHP samples should populate tier column with PATHOGENICITY_PATHOLOGIST
                    # val from genomic samples
                    if "PATHOGENICITY_PATHOLOGIST" in genomic and 'TIER' not in self.cache.docs[clinical_id]:
                        self.cache.docs[clinical_id]['TIER'] = genomic['PATHOGENICITY_PATHOLOGIST']

            results[clinical_id] = [reasons[0]]

    def create_trial_matches(self, trial_match: TrialMatch, new_trial_match: Dict) -> Dict:
        """
        Create a filter match document to be inserted into the db.
        Reformat to match existing match schema.
        """
        new_trial_match.pop("_updated", None)
        new_trial_match.pop("last_updated", None)
        new_trial_match.pop('q_depth', None)
        new_trial_match.pop('q_width', None)
        new_trial_match.pop('code', None)
        new_trial_match.pop('trial_curation_level_status', None)
        new_trial_match.pop('trial_summary_status', None)
        new_trial_match.pop('match_level', None)
        new_trial_match.pop('internal_id', None)
        new_trial_match.pop('coordinating_center', None)
        new_trial_match.pop('show_in_ui', None)
        new_trial_match.pop('match_path', None)
        new_trial_match.pop('combo_coord', None)
        new_trial_match.pop('reason_type', None)
        new_trial_match.pop('filter_id', None)
        new_trial_match.pop('label', None)
        new_trial_match.pop('ord_physician_email', None)
        new_trial_match['PATIENT_MRN'] = new_trial_match.pop('mrn', None)
        new_trial_match['FILTER_STATUS'] = trial_match.trial['status']
        new_trial_match['FILTER_ID'] = trial_match.trial['_id']

        protocol_id = new_trial_match.get('protocol_id', "")
        test_name = new_trial_match.pop('test_name', "").title()
        if test_name == 'Oncopanel':
            test_name = 'OncoPanel'

        new_trial_match['EMAIL_SUBJECT'] = f"{test_name} Trial Match ({protocol_id})"
        new_trial_match['MATCH_STATUS'] = 1

        # check for multiple genomic genes in 'or' clauses
        if len(trial_match.match_clause_data.match_clause[0]['and']) > 1:
            # set default hugo symbol val to existing true_hugo_symbol val from the genomic doc
            # if no hugo symbol is present on the genomic document,
            # populate it from query which returned match
            genes = ""
            if 'true_hugo_symbol' in new_trial_match and new_trial_match['true_hugo_symbol'] is not None:
                genes = new_trial_match['true_hugo_symbol']

            if genes == "":
                query_nodes = trial_match.multi_collection_query.extended_attributes[0].query_nodes
                for query_node in query_nodes:
                    criterion_ancestor = query_node.criterion_ancestor
                    if 'genomic' in criterion_ancestor and 'TRUE_HUGO_SYMBOL' in criterion_ancestor['genomic']:
                        if genes == "":
                            genes = criterion_ancestor['genomic']['TRUE_HUGO_SYMBOL']
                        elif criterion_ancestor['genomic']['TRUE_HUGO_SYMBOL'] not in genes:
                            genes += ', ' + criterion_ancestor['genomic']['TRUE_HUGO_SYMBOL']

            new_trial_match['true_hugo_symbol'] = genes

        # capitalize output for consistency
        output = {}
        for key in new_trial_match.keys():
            if key in ["_updated", "hash", "is_disabled", "_id", "sample_id"]:
                output[key] = new_trial_match[key]

            elif key == "clinical_id":
                # hack. UI expects upper case clinical ID. Engine expects lower case for smartupdate to work
                output["clinical_id"] = new_trial_match["clinical_id"]
                output["CLINICAL_ID"] = new_trial_match["clinical_id"]
            else:
                output[key.upper()] = new_trial_match[key]

        return output


__export__ = ["DFCIFilterMatchDocumentCreator"]
