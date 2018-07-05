#!/usr/bin/env python3
# Copyright (c) 2018
# Cavium
#
# SPDX-License-Identifier: Apache-2.0
#
# Author: Federico Claramonte <fclaramonte@cavium.com>
# Author: chencho <smunoz@cavium.com>


"""
Script to simulate several rooms with 3 temperature sensors and 2 actuators(AC/heater)
with edgex, copied from sensorSimulator
"""

import random
import sys
import time
import math
import logging

import edgex

from pymongo import MongoClient

EXTERNAL_HOT = 40
EXTERNAL_COLD = 5
HEATER_AC_ITER = 0.05
HEATER_AC_ITER = 0.8
# temperature difference at which we start to apply a correction
MAX_TEMP_DIFFERENCE = 4

heatOrCold = HEATER_AC_ITER / 3.0
externalTemp = EXTERNAL_HOT
lastChange = None

class Room:
    def __init__(self, name):
        self.temperatures = [0.0, 0.0, 0.0]
        self.ac = False
        self.heater = True
        self.name = name

    def __str__(self):
        return "Room %s: temps %r ac %r heater %r" % (self.name,
                                                      self.temperatures,
                                                      self.ac,
                                                      self.heater)

    def updateEdgeXTemperature(self, ex):
        ex.sendTemperatureData(self.name,
                               self.temperatures[0],
                               self.temperatures[1],
                               self.temperatures[2],
                               externalTemp)
        print(self)

    def updateTemperatures(self, ex):
        for i in range(len(self.temperatures)):
            if self.temperatures[i] >= EXTERNAL_HOT:
                self.temperatures[i] = EXTERNAL_HOT
            if self.temperatures[i] <= EXTERNAL_COLD:
                self.temperatures[i] = EXTERNAL_COLD
            self.temperatures[i] += random.random() - 0.5 + heatOrCold
            if self.heater:
                self.temperatures[i] += HEATER_AC_ITER
            if self.ac:
                self.temperatures[i] -= HEATER_AC_ITER

        temp_average = 0.0
        for i in range(len(self.temperatures)):
            temp_average += self.temperatures[i]
        temp_average = temp_average/len(self.temperatures)

        for i in range(len(self.temperatures)):
            if(math.fabs(temp_average - self.temperatures[i])>MAX_TEMP_DIFFERENCE):
                correction = math.copysign(random.random(), (temp_average - self.temperatures[i]))
                print ("---------------> applying corrections on Temp "+ str(i+1) + " correction: %.2f" % correction)
                self.temperatures[i] += correction

        self.updateEdgeXTemperature(ex)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: %s edgeXCoreDataHost mqttHost topicRooms.." % sys.argv[0])
        sys.exit(1)


    # Enable to debug http requests
    if False:
        # You must initialize logging, otherwise you'll not see debug output.
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
        
    edgeXHost = sys.argv[1]
    mqttHost = sys.argv[2]

    ex = edgex.EdgeX(edgeXHost)
    
    c = MongoClient(sys.argv[1], 27017)
    for db in ['coredata', 'exportclient', 'logging', 'metadata', 'notifications']:
        usedb = c[db]
        collections = usedb.collection_names()
        for colls in collections:
            coll = usedb[colls]
            print('Removing %s from %s' % (coll.name, usedb.name))
            coll.remove({})
            print('Removed %s (%d)' % (coll.name, coll.count()))
    
    ex.setupDemo()
    ex.exportToMqtt(mqttHost)

    rooms = []
    for name in sys.argv[3:]:
        rooms.append(Room(name))
        ex.createDevice(name)
        
    nRooms = len(rooms)
    # for r in rooms:
    #     print r

    lastChange = time.time()
    while True:
        t = time.time()
        if t - lastChange > 300.0:
            lastChange = t
            heatOrCold = -heatOrCold;
            print('temp cicle change', heatOrCold)

        if(heatOrCold > 0):
            # It is Hot!!!
            externalTemp += 1
        else:
            # It is Cold!!!
            externalTemp -= 1

        if externalTemp >= EXTERNAL_HOT:
            externalTemp = EXTERNAL_HOT
        if externalTemp <= EXTERNAL_COLD:
            externalTemp = EXTERNAL_COLD

        # Update temperatures and send to core-data
        for r in rooms:
            r.updateTemperatures(ex)

        # Get latest readings
        # TODO: change to getReadsSince
        readings = ex.getReadsLastSeconds(3)
        lastActuatorState = {}
        for actuator in readings:
            if actuator['name'] not in ['ac', 'heater']:
                # Only interested in the actuators
                continue

            i = actuator['device'] + "_" + actuator['name']
            try:
                knownState = lastActuatorState[i]
            except:
                lastActuatorState[i] = actuator
                continue

            if actuator['created'] > knownState['created']:
                lastActuatorState[i] = actuator

        for r in rooms:
            i = r.name + "_ac"
            if i in lastActuatorState:
                if lastActuatorState[i]['value'] == 'true':
                    state = True
                elif lastActuatorState[i]['value'] == 'false':
                    state = False
                else:
                    print('Not know ac value:', lastActuatorState[i]['value'])
                if state != r.ac:
                    print ('Updating %s ac to %s' % (r.name, str(state)))
                    r.ac = state

            i = r.name + "_heater"
            if i in lastActuatorState:
                if lastActuatorState[i]['value'] == 'true':
                    state = True
                elif lastActuatorState[i]['value'] == 'false':
                    state = False
                else:
                    print('Not know heater value:', lastActuatorState[i]['value'])
                if state != r.heater:
                    print('Updating %s heater to %s' % (r.name, str(state)))
                    r.heater = state

        print('Iter took %f secs' % (time.time() - t,))
        # print 'Iter took %f secs without 1 sec sleep' % (time.time() - t,)
        # time.sleep(1)
