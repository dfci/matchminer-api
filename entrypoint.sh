#!/bin/bash
set -e

function enable_site {

    # enable the site.
    a2enmod headers ssl wsgi
    a2dissite 000-default.conf
    a2ensite apache-flask.conf

    # run the webserver.
    /usr/sbin/apache2ctl -D FOREGROUND
}

case ${1} in dev)
    echo "DEV"
    python pymm_run.py serve --no-auth
    ;;
  stage)
    echo "STAGE"
    enable_site;
    ;;
  prod)
    echo "PROD"
    enable_site;
    ;;
  help)
    echo "Available options:"
    echo " dev        - Starts the development server"
    echo " stage      - Starts the staging server"
    echo " prod       - Starts the production server"
    echo " help       - Displays the help"
    echo " [command]  - Execute the specified command, eg. bash."
    ;;
  *)
    exec "$@"
    ;;
esac
