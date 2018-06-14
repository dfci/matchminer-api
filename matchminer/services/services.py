class Services:

    def __init__(self):
        pass

    @staticmethod
    def parse_query(query, **kwargs):
        """Returns pymongo query"""

        for k, v in kwargs.iteritems():
            query[k] = v

        return query
