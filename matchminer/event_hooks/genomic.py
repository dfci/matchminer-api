import logging

from bson import ObjectId
from flask import current_app as app

from matchminer import settings
from matchminer import database

def negative_genomic(items):
    """
    When "negative_genomic" documents are POSTed, all entries without an exon or codon specified will be marked
    entire_gene: True. All others will be marked entire_gene: False.
    """

    for item in items:

        # pertinent and non-pertinent low coverage types always display exon
        if item['coverage_type'] == 'PLC' or item['coverage_type'] == 'NPLC':
            item['show_exon'] = True

        # pertinent negatives display logic proceeds by roi_type ("Region of interest")
        elif item['coverage_type'] == 'PN':

            if 'roi_type' not in item or item['roi_type'] is None:
                continue

            if item['roi_type'] == 'C':
                item['show_codon'] = True

            elif item['roi_type'] == 'E':
                item['show_exon'] = True

            elif item['roi_type'] == 'R':
                item['show_codon'] = True

            elif item['roi_type'] == 'G':
                item['entire_gene'] = True

            elif item['roi_type'] == 'M':
                item['show_codon'] = True


def get_alterations(variant):
    # get the alteration
    genomic = variant[0]
    if genomic['VARIANT_CATEGORY'] == 'MUTATION':
        if 'TRUE_PROTEIN_CHANGE' in genomic and genomic['TRUE_PROTEIN_CHANGE'] is not None:
            alteration = "%s %s mutation" % (genomic['TRUE_HUGO_SYMBOL'], genomic['TRUE_PROTEIN_CHANGE'].replace("p.", ""))
        else:
            alteration = "%s mutation" % (genomic['TRUE_HUGO_SYMBOL'])

    elif genomic['VARIANT_CATEGORY'] == 'CNV':
        alteration = "%s %s" % (genomic['TRUE_HUGO_SYMBOL'], genomic['CNV_CALL'].lower())

    else:
        alteration = "structural re-arrangement"
    return alteration


def genomic_insert(items):

    # modify each item.
    for item in items:

        # set strings to be object ids
        item['CLINICAL_ID'] = ObjectId(item['CLINICAL_ID'])


def align_matches_genomic(a):
    """
   Attach filter docs to genomic docs which have been matched successfully by filters.

   E.g. If a filter is seeking EGFR, and a genomic document represents EGFR and
   has been positively matched, attach the EGFR filter to the EGFR genomic doc.
   :param genomic_docs:
   :return:
   """

    # short circuit.
    if len(a['_items']) == 0:
        return

    # get the user.
    if settings.NO_AUTH:
        logging.info("NO AUTH enabled. align_matches_genomic")
        accounts = app.data.driver.db['user']
        user = accounts.find_one({"last_name": "Doe"})
    else:
        user = app.auth.get_request_auth_value()

    # extract the clinical id.
    clinical_id = a['_items'][0]['CLINICAL_ID']

    match_db = database.get_collection('match')
    filter_db = database.get_collection('filter')

    variants = dict()
    for match in match_db.find({"CLINICAL_ID": clinical_id, "is_disabled": False}):
        for variant_id in match['VARIANTS']:
            if variant_id not in variants:
                variants[variant_id] = list()

            variants[variant_id].append(match['FILTER_ID'])

    for item in a['_items']:
        if item['_id'] in variants:
            for filter_id in variants[item['_id']]:

                filter_doc = filter_db.find_one(filter_id)
                if filter_doc is None:
                    continue

                # check status.
                if filter_doc['status'] != 1:
                    continue

                # check ownership.
                if filter_doc['TEAM_ID'] not in set(user['teams']):
                    continue

                # embed this in filter.
                if 'FILTER' not in item:
                    item['FILTER'] = list()

                item['FILTER'].append(filter_doc)

        # merge genetic event with cytoband
        if 'GENETIC_EVENT' in item and 'CYTOBAND' in item and item['GENETIC_EVENT'] is not None:
            item['CYTOBAND'] = '%s %s' % (item['CYTOBAND'], item['GENETIC_EVENT'])
