FROM python:3.7

# install ubuntu packages.
RUN DEBIAN_FRONTEND=noninteractive apt-get update --fix-missing && apt-get install -y \
    build-essential \
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
    apache2 \
    libapache2-mod-wsgi \
    git \
    libxml2-dev \
    libxslt1-dev \
    libxmlsec1-dev \
    swig \
    lib32ncurses5-dev \
    nano \
    vim \
    libpng-dev \
    libjpeg62-turbo-dev \
    libfreetype6-dev \
    ca-certificates \
    openssl \
    libssl-dev \
    libffi-dev \
 && apt-get clean \
 && apt-get autoremove \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONWARNINGS="ignore:a true SSLContext object"


RUN pip install --upgrade setuptools pip

# set the timezone.
RUN echo "America/New_York" > /etc/timezone
RUN dpkg-reconfigure -f noninteractive tzdata

# copy the applicaiton
COPY ./matchminer /var/www/apache-flask/api/matchminer
COPY ./services /var/www/apache-flask/api/services
COPY ./tcm /var/www/apache-flask/api/tcm
COPY ./cerberus1 /var/www/apache-flask/api/cerberus1
COPY ./pymm_run.py /var/www/apache-flask/api/pymm_run.py
COPY ./api-swagger-documentation.json /var/www/apache-flask/api/api-swagger-documentation.json

WORKDIR /var/www/apache-flask/api
COPY ./requirements.txt /var/www/apache-flask/api/requirements.txt
RUN pip install -r requirements.txt

# setup entrypoint.
COPY ./entrypoint.sh /
ENTRYPOINT  ["/entrypoint.sh"]

# enable nano debugging (i hate vi)
ENV TERM xterm

