from services import Services


class Filter(Services):

    def __init__(self, db):
        """
        :param db: Database connection
        """
        Services.__init__(self)
        self.db = db
        self.proj = {}
        self.filter_query = {'status': 1, 'temporary': False}
        self.trial_watch_query = {'status': 1, 'temporary': False, 'trial_watch': True}

    def get_filter(self, query=None, proj=None, **kwargs):
        """
        Retrieve all "filter" documents that match the given query.

        :param query: ```pymongo query```
        :param proj: ```pymongo projection```
        :param kwargs: Optional additions to pymongo query
        :return: ```list```
        """
        if query is None:
            query = self.parse_query(self.filter_query, **kwargs)

        if proj is None:
            list(self.db.filter.find(query, proj))

        return list(self.db.filter.find(query, proj))

    def get_trial_watch_filter(self, query=None, proj=None, **kwargs):
        """
        Retrieve all "filter" documents that are created by the trial watch feature.

        :param query: ```pymongo query```
        :param proj: ```pymongo projection```
        :param kwargs: Optional additions to pymongo query
        :return: ```list```
        """
        if query is None:
            query = self.parse_query(self.trial_watch_query, **kwargs)

        if proj is None:
            return self.get_filter(query, proj)

        return self.get_filter(query, proj)
