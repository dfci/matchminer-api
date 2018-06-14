from services import Services


class Match(Services):

    def __init__(self, db):
        """
        :param db: Database connection
        """
        Services.__init__(self)
        self.db = db
        self.proj = {}
        self.match_query = {}

    def add_matches(self, matches):
        """
        Adds match documents.

        :param matches: ```list```
        """
        self.db.match.insert_many(matches)

    def remove_matches(self, query):
        """
        Remove all "match" documents that match the given query.

        :param query: ```pymongo query```
        """
        self.db.match.remove(query)

    def add_trial_watch_matches(self, matches, query):
        """
        Adds trial watch match documents.

        :param matches: ```list```
        :param query: ```pymongo query```
        """
        if len(matches) == 0:
            return

        self.remove_matches(query)
        self.add_matches(matches)

    def get_matches(self, query=None, proj=None, **kwargs):
        """
        Retrieve all "match" documents that match the given query.

        :param query: ```pymongo query```
        :param proj: ```pymongo projection```
        :param kwargs: Optional additions to pymongo query
        :return: ```list```
        """
        if query is None:
            query = self.parse_query(self.match_query, **kwargs)

        if proj is None:
            list(self.db.match.find(query, proj))

        return list(self.db.match.find(query, proj))
