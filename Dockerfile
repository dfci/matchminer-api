FROM ubuntu:14.04
MAINTAINER James Lindsay <jlindsay@jimmy.harvard.edu>

# add mongo repos.
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927
RUN echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.2 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.2.list

# install ubuntu packages.
RUN DEBIAN_FRONTEND=noninteractive apt-get update --fix-missing && apt-get install -y \
    build-essential \
    autoconf \
    libtool \
    pkg-config \
    python \
    python-dev \
    python-setuptools \
    cython \
    python-scipy \
    python-pip \
    supervisor \
    bcrypt \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    rsyslog \
    apache2 \
    libapache2-mod-wsgi \
    git \
    libxml2-dev \
    libxslt1-dev \
    libxmlsec1-dev \
    swig \
    lib32ncurses5-dev \
    mongodb-org-tools \
    nano \
    python-matplotlib \
    libpng-dev \
    libjpeg8-dev \
    libfreetype6-dev \
    ca-certificates \
    openssl \
    libssl-dev \
    libffi-dev \
 && apt-get clean \
 && apt-get autoremove \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONWARNINGS="ignore:a true SSLContext object"

# need to manual install for SAML package.
RUN pip install pkgconfig

# copy over and install the requirements
RUN pip install --upgrade setuptools pip numpy
COPY ./requirements.txt /var/www/apache-flask/api/requirements.txt
RUN pip install --ignore-installed six -r /var/www/apache-flask/api/requirements.txt

# set the timezone.
RUN echo "America/New_York" > /etc/timezone
RUN dpkg-reconfigure -f noninteractive tzdata

RUN pip uninstall -y certifi && pip install certifi ndg-httpsclient pyasn1

# copy the applicaiton
COPY ./matchminer /var/www/apache-flask/api/matchminer
COPY ./services /var/www/apache-flask/api/services
COPY ./tcm /var/www/apache-flask/api/tcm
COPY ./cerberus1 /var/www/apache-flask/api/cerberus1
COPY ./pymm_run.py /var/www/apache-flask/api/pymm_run.py
COPY ./api-swagger-documentation.json /var/www/apache-flask/api/api-swagger-documentation.json
COPY ./email.config.json /var/www/apache-flask/api/email.config.json

# start apache
EXPOSE 80
EXPOSE 443
EXPOSE 5000
EXPOSE 8443
WORKDIR /var/www/apache-flask/api

# setup entrypoint.
COPY ./entrypoint.sh /
ENTRYPOINT  ["/entrypoint.sh"]

# enable nano debugging (i hate vi)
ENV TERM xterm

# hack from https://github.com/onelogin/python3-saml/issues/82
RUN STATIC_DEPS=true pip install lxml==4.1.1 --force-reinstall
