FROM python:3.7-slim

# install ubuntu packages.
RUN DEBIAN_FRONTEND=noninteractive apt-get update --fix-missing && apt-get install -y \
    libxml2-dev \
    libxslt1-dev \
    libxmlsec1-dev \
    libxmlsec1-openssl \
    pkg-config \
    git \
    gcc

RUN mkdir /matchminerAPI
COPY ./requirements.txt /matchminerAPI/requirements.txt
WORKDIR /matchminerAPI

RUN pip install -r requirements.txt

# Hack to work around https://github.com/py-bson/bson/issues/82
RUN pip --no-input uninstall --yes bson
RUN pip --no-input uninstall --yes pymongo
RUN pip install 'pymongo==3.10'

ENV ONCOTREE_CUSTOM_DIR /matchminerAPI/data/oncotree_file.txt

EXPOSE 80
COPY . /matchminerAPI/
CMD gunicorn wsgi:app --bind=0.0.0.0:80
