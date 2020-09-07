#!/bin/bash
set -e
mongo="${MONGO}"
mongoport="${MONGOPORT}"

# check that mongo db is setup as a replica set correctly.
function _mongo() {
    mongo --host ${mongo} --port ${mongoport} <<EOF
    $@
EOF
}

is_master_result="false"
expected_result="true"
while true;
do
  if [ "${is_master_result}" == "${expected_result}" ] ; then
    is_master_result=$(_mongo "rs.isMaster().ismaster")
    echo "Waiting for Mongod node to assume primary status..."
    sleep 5
  else
    echo "Mongod node is now primary"
    break;
  fi
done
sleep 1

mongo-connector -c /config.json --stdout
