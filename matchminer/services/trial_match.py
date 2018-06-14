import pandas as pd


class TrialMatch:

    def __init__(self, db):
        """
        :param db: Database connection
        """
        self.db = db

    def get_trial_match(self, query):
        """
        Retrieve all "trial_match" documents that match the given query.

        :param query: ```pymongo query```
        :return: ```list```
        """
        return list(self.db.trial_match.find(query))

    def get_trial_match_as_df(self, query):
        """
        Retrieve all "trial_match" documents that match the given query and store them
        in a Pandas dataframe.

        :param query: ```pymongo query```
        :return: ```Pandas dataframe```
        """
        return pd.DataFrame.from_records(self.db.trial_match.find(query))
