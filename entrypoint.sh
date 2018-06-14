#!/bin/bash
set -e

function env_vars {

    # check variables.
    if [ -z "$MM_SETTINGS" ]; then
      echo "MM_SETTINGS NOT SET"
      exit 1;
    fi
    if [ -z "$SSL_PORT" ]; then
      echo "SSL_PORT NOT SET"
      exit 1;
    fi

}

function enable_site {

    # build actual configuration files.
    j2 apache-flask.conf.j2 > /etc/apache2/sites-available/apache-flask.conf
    j2 apache-ports.conf.j2 > /etc/apache2/ports.conf

    # enable the site.
    a2enmod headers ssl
    a2dissite 000-default.conf
    a2ensite apache-flask.conf

    # run the webserver.
    /usr/sbin/apache2ctl -D FOREGROUND
}

case ${1} in dev)
    echo "DEV"
    #python pymm_run.py restore
    #python pymm_run.py debug
    python pymm_run.py serve --no-auth
    ;;
  stage)
    echo "STAGE"
    env_vars;
    enable_site;
    ;;
  prod)
    echo "PROD"
    env_vars;
    enable_site;
    ;;
  backup)
    echo "BACKUP"
    python pymm_run.py backup_daemon
    ;;
  account)
    echo "ACCOUNT"
    python pymm_run.py account_daemon
    ;;
  empi)
    echo "EMPI"
    python pymm_run.py empi_daemon
    ;;
  help)
    echo "Available options:"
    echo " dev        - Starts the development server"
    echo " stage      - Starts the staging server"
    echo " prod       - Starts the production server"
    echo " backup     - Starts the backup service"
    echo " account    - Starts the account service"
    echo " empi       - Starts the empi service"
    echo " help       - Displays the help"
    echo " [command]  - Execute the specified command, eg. bash."
    ;;
  *)
    exec "$@"
    ;;
esac
