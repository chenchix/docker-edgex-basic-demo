#!/usr/bin/env python3
# Copyright (c) 2018
# Cavium
#
# SPDX-License-Identifier: Apache-2.0
#
# Author: Federico Claramonte <fclaramonte@cavium.com>
# Author: chencho <smunoz@cavium.com>


"""
Some classes to comunicate with edgex
"""
import time
import json
import requests

class EdgeX:
    def __init__(self, ip='127.0.0.1'):
        self.ip = ip
        self.port = 48080
        self.metaIp = ip
        self.metaPort = 48081
        self.headers = {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*','Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods' : 'POST, GET, OPTIONS'}

    def setupDemo(self):
        tempTemplate = '{"name":"temp%s","min":"-20","max":"60","type":"F","uomLabel":"degree cel","defaultValue":"0","formatting":"%%s","labels":["temp","hvac"]}'
        actuatorTemplate = '{"name":"%s","type":"B","uomLabel":"per","defaultValue":"false","formatting":"%%s","labels":["actuator","hvac"]}'
        url = 'http://%s:%d/api/v1/valuedescriptor' % (self.ip, self.port)

        print(url)

        for i in ["1", "2", "3", "_ext"]:
            d = tempTemplate % i
            response = requests.post(url, data=d, headers=self.headers)
            if response.status_code == 409:
                # Updating temperature
                response = requests.put(url, data=d, headers=self.headers)

            if response.status_code != 200:
                print("Error adding temp%s:" % i, response.status_code)
                print(response.content)

        for act in ['ac', 'heater']:
            d = actuatorTemplate % act
            response = requests.post(url, data=d, headers=self.headers)
            if response.status_code == 409:
                # Updating actuator
                response = requests.put(url, data=d, headers=self.headers)

            if response.status_code != 200:
                print("Error adding actuator %s:" % act, response.status_code)

    def getValueDescriptors(self):
        url = 'http://%s:%d/api/v1/valuedescriptor' % (self.ip, self.port)
        response = requests.get(url, headers=self.headers)
        print(response.status_code)
        return json.loads(response.content)

    def getReadsByLabel(self, label, limit):
        url = 'http://%s:%d/api/v1/reading/label/%s/%d' % (self.ip, self.port, label, limit)
        response = requests.get(url, headers=self.headers)
        print(response.status_code)
        return json.loads(response.content)

    # since and until are in milliseconds
    def __getReadsTime(self, since, until):
        url = 'http://%s:%d/api/v1/reading/%d/%d/100' % (self.ip, self.port, since, until)
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return json.loads(response.content)
        else:
            return None

    def getReadsLastSeconds(self, seconds):
        until = int(time.time() * 1000)
        since = until - seconds * 1000
        return self.__getReadsTime(since, until)

    def getReadsSince(self, timestamp):
        until = int(time.time() * 1000)
        since = int(timestamp * 1000)
        return self.__getReadsTime(since, until)

    def sendTemperatureData(self, device, temp1, temp2, temp3, temp_ext):
        origin = self.getOriginForName(device)
        d = '{"origin":%d,"device":"%s","readings":[{"origin":%d,"name":"temp1","value":"%f"}, {"origin":%d,"name":"temp2","value":"%f"}, {"origin":%d,"name":"temp3","value":"%f"}, {"origin":%d,"name":"temp_ext","value":"%f"}]}'
        data = d % (origin, device, origin, temp1, origin, temp2, origin, temp3, origin, temp_ext)
        url = 'http://%s:%d/api/v1/event' % (self.ip, self.port)
        response = requests.post(url, data=data, headers=self.headers)
        if response.status_code != 200:
            print(response.status_code)

    def sendActuatorsData(self, device, ac, heater):
        origin = self.getOriginForName(device)
        d = '{"origin":%d,"device":"%s","readings":[{"origin":%d,"name":"ac","value":"%s"}, {"origin":%d,"name":"heater","value":"%s"}]}'

        if ac:
            acStr = 'true'
        else:
            acStr = 'false'
        if heater:
            heaterStr = 'true'
        else:
            heaterStr = 'false'

        data = d % (origin, device, origin, acStr, origin, heaterStr)
        url = 'http://%s:%d/api/v1/event' % (self.ip, self.port)
        response = requests.post(url, data=data, headers=self.headers)
        if response.status_code != 200:
            print(response.status_code)

    def createDevice(self, deviceName):
        print('Creating addressable for ', deviceName)
        addresableData = '{"origin":1471806386919,"name":"%s","protocol":"HTTP","address":"172.17.0.1","port":48089,"path":"/livingroomthermostat","publisher":"none","user":"none","password":"none","topic":"none"}' % (deviceName, )
        url = 'http://%s:%d/api/v1/addressable' % (self.metaIp, self.metaPort)
        response = requests.post(url, data=addresableData, headers=self.headers)
        if response.status_code != 200:
            print(response.status_code)
            print(response.content)
        else:
            print('OK')

        print('Creating addressable for service')
        serviceAddresableData = '{"origin":1471806386919,"name":"roomServiceAddress","protocol":"HTTP","address":"172.17.0.1","port":48089,"path":"/asdfasdf","publisher":"none","user":"none","password":"none","topic":"none"}'
        url = 'http://%s:%d/api/v1/addressable' % (self.metaIp, self.metaPort)
        response = requests.post(url, data=serviceAddresableData, headers=self.headers)
        if response.status_code != 200:
            print(response.status_code)
            print(response.content)
        else:
            print('OK')

        print('Creating service')
        serviceData = '{"origin":1471806386919,"name":"room device service","description":"manager service for rooms","lastConnected":0,"lastReported":0,"labels":["hvac","thermostat","home"],"adminState":"UNLOCKED","operatingState":"ENABLED","addressable":{"name":"roomServiceAddress"}}'
        url = 'http://%s:%d/api/v1/deviceservice' % (self.metaIp, self.metaPort)
        response = requests.post(url, data=serviceData, headers=self.headers)
        if response.status_code != 200:
            print(response.status_code)
            print(response.content)
        else:
            print('OK')

        print('Creating profile')
        profileData = '{"origin":1471806386919,"name":"roomProfile","description":"","manufacturer":"Cavium","model":"ABC123", "labels":["thermostat"],"commands":[],"objects":{}}'
        url = 'http://%s:%d/api/v1/deviceprofile' % (self.metaIp, self.metaPort)
        response = requests.post(url, data=profileData, headers=self.headers)
        if response.status_code != 200:
            print(response.status_code)
            print(response.content)
        else:
            print('OK')
        
        print('Creating device for ', deviceName)
        d = '{"origin":1471806386919,"name":"%s","description":"%s sensors","adminState":"UNLOCKED","operatingState":"ENABLED","addressable":{"name":"%s"},"labels":["temp","hvac"],"location":"{lat:45.45,long:47.80}","service":{"name":"room device service"},"profile":{"name":"roomProfile"}}' % (deviceName, deviceName, deviceName)
        url = 'http://%s:%d/api/v1/device' % (self.metaIp, self.metaPort)
        response = requests.post(url, data=d, headers=self.headers)
        if response.status_code != 200:
            print(response.status_code)
            print(response.content)
        else:
            print('OK')
            
    def exportToMqtt(self, mqttip, name="MQTTClient2"):
        # User and password must have some value, if not export-distro fails
        print(mqttip)
        d = '{"origin":1471806386919,"name":"%s","addressable":{"origin":1471806386919,"name":"%s","method":"POST","protocol":"TCP","address":"%s","port":1883,"publisher":"FuseExportPublisher_%s","user":"dummy","password":"dummy","topic":"FuseDataTopic"},"format":"JSON","enable":true, "destination":"MQTT_TOPIC","compression":"NONE"}' % (name, name, mqttip, name)
        url = 'http://%s:48071/api/v1/registration' % (self.ip,)
        response = requests.post(url, data=d, headers=self.headers)
        print(response.status_code)

    def deleteRegistration(self, name="MQTTClient2"):
        url = 'http://%s:48071/api/v1/registration/name/%s' % (self.ip, name)
        response = requests.delete(url, headers=self.headers)
        print(response.status_code)

    def getOriginForName(self, name):
        return abs(hash(name)) % 1000000

    def testMsgs(self):
        msgs = 10000
        t = time.time()
        for i in range(msgs):
            self.sendTemperatureData(333333, "testDevice", 23.4, 24.5, 25.6, 30.0)
        t2 = time.time()
        print('mesages per seg', msgs / (t2 - t))

    # functions no longer used
    # def testDataTest(self):
    #     d = '{"origin":1471806386919,"device":"livingroomthermostat","readings":[{"origin":1471806386919,"name":"temperature","value":"72"}, {"origin":1471806386919,"name":"humidity","value":"58"}]}'
    #     url = 'http://%s:%d/api/v1/event' % (self.ip, self.port)
    #     response = requests.post(url, data=d, headers=self.headers)
    #     if response.status_code != 200:
    #         print response.status_code

    # def setupDemoTest(self):
    #     d1 = '{"name":"temperature","min":"-40","max":"140","type":"F","uomLabel":"degree cel","defaultValue":"0","formatting":"%s","labels":["temp","hvac"]}'
    #     d2 = '{"name":"humidity","min":"0","max":"100","type":"F","uomLabel":"per","defaultValue":"0","formatting":"%s","labels":["humidity","hvac"]}'
    #     url = 'http://%s:%d/api/v1/valuedescriptor' % (self.ip, self.port)

    #     response = requests.post(url, data=d1, headers=self.headers)
    #     print response.status_code
    #     response = requests.post(url, data=d2, headers=self.headers)
    #     print response.status_code
    #     #print response.content

if __name__ == '__main__':
    edgex = EdgeX()
    #edgex.testData()
