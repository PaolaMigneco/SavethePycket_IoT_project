#!/usr/bin/env python

import random 
import sys 
import random 
import time
import json
sys.path.append('/shared')
from Sensor_Manager import *
class SensorWeight(SensorManager):
    def __init__(self):
        SensorManager.__init__(self)
        self.is_relay_open = False
        self.weight = 0.0

    def notify(self, topic, msg):
        print("msg: ", msg)
        jsonMsg=json.loads(msg)
    
        value=jsonMsg["info_sensor"][0]["value"] 
        if value == "True": # if the relay was opened by the user when the postman arrives
            self.weight = random.uniform(weight_ref+5, weight_ref+50)
            self.is_relay_open = True
        else: # if the relay was opened by the user to retrieve the packet
            self.is_relay_open = False
            self.weight = 0.0

if __name__ == "__main__":
    print("Starting weight sensor")
    sensor = SensorWeight()
    sensor.registration(sys.argv[1],"/shared/service_catalog_settings.json")
    
    if sensor.sensorID=='NOT FOUND' and sensor.topic=='NOT FOUND' and sensor.sensor_type =='NOT FOUND' and sensor.sensor_unit=='NOT FOUND'and sensor.sensor_location=='NOT FOUND' and sensor.broker=='NOT FOUND' and sensor.port=='NOT FOUND':
        print("Error: Service Catalog not found")
        exit()
    sensor.start() # start the sensor manager
    weight_ref = 0
    box_topic = sensor.boxID 
    building_topic = sensor.buildingID
    sensor.mySubscribe("SaveThePycket/sensors/sensor_Relbox_"+str(building_topic)+"_"+str(box_topic))
    while True:

        if sensor.is_relay_open:
            print("Publishing weight: " + str(sensor.weight) , flush=True)
            sensor.myPublish(sensor.weight, sensor.sensor_location, sensor.sensor_type, sensor.sensor_unit)
            time.sleep(5)
        else:
            print("Publishing weight: " + str(sensor.weight) , flush=True)
            sensor.myPublish(sensor.weight, sensor.sensor_location, sensor.sensor_type, sensor.sensor_unit)
            time.sleep(5)

