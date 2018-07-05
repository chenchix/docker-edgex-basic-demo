# docker-edgex-basic-demo



## How to run the demo:

### EdgeX docker-compose file:

(docker-compose-edgex_arm64.yml) is ready to run in an ARM64. In this case, we will use a Cavium OcteonTX board running linux as SO based on buildroot customized rootfs.

We will run this script to launch dockers:

```#!/bin/sh

# Copyright (c) 2018
# Cavium
#
# SPDX-License-Identifier: Apache-2.0
#

# Start EdgeX Foundry services in right order, as described:
# https://wiki.edgexfoundry.org/display/FA/Get+EdgeX+Foundry+-+Users

COMPOSE_FILE=/docker-compose-edgex_arm64.yml

export COMPOSE_HTTP_TIMEOUT=100

docker login --username=docker --password=docker nexus3.edgexfoundry.org:10003

echo "Starting mongo"
docker-compose -f $COMPOSE_FILE up -d mongo
echo "Starting consul"
docker-compose -f $COMPOSE_FILE up -d config-seed

echo "Sleeping before launching remaining services"
sleep 15

echo "Starting support-logging"
docker-compose -f $COMPOSE_FILE up -d logging
echo "Starting core-metadata"
docker-compose -f $COMPOSE_FILE up -d metadata
echo "Starting core-data"
docker-compose -f $COMPOSE_FILE up -d data
echo "Starting core-command"
docker-compose -f $COMPOSE_FILE up -d command
echo "Starting export-client"
docker-compose -f $COMPOSE_FILE up -d export-client
echo "Starting export-distro"
docker-compose -f $COMPOSE_FILE up -d export-distro
echo "Startingc ui"
docker-compose -f $COMPOSE_FILE up -d ui

```

**NOTE**: EdgeX credentials are public and can be found [here](https://nexus.edgexfoundry.org/content/sites/docs/staging/master/docs/_build/html/Ch-GettingStartedUsersNexus.html?highlight=docker)

Once all dockers are up, you should se something like this in your board.

```CONTAINER ID        IMAGE                                                                         COMMAND                  CREATED             STATUS              PORTS                                                                                              
                                      NAMES
7b67d09f08b3        chenchix/edgex-ui-go                                                          "sh -c 'cd bin && ..."   2 days ago          Up 43 hours         0.0.0.0:4000->4000/tcp, 0.0.0.0:8080->8080/tcp                                                     
                                      edgex-ui-go
ffb97b7ef892        nexus3.edgexfoundry.org:10003/docker-export-distro-go-arm64:03a8236-0.5.2     "/export-distro --..."   6 days ago          Up 43 hours         0.0.0.0:48070->48070/tcp                                                                           
                                      edgex-export-distro
7300c1b8f231        nexus3.edgexfoundry.org:10003/docker-export-client-go-arm64:03a8236-0.5.2     "/export-client --..."   6 days ago          Up 43 hours         0.0.0.0:48071->48071/tcp                                                                           
                                      edgex-export-client
2db74774027b        nexus3.edgexfoundry.org:10003/docker-core-command-go-arm64:03a8236-0.5.2      "/core-command --c..."   6 days ago          Up 43 hours         0.0.0.0:48082->48082/tcp                                                                           
                                      edgex-core-command
19f65587ca01        nexus3.edgexfoundry.org:10003/docker-core-data-go-arm64:03a8236-0.5.2         "/core-data --cons..."   6 days ago          Up 43 hours         0.0.0.0:5563->5563/tcp, 0.0.0.0:48080->48080/tcp                                                   
                                      edgex-core-data
4a9f416299e4        nexus3.edgexfoundry.org:10003/docker-core-metadata-go-arm64:03a8236-0.5.2     "/core-metadata --..."   6 days ago          Up 43 hours         0.0.0.0:48081->48081/tcp, 48082/tcp                                                                
                                      edgex-core-metadata
e5dbcef8cd0b        nexus3.edgexfoundry.org:10003/docker-support-logging-go-arm64:03a8236-0.5.2   "/support-logging ..."   6 days ago          Up 43 hours         0.0.0.0:48061->48061/tcp                                                                           
                                      edgex-support-logging
12077d31116b        nexus3.edgexfoundry.org:10004/docker-core-config-seed-go-arm64                "sh launch-consul-..."   6 days ago          Up 43 hours         0.0.0.0:8300->8300/tcp, 0.0.0.0:8400->8400/tcp, 8301-8302/udp, 0.0.0.0:8500->8500/tcp, 0.0.0.0:8600
->8600/tcp, 8301-8302/tcp, 8600/udp   edgex-config-seed
9a8b1ad78d73        chenchix/mongo-arm64                                                          "/bin/sh -c /edgex..."   6 days ago          Up 43 hours         0.0.0.0:27017->27017/tcp                                                                           
                                      edgex-mongo
41af013684da        chenchix/volume-arm64                                                         "/bin/sh -c '/usr/..."   6 days ago          Up 43 hours                                                                                                            
                                      edgex-files
```


### Data generation and "cloud"

This Docker container, includes a mosquitto server (MQTT broker) which will act as cloud and a set of python scripts that simulates several rooms with 4 temperature sensors and 2 actuators (AC/Heater)

In your pc, set these variables and run docker-compose with the file (docker-compose-demo.yml)

- EDGEX_HOST: EdgeX server IP
- MQTT_HOST: Mqtt broker IP (local ip if you want to use the mqtt integrated in the dockerfile)
- ROOMS: number of rooms, space separated and without quotes

**NOTE**: Mosquitto browser credentials are hardcoded to dummy:dummy

Run: 
$ docker-compose -f docker-compose-edgex-demo.yml up


And you can launch a browser and navigate to *http://EDGEX_HOST:4000* using **admin:admin** to log in, and configure a gateway (EDGEX_HOST), select a device and check in *exports section* to see data.

