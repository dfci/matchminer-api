#!/usr/bin/env bash

VERSION="1.0.0"
ES_VERSION="2.4.0"
MONGO_VERSION="latest"

# DATA_NAME="mm_data"
# TARBALL="${DATA_NAME}.tar.gz?raw=true"
# DATA_REMOTE_PATH="https://github.com/dfci/matchminer-engine/blob/master/examples/${TARBALL}"
DATA_LOCAL_PATH="demo/matchminer/data/mongo"
DOCKER_IMG_PATH="demo/matchminer"

# UI_REPO="git@gitlab-bcb.dfci.harvard.edu:knowledge-systems/matchminer-ui.git"
# UI_DEMO_BRANCH="simulated-data-demo"

API_DIR="matchminer-api"
UI_DIR="matchminer-ui"
DB_NAME="matchminer"

DOCKER_IMAGE_UI="matchminer-demo-ui"
DOCKER_IMAGE_API="matchminer-demo-api"
UI_CONTAINER="matchminer_ui_1"
API_CONTAINER="matchminer_api_1"
KIBANA_CONTAINER="matchminer_kibana_1"
CONNECTOR_CONTAINER="matchminer_connector_1"
ELASTIC_CONTAINER="matchminer_elastic_1"
MONGO_CONTAINER="matchminer_mongo_1"
MONGO_SETUP_CONTAINER="matchminer_mongo-setup_run_1"
DOCKER_CONTAINERS=(
    "${UI_CONTAINER}"
    "${API_CONTAINER}"
    "${KIBANA_CONTAINER}"
    "${CONNECTOR_CONTAINER}"
    "${ELASTIC_CONTAINER}"
    "${MONGO_CONTAINER}"
)

ES_URL="http://localhost:9200"
MAPPING_NAME="elasticsearch_settings.txt"
WORK_DIR=$(pwd)
# system checks
#if [ -d .git ]; then
#    WORK_DIR=$(git rev-parse --show-toplevel)
#else
#    echo "## ERROR: Please navigate to the home directory of your git repository before continuing"
#    exit 1
#fi

CHECK_FOR_DOCKER=$(pgrep docker)
if [ -z "${CHECK_FOR_DOCKER}" ]; then
    echo "## ERROR: Docker is not running."
    echo "##        See: https://docs.docker.com/engine/installation/ for"
    echo "##        instructions on how to install and setup docker on your machine"
    exit 1
fi

# echo
# echo
# echo "-------------------------------"
# echo "Downloading demo data"
# echo "-------------------------------"
# set -e

# wget ${DATA_REMOTE_PATH}

# echo
rm -rf ${WORK_DIR}/${DOCKER_IMG_PATH}/data/db
# rm -f ${WORK_DIR}/${DATA_LOCAL_PATH}/${TARBALL}
# rm -rf ${WORK_DIR}/${DATA_LOCAL_PATH}/${DATA_NAME}
# mv ./${TARBALL} ${WORK_DIR}/${DATA_LOCAL_PATH}
# tar xvfz ${WORK_DIR}/${DATA_LOCAL_PATH}/${TARBALL}
# mv ${DATA_NAME} ${WORK_DIR}/${DATA_LOCAL_PATH}
# rm -f ${WORK_DIR}/${DATA_LOCAL_PATH}/${TARBALL}

echo
echo
echo "-------------------------------"
echo "Creating and setting up docker images"
echo "-------------------------------"
set +e

CHECK_FOR_DEMO_IMG_API=$(docker images | grep "${DOCKER_IMAGE_API}")
CHECK_FOR_DEMO_IMG_UI=$(docker images | grep "${DOCKER_IMAGE_UI}")

# API
echo; echo "API"
if [ -z "${CHECK_FOR_DEMO_IMG_API}" ]; then
    docker build -t ${DOCKER_IMAGE_API}:${VERSION} .
fi
echo "DONE"

# UI
echo; echo "UI"
if [ -z "${CHECK_FOR_DEMO_IMG_UI}" ]; then
#    if [ ! -d "${WORK_DIR}/../${UI_DIR}" ]; then
#        echo "## WARNING: No UI repository was found in the same directory"
#        echo "##          as the API repository."
#        echo "##          Cloning now."
#
#        cd ${WORK_DIR}/..
#        git clone ${UI_REPO}
#        cd ${UI_DIR}
#
#    else
        cd ${WORK_DIR}/../${UI_DIR}
#    fi

#    ON_BRANCH=$(git branch -l | grep '*' | awk '{print $2}')

#    if [ "${ON_BRANCH}" != "${UI_DEMO_BRANCH}" ]; then
#        git stash
#        git checkout -b ${UI_DEMO_BRANCH} origin/${UI_DEMO_BRANCH}
#    fi

#    git pull origin ${UI_DEMO_BRANCH}

#    echo "On branch $(git branch -l | grep '*' | awk '{print $2}')"
    docker build -t ${DOCKER_IMAGE_UI}:${VERSION} .
fi
echo "DONE"

# Mongo, mongo-setup, Kibana, mongo-connector, ElasticSearch
echo; echo "Mongo and Elasticsearch"
cd ${WORK_DIR}/${DOCKER_IMG_PATH}
docker-compose up -d mongo
docker-compose run mongo-setup
docker rm ${MONGO_SETUP_CONTAINER}
docker-compose up -d api
docker-compose up -d elastic
docker-compose up -d connector
docker-compose up -d kibana
docker-compose up -d ui
echo "DONE"

echo
echo
echo "-------------------------------"
echo "Checking that the stack is running"
echo "-------------------------------"
sleep 10
for CONTAINER in "${DOCKER_CONTAINERS[@]}"; do

    RUNNING=$(docker inspect --format="{{.State.Running}}" ${CONTAINER} 2> /dev/null)

    if [ $? -eq 1 ]; then
        echo "## ERROR: ${CONTAINER} does not exist."
        exit 1
    fi

    if [ "${RUNNING}" = "false" ]; then
        echo "## ERROR: ${CONTAINER} is not running"
        exit 1
    fi

    RESTARTING=$(docker inspect --format="{{.State.Restarting}}" ${CONTAINER} 2> /dev/null)

    if [ "${RESTARTING}" = "true" ]; then
        echo "## ERROR: ${CONTAINER} is restarting"
        exit 1
    fi

    echo "${CONTAINER} is up"

done

echo
echo
echo "-------------------------------"
echo "Loading data into MongoDB"
echo "-------------------------------"
set -e
docker cp ${WORK_DIR}/${DATA_LOCAL_PATH}/${DB_NAME} ${MONGO_CONTAINER}:/
docker exec -it ${MONGO_CONTAINER} mongorestore --drop --db ${DB_NAME} ${DB_NAME}

echo
echo
echo "-------------------------------"
echo "Setting the ElasticSearch mapping"
echo "-------------------------------"
MAPPING=$(cat ${WORK_DIR}/${DATA_LOCAL_PATH}/${MAPPING_NAME})
docker-compose stop elastic connector
yes | docker-compose rm elastic connector
docker-compose up -d elastic
sleep 10
curl -X POST ${ES_URL}/${DB_NAME} -d "${MAPPING}"
docker-compose up -d connector

cd ${WORK_DIR}
echo
echo
echo "------------------------------------------------------------------"
echo "Demo environment setup complete. Navigate to http://localhost:8001"
echo "------------------------------------------------------------------"
