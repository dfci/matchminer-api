FROM python:3.7
# install ubuntu packages.
RUN DEBIAN_FRONTEND=noninteractive apt-get update --fix-missing && apt-get install -y \
    build-essential \
    checkinstall \
    autoconf \
    libtool \
    pkg-config \
    supervisor \
    build-essential \
    bcrypt \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    rsyslog \
    git \
    libxml2-dev \
    libxslt1-dev \
    libxmlsec1-dev \
    swig \
    lib32ncurses5-dev \
    vim \
    libpng-dev \
    libjpeg62-turbo-dev \
    libfreetype6-dev \
    ca-certificates \
    openssl \
    libssl-dev \
    libffi-dev \
    libncurses5-dev \
    libsqlite3-dev \
    tk-dev libgdbm-dev \
    libc6-dev \
    libbz2-dev \
    curl \
    xz-utils \
 && apt-get clean \
 && apt-get autoremove

WORKDIR /
RUN rm -rf /tmp/build*

ENV PYTHONWARNINGS="ignore:a true SSLContext object"

# copy the applicaiton
RUN mkdir /api

# app
COPY ./matchminer /api/matchminer
COPY ./filters_config /api/filters_config
COPY ./cerberus1 /api/cerberus1
COPY ./pymm_run.py /api/pymm_run.py
COPY ./elasticsearch /api/elasticsearch

# gunicorn configs
COPY ./wsgi.py /api/wsgi.py
COPY ./gunicorn.conf.py /api/gunicorn.conf.py

WORKDIR /api
COPY ./requirements.txt /api/requirements.txt
RUN pip install -r requirements.txt

# setup entrypoint.
COPY ./entrypoint.sh /
ENTRYPOINT  ["/entrypoint.sh"]
