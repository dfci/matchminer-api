import time

import logging
from oncotreenx import build_oncotree
import networkx as nx

import requests
from elasticsearch import Elasticsearch, helpers
from requests.auth import HTTPBasicAuth

from matchminer import database

from .settings import *

es_client = None


def get_es_client():
    global es_client
    if not es_client:
        es_client = Elasticsearch(hosts=ES_URL,
                                  maxsize=50,
                                  http_auth=(ES_USER, ES_PASSWORD),
                                  timeout=300)
    return es_client


def get_mongo_doc_by_trial_id(trial_id):
    db = database.get_db()
    output = db.trial.find_one({"protocol_no": trial_id})
    logging.info("get_mongo_doc_by_trial_id " + trial_id)
    return output


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def add_all_trials_to_elasticsearch():
    db = database.get_db()
    distinct_trial_ids = db.trial.distinct("protocol_no")
    logging.info("add_all_trials_to_elasticsearch " + str(distinct_trial_ids))
    for chunked_trial_ids in chunker(distinct_trial_ids, 100):
        add_trial_id_list_to_elasticsearch(chunked_trial_ids)


def add_trial_id_list_to_elasticsearch(trial_ids):
    logging.info("add_trial_id_list_to_elasticsearch " + str(trial_ids))
    prepared_trials = prepare_trials_for_elasticsearch([get_mongo_doc_by_trial_id(trial_id) for trial_id in trial_ids])
    add_prepared_trials_to_elasticsearch(prepared_trials)


def prepare_trials_for_elasticsearch(trials, op_type="index"):
    logging.info("prepare_trials_for_elasticsearch " + str(
        [trial.setdefault("protocol_no") for trial in trials]) + " " + op_type)
    return [prepare_for_es(trial, op_type) for trial in trials]


def add_trial_id_to_elasticsearch(t):
    logging.info("add_trial_id_to_elasticsearch " + t)
    add_trial_id_list_to_elasticsearch([t])


def add_prepared_trials_to_elasticsearch(prepared_trials):
    logging.info("add_prepared_trials_to_elasticsearch " + str([trial.setdefault("_id") for trial in prepared_trials]))
    helpers.bulk(get_es_client(), prepared_trials)


def put_prepared_trial_in_elasticsearch(prepared_trial):
    logging.info("put_prepared_trial_in_elasticsearch " + prepared_trial.setdefault('protocol_no'))
    if '_id' in prepared_trial:
        del prepared_trial["_id"]
    if '_type' in prepared_trial:
        del prepared_trial["_type"]
    if '_index' in prepared_trial:
        del prepared_trial["_index"]
    get_es_client().index(index=ES_INDEX, doc_type="trial", id=prepared_trial["protocol_no"], body=prepared_trial)


def prepare_for_es(trial, op_type="index", is_bulk=True):
    logging.info("prepare_for_es " + trial.setdefault("protocol_no"))
    if is_bulk:
        trial[u'_id'] = trial["protocol_no"]
    if 'created' in trial:
        trial['_created'] = trial['_created'].isoformat()
    if 'updated' in trial:
        trial['_updated'] = trial['_updated'].isoformat()
    if '_suggest' in trial:
        for k, v in trial['_suggest'].items():
            if isinstance(v, list):
                for item in v:
                    if u'output' in item:
                        del item[u'output']
            if u'output' in v:
                del v[u'output']
    if is_bulk:
        trial.update({"_index": ES_INDEX, "_type": "trial", "_op_type": op_type})
    return trial


def remove_trial_from_elasticsearch_by_es_id(es_id):
    if get_es_client().exists(ES_INDEX, "trial", es_id):
        logging.info("remove_trial_from_elasticsearch_by_es_id " + str(es_id))
        r = requests.delete(ES_URI + "/trial/" + es_id, auth=HTTPBasicAuth(ES_USER, ES_PASSWORD))
        r.raise_for_status()
        return {"status_code", r.status_code, "text", r.text}
    else:
        return dict()


def create_elasticsearch_index():
    logging.info("create_elasticsearch_index")
    get_es_client().indices.create(index=ES_INDEX)
    time.sleep(1)
    return {"created elasticsearch index": True}


def close_elasticsearch_index():
    logging.info("close_elasticsearch_index")
    get_es_client().indices.close(index=ES_INDEX)
    return {"closed elasticsearch index": True}


def open_elasticsearch_index():
    logging.info("open_elasticsearch_index")
    get_es_client().indices.open(index=ES_INDEX)
    return {"opened elasticsearch index": True}


def reset_elasticsearch_settings():
    logging.info("reset_elasticsearch_settings")
    with open(ES_SETTINGS) as es_settings_file_handle:
        json_payload = json.load(es_settings_file_handle)['settings']
    r = requests.put(ES_URI + "/_settings", json=json_payload, auth=HTTPBasicAuth(ES_USER, ES_PASSWORD))
    r.raise_for_status()
    msg = {"status_code": r.status_code, "text": r.text}
    logging.info(msg)
    return msg


def reset_elasticsearch_mapping():
    logging.info("reset_elasticsearch_mapping")
    with open(ES_MAPPING) as es_mapping_file_handle:
        json_payload = json.load(es_mapping_file_handle)['trial']

    ot = build_oncotree(TUMOR_TREE)
    order = ["All Solid Tumors", "All Liquid Tumors"]
    top_level_ot = sorted([node for node, path in nx.shortest_path(ot, 'root').items() if len(path) == 2],
                          key=lambda x: ot.node[x]['text'])
    for top_level in top_level_ot:
        order.append(ot.node[top_level]['text'])
        if '/' in ot.node[top_level]['text']:
            order = order + ot.node[top_level]['text'].split('/')
        second_level_ot = sorted([item for item in nx.descendants(ot, top_level)], key=lambda x: ot.node[x]['text'])
        for second_level in second_level_ot:
            order.append(ot.node[second_level]['text'])
            third_level_ot = sorted([item for item in nx.descendants(ot, second_level)],
                                    key=lambda x: ot.node[x]['text'])
            for third_level in third_level_ot:
                order.append(third_level)

    json_payload["_meta"] = dict(json_payload.setdefault('_meta',
                                                         dict()),
                                 **{"tumor_type_sort_order": order})
    r = requests.put(ES_URI + "/_mapping/trial?include_type_name=true", json=json_payload, auth=HTTPBasicAuth(ES_USER, ES_PASSWORD))
    r.raise_for_status()
    msg = {"status_code": r.status_code, "text": r.text}
    logging.info(msg)
    return msg


def delete_elasticsearch_index():
    logging.info("delete_elasticsearch_index")

    # when running for the first time ignore error that index does not exist
    get_es_client().indices.delete(index=ES_INDEX, ignore=[400, 404])
    return {"deleted elasticsearch index": True}


def reset_elasticsearch():
    logging.info("reset_elasticsearch")
    logging.info(ES_URI)
    logging.info(ES_USER)
    logging.info(ES_PASSWORD)
    return [delete_elasticsearch_index(),
            create_elasticsearch_index(),
            close_elasticsearch_index(),
            reset_elasticsearch_settings(),
            open_elasticsearch_index(),
            reset_elasticsearch_mapping(),
            add_all_trials_to_elasticsearch()]
