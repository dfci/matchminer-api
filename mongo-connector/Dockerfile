FROM python:3.4.3

ENV DEBIAN_FRONTEND noninteractive

# Installing Mongo Connector which will connect MongoDB and Elasticsearch
RUN pip install mongo-connector
RUN pip install elastic2-doc-manager[elastic2]
RUN pip install pathlib2
RUN pip install pymongo

COPY startup.sh /

# create the log directory
VOLUME /data

# sample usage when no commands is given outside
ENTRYPOINT ["/startup.sh"]
