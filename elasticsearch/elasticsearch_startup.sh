#!/usr/bin/env bash
set -e

# When setting up a new elasticsearch server, run this file to setup settings and mappings.
# This assumes you have a local elasticsearch instance running on localhost:9200 version 5 or earlier

# First make index with settings file
INDEX="matchminer"
echo "Creating index..."
curl -XPUT -H "Content-Type: application/json" -d "@./settings.json" "http://localhost:9200/${INDEX}/" && \
echo ""
sleep 5

#Then close index
echo "Closing index..."
curl -XPOST --head --fail "http://localhost:9200/${INDEX}/_close" && \
echo ""

# Now setup settings for index
echo "Creating analyzers..."
curl -XPUT -H "Content-Type: application/json" -d "@./analyzers.json" "http://localhost:9200/${INDEX}/_settings" && \
echo ""

echo "Creating analysis settings..."
curl -XPUT -H "Content-Type: application/json" -d "@./analysis.json" "http://localhost:9200/${INDEX}/_settings" && \
echo ""

echo "Creating mappings..."
curl -XPUT -H "Content-Type: application/json" -d "@./mapping.json" "http://localhost:9200/${INDEX}/_mapping/trial" && \
echo ""

#Now open index
echo "Opening index..."
curl -XPOST --head --fail "http://localhost:9200/${INDEX}/_open" && \
echo ""
echo "DONE"

# To make mongo-connector sync between elasticsearch and mongoDB correctly,
# you MUST setup the mongo db as a replica set.
# See: https://github.com/yougov/mongo-connector

