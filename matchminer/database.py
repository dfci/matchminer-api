from flask import current_app as app
from pymongo import MongoClient

from matchminer.settings import *


def get_collection(name):
    """
    return a connection to a specific collection

    :param name: name of the collection
    :return: mongoDB collection
    """
    try:
        collection = app.data.driver.db[name]
    except RuntimeError as e:

        # connect to database.
        #connection = MongoClient(MONGO_HOST, MONGO_PORT)

        connection = MongoClient(MONGO_URI)

        if MONGO_USERNAME:
            connection[MONGO_DBNAME].add_user(MONGO_USERNAME, MONGO_PASSWORD)

        db = connection[MONGO_DBNAME]

        # get the collection
        collection = db[name]

    # return it
    return collection


def get_db():
    """
    return a database connection.

    :return: mongoDB pointer
    """
    try:
        db = app.data.driver.db
    except RuntimeError as e:

        # connect to database.
        connection = MongoClient(MONGO_URI)

        if MONGO_USERNAME:
            connection[MONGO_DBNAME].add_user(MONGO_USERNAME, MONGO_PASSWORD)

        db = connection[MONGO_DBNAME]

    # return it
    return db
