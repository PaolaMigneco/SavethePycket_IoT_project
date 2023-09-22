#!/usr/bin/env python

import json
import sys
import requests
import time
sys.path.append('/shared')
from MyMQTT import *

class SensorManager(): # create a sensor manager class that registers the sensor in the catalog and publishes the sensor data with MQTT
    def __init__(self):
        self.sensorID = "" 
        self.sensor_name = ""
        self.sensor_type = ""
        self.sensor_unit = ""
        self.sensor_location = ""
        self.buildingID = ""
        self.boxID = ""
        self.topic = ""
        self.client = ""
        self.broker = ""
        self.port = ""
        self.__message = {
                                    'topic': self.topic, 
                                    'info_sensor': [
                                            {
                                                'type':self.sensor_type,
                                                'unit':self.sensor_unit,
                                                'timestamp':'',
                                                'value':'',
                                                'location':'',
                                                'buildingID':'',
                                                'boxID':'',
                                                'sensor_name':''
                                            }
                                        ]
                }
    def registration (self, settings, service_catalog_settings): # registration of a new sensor in the catalog
        with open(settings) as f: # get the settings of the sensor
            data = json.load(f)
            buildingID = data["buildingID"]
            sensorID = data["sensorID"]
            sensor_type = data["sensor_type"] 
            sensor_unit = data["sensor_unit"]
            sensor_location = data["sensor_location"] 
            topic = data["topic"]
            if "boxID" in data:
                boxID = data["boxID"]
                sensor_name = data["sensor_name"]
           
        with open(service_catalog_settings) as f: # get the settings of the service catalog
            data_service = json.load(f)
            ip_address = data_service["ip_address"]
            ip_port = data_service["ip_port"]
        
        info_request = "http://" + ip_address + ":" + str(ip_port) + "/resource_catalog" # request of information to the service catalog about the resource catalog
        rc = requests.get(info_request)
        rc_dict = rc.json()
        mqtt_request = "http://" + ip_address + ":" + str(ip_port) + "/mqtt_connection" # request of information to the service catalog about the mqtt broker
        mqtt = requests.get(mqtt_request)
        mqtt_dict = mqtt.json()
        if len(rc_dict) == 0 and len(mqtt_dict) == 0: # if there is no resource catalog
            return "NOT FOUND", "NOT FOUND", "NOT FOUND", "NOT FOUND", "NOT FOUND", "NOT FOUND", "NOT FOUND", "NOT FOUND", "NOT FOUND", "NOT FOUND"
        else:
            request = "http://" + rc_dict["ip_address"] + ":" + str(rc_dict["ip_port"]) + "/register_sensor" # request to the resource catalog to register a sensor
            requests.post(request, data = json.dumps(data))
            
            self.sensorID = sensorID
            self.sensor_type = sensor_type
            self.sensor_unit = sensor_unit
            self.sensor_location = sensor_location
            self.buildingID = buildingID
            self.topic = topic
            if "boxID" in data:
                self.boxID = boxID
                self.sensor_name = sensor_name
            self.broker = mqtt_dict["broker"]
            self.port = mqtt_dict["broker_port"]

            # create an instance of the MQTT client
            self.client = MyMQTT(self.sensorID, self.broker, self.port, self)
    
    def start (self): # start the MQTT client
        self.client.start()
    
    def stop (self): # stop the MQTT client
        self.client.stop()

    def myPublish (self, value, location, type_meas, unit): # publish a message with a certain topic
        msg = self.__message
        msg['info_sensor'][0]['type'] = type_meas # update the type of measurement
        msg['info_sensor'][0]['unit'] = unit # update the unit of measure
        msg['info_sensor'][0]['value'] = value # update the value of the sensor
        msg['info_sensor'][0]['timestamp'] = str(time.time()) # update the timestamp of the sensor
        msg['info_sensor'][0]['location'] = location # update the location of the sensor
        msg['info_sensor'][0]['buildingID'] = self.buildingID # update the buildingID of the sensor
        if self.boxID != "": # if the sensor is in a box 
            msg['info_sensor'][0]['boxID'] = self.boxID # update the boxID of the sensor
            msg['info_sensor'][0]['sensor_name'] = self.sensor_name # update the sensor name
        self.client.myPublish(self.topic, msg) 
    
    def mySubscribe (self, topic): # subscribe to a certain topic
        self.client.mySubscribe(topic)

    def notify(self, topic, msg): # notify the sensor manager that a message has been received
        jsonMsg=json.loads(msg)
        value=jsonMsg["info_sensor"][0]["value"]
        print("Value received: "+str(value))

    

   