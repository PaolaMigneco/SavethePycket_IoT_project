#!/usr/bin/env python

import random 
import sys 
import time
sys.path.append('/shared')
from Sensor_Manager import *
class SensorRelayBox(SensorManager):
    def __init__(self):
        SensorManager.__init__(self)
        self.box_is_open = "False"

    def notify(self, topic, msg):
        print("msg: ", msg)
        jsonMsg=json.loads(msg)
        if jsonMsg == "True":
            print("Box has been occupied")
            self.box_is_open = "True"
            self.myPublish(self.box_is_open, self.sensor_location, self.sensor_type, self.sensor_unit) 
        else:
            print("Box has been emptied")
            self.box_is_open = "False"
            self.myPublish(self.box_is_open, self.sensor_location, self.sensor_type, self.sensor_unit)
    
if __name__ == "__main__":
    print("Starting Relaybox Sensor")
    sensor = SensorRelayBox()
    sensor.registration(sys.argv[1],"/shared/service_catalog_settings.json")
    
    if sensor.sensorID=='NOT FOUND' and sensor.topic=='NOT FOUND' and sensor.sensor_type =='NOT FOUND' and sensor.sensor_unit=='NOT FOUND'and sensor.sensor_location=='NOT FOUND' and sensor.broker=='NOT FOUND' and sensor.port=='NOT FOUND':
        print("Error: Service Catalog not found")
        exit()

    sensor.start() # start the sensor manager

    building_topic = str(sensor.buildingID)
    box_topic = str(sensor.boxID)
    sensor.mySubscribe("SaveThePycket/telegram/boxes/sensor_Relbox_" + building_topic + "_" + box_topic) 

    while True:    
        time.sleep(10)   
        