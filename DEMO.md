# MatchMiner V1.0 demo installation
This is a step by step guide to install and run a dockerized demo installation of MatchMiner using simulated data.

   ### Download the demo data
- https://drive.google.com/open?id=0B334b-HHVrwGc3djZUdvMktNekU
- Decompress mm_data.tar.gz and move genomic.bson, clinical.bson, trial.bson, and synonyms.txt to ./demo/matchminer/data/mongo

   ### Creating and setting up the images
1. Start the Docker Engine

   Check if the matchminer-demo-api:1.0.0 and matchminer-demo-ui:1.0.0 docker images are available. If not do step 2 - 5

   `> docker images`

   If they are present you should see:
   ```
   REPOSITORY                         TAG                 IMAGE ID            CREATED             SIZE
   matchminer-demo-ui                1.0.0               5c520c30478c        10 hours ago        1.04 GB
   matchminer-demo-api               1.0.0               938ea08d802c        10 hours ago        1.06 GB
   ...
   ```

   #### The UI image
   Navigate to matchminer-ui repository
2. `> cd /matchminer-ui`
3. `> docker build -t matchminer-demo-ui:1.0.0 .`

   #### The API image
   Navigate to matchminer-api repository

4. `> cd /matchminer-api/`
5. `> docker build -t matchminer-demo-api:1.0.0 .`

   NOTE: All mentioned paths are relative to the matchminer-api repository root.

   #### Building the remaining images (mongo, mongo-setup, kibana, mongo-connector, elasticsearch)
6. `> cd ./demo/matchminer`
7. `> docker-compose up -d`

   #### Check if the stack is running
8. `> docker ps`

   You should see something like the following:
   ```
   CONTAINER ID        IMAGE                                    COMMAND                  CREATED             STATUS              PORTS                                               NAMES
   ca04363b2487        matchminer-demo-ui:1.0.0                "/entrypoint.sh"         9 hours ago         Up 9 hours          0.0.0.0:8001->8001/tcp                              matchminer_ui_1
   cf7f2fb67265        matchminer-demo-kibana-sense:1.0.0      "/docker-entrypoin..."   9 hours ago         Up 9 hours          0.0.0.0:5601->5601/tcp                              matchminer_kibana_1
   326aa84fbf9b        matchminer-demo-mongo-connector:1.0.0   "/tmp/startup.sh"        9 hours ago         Up 9 hours                                                              matchminer_connector_1
   8a75218f7fca        matchminer-demo-api:1.0.0               "/entrypoint.sh dev"     9 hours ago         Up 9 hours          80/tcp, 443/tcp, 8443/tcp, 0.0.0.0:5555->5000/tcp   matchminer_api_1
   5b66b3b1c2c7        elasticsearch:2.4.0                     "/docker-entrypoin..."   9 hours ago         Up 9 hours          0.0.0.0:9200->9200/tcp, 9300/tcp                    matchminer_elastic_1
   896379773ce9        mongo:latest                            "docker-entrypoint..."   9 hours ago         Up 9 hours          27017/tcp                                           matchminer_mongo_1
   ```

   #### Check if the mongo replicateset (rs) has been initialized.
9. `> docker exec -it matchminer_mongo_1 sh`
10. `# mongo`

   You should see the following prompt presented:

   `rs0:PRIMARY>`

   If this is the case then the replicateset has been initialized.
   If this has not been done correctly you would see `rs0:OTHER>` as a prompt. To initialize the replicateset run the following command:

	 `> rs.initiate();`

  ### Loading the data
11. Exit the mongo shell (> exit or ctrl-c)
12. `> cd /storage`

  #### Loading the genomic data
13. `> mongorestore --db matchminer genomic.bson`

  #### Loading the clinical data
14. `> mongorestore --db matchminer clinical.bson`

    The clinical trials will be added later. We will have to correctly add the mapping to Elasticsearch first.

  #### Insert a demo user
15. `> cat /storage/user.txt`

    Copy the first json object into the clipboard and insert it into the mongo database

16. `> mongo`
17. `# use matchminer;`
18. `db.user.insert(PASTE JSON OBJECT HERE)`

    Find the _id of the user just inserted
19. `db.user.find()`

    Copy the _id of the user to the clipboard

20. Exit the mongo shell and exit the container (> exit (2x))

    #### Add the demo user _id to the config.json of the UI
21. `> docker exec -it matchminer_ui_1 sh`

    NOTE: You might have to install a text editor if its not present in the container

    #### Installing a text editor
22. `> apt-get update`
23. `> apt-get install vim`
24. `> cd properties`
25. `> vim config.json`

    Replace the user_id under the following path: dev.ENV.devUser.user_id
27. Exit the UI container

    #### Restart the ui container
26. `> cd ./demo/matchminer`
27. `> docker-compose restart ui`

    #### Getting the Elasticsearch mapping right
    Bring down the mongo-connector

28. `> docker-compose stop connector`

    In browser navigate to: localhost:5601

30. Set Elasticsearch URL in kibana to: http://elasticsearch:9200

    Drop the matchminer Elasticsearch index

31. In the large text field on the left enter:
`DELETE matchminer`

32. Click the green play icon on the top right of the text box

    Copy the mapping JSON structure that came with this installation guide (./demo/data/mongo/elasticsearch_settings.txt)

33. In the same text box add
`POST matchminer {
	PASTE JSON MAPPING HERE
}`

33. Click the green play button to execute the command

    #### Launch the mongo container shell again
34. `> docker exec -it matchminer_mongo_1 sh`
35. `# cd /storage`
36. `# mongorestore --db matchminer trial.json`
37. Exit the mongo container (`# exit`)

    #### Start the mongo-connector
38. `> docker-compose start connector`

    ### All should be well! Check if the UI is running correctly in your browser:
`http://localhost:8001`
