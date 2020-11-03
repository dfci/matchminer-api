#!/bin/bash
set -e

function enable_site {
    # enable site using gunicorn
    gunicorn wsgi:app
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
