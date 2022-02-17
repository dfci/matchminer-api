#!/usr/bin/env bash

# Set up a local development mongo/mongo-connector/elasticsearch environment.
set -e

case "$(docker-compose version)" in
  *docker-compose\ version\ 1*)
    # docker-compose exec sometimes breaks in v1
    echo "Requires docker-compose version 2 or greater."
    exit 1
    ;;
esac

echo "*****************"
echo "STARTING DATABASE SERVICES"
echo "*****************"
docker-compose up -d mm-mongo mm-elastic
echo "DONE."
echo ""

echo "*****************"
echo "SETTING UP MONGO"
echo "*****************"
sleep 5

echo "Add dev user to database to bypass authentication"
docker-compose exec mm-mongo mongo matchminer --eval 'db.user.insert({
  "_id": ObjectId("577cf6ef2b9920002cef0337"),
  "last_name" : "Doe",
  "teams" : [
    ObjectId("5a8ede8f4e0cce002dd5913c")
  ],
  "_updated" : ISODate("2018-02-22T10:15:27.000-05:00"),
  "first_name" : "John",
  "roles" : [
    "user",
    "cti",
    "oncologist",
    "admin"
  ],
  "title" : "",
  "email" : "fake_email@dfci.harvard.edu",
  "_created" : ISODate("2018-02-22T10:15:27.000-05:00"),
  "user_name" : "du123",
  "token" : "fb4d6830-d3aa-481b-bcd6-270d69790e11",
  "oncore_token" : "5f3c2421-271c-41ba-ac14-899f214d49b9"
})'

echo ""
echo "*****************"
echo "SETTING UP ELASTICSEARCH"
echo "*****************"
# naively wait for elasticsearch to start up
sleep 10
# run script to configure indexes, synonyms, etc.
docker-compose build mm-api
echo "Setup elasticsearch settings, mappings"

docker-compose run --rm mm-api python pymm_run.py reset-elasticsearch
echo "DONE."
echo ""

echo "*****************"
echo "STARTING API"
echo "*****************"
docker-compose build mm-api
docker-compose up mm-api
echo "Go to: http://localhost:5000"
