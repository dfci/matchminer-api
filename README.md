## Overview
Matchminer API written in python. This API utilizes the [Eve](http://python-eve.org/) framework and 
mongodb to build a lightweight and intuitive web app. Utilizing Eve's opinioned choices and direct 
integration with MongoDB enabled us to create a level 3 REST compliant application.

## Development guide
The following sections detail steps necessary to begin development on MatchMiner.
Python2.7, Docker, Virtualenv, and MongoDB are expected to be already installed 
in order to execute these installation directions.

### Installation
###### 1) clone repository
`git clone THIS-REPO`

###### 2) create virtual environment
```bash
virtualenv ENV-NAME
. ENV-NAME/bin/activate
cd matchminer-api
```

###### 3) install dependencies
`pip install -r requirements.txt`

###### 4) create mongodb docker container
The following commands will start and test the mongo container. A local instance of mongo can also be used,
 by over-ridding the configuration variables for the DB host.
```bash
docker run --name match-mongo -d -p 27017:27017 mongo mongod --smallfiles --replSet=rs0
docker exec -it match-mongo mongo matchminer --eval "rs.initiate();"
```

###### 5) add test data
First start a local mongo database. Then load the data from ./tests/data/clinical.bson and ./tests/data/genomic.bson. You will need to drop the db and restore after every full test run 

###### 6) run unit tests
Due to the sensitive nature of the application test driven development is a must. 
Unit tests are located in the /tests folder and roughly correspond to the application structure itself.
```bash
nosetests tests
```
Specific test functions can be called by following the syntax in the second command.
e.g.
 ```bash
nosetests tests/test_matchminer/test_filter.py:TestFiler.test_put_dirty
```

You also must update the oncotree file in ```settings_prod.py``` to ```./matchminerAPI/data/oncotree_file.txt``` as the file is in the repo.

### DEV server ###

The root of the application is **pymm_run.py**. The API can be served in development mode by using the following command:
```bash
python pymm_run.py serve [--no-auth]
```

You'll notice there are several commands inside the application.
* *debug* loads default filter/match data and users into the database.
* *restore* rebuilds the clinical and genomic repositories from serialized files
* *insert* populates the clinical and genomic repositories from Pandas .pkl files
* *dump* creates the serialized database files used for restoring.


## Deployment guide

MatchMiner can be deployed in development or production mode. In *development* a built in webserver is used to host the API. In *production* Docker is used.

The production deployment process consists of several phases:
1. building the Docker container locally
```bash
docker build -t DOCKER_IMAGE:VERSION .
```
2. push the container to central repository
```bash
docker push DOCKER_IMAGE:VERSION
```
3. log into remote repository
4. pull the container from repository to production host
```bash
docker pull DOCKER_IMAGE:VERSION
```
5. stoping existing containers and re-starting on deployment server
```bash
docker-compose down
docker-compose up -d
```

##### tagging convention #####
* dev: is used to development candidates (it will only ever contain simulated data)
* stage: is used for the staging enviroment
* latest: is the *master* or the *production* image


## Built with
* Python2.7
* [Virtualenv](https://virtualenv.pypa.io/en/stable/) - Tool to create isolated Python environments.
* [Eve](http://python-eve.org/) - REST API framework.
* [MongoDB](https://docs.mongodb.com/) - NoSQL document database for data storage.
* [Docker](https://docs.docker.com/machine/) - Container platform for deployment.
* [nose](http://nose.readthedocs.io/en/latest/) - Python library for unit testing.