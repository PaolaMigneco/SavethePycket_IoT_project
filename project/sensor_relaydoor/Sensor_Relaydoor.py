#!/usr/bin/env python

import random 
import sys 
import time
sys.path.append('/shared')
from Sensor_Manager import *
class SensorRelayDoor(SensorManager):
    def __init__(self):
        SensorManager.__init__(self)
        self.door_is_open = "False"

    def notify(self, topic, msg):
        print("msg: ", msg)
        jsonMsg=json.loads(msg)
        if jsonMsg == "True":
            print("Opening door")
            self.door_is_open = "True"
            #relay door publishes that it is open
            self.myPublish(self.door_is_open, self.sensor_location, self.sensor_type, self.sensor_unit)


if __name__ == "__main__":
    print("Starting Relaydoor Sensor")
    sensor = SensorRelayDoor()
    sensor.registration("relay_door_settings.json","/shared/service_catalog_settings.json")
    
    if sensor.sensorID=='NOT FOUND' and sensor.topic=='NOT FOUND' and sensor.sensor_type =='NOT FOUND' and sensor.sensor_unit=='NOT FOUND'and sensor.sensor_location=='NOT FOUND' and sensor.broker=='NOT FOUND' and sensor.port=='NOT FOUND':
        print("Error: Service Catalog not found")
        exit()
    
    sensor.start() # start the sensor manager
    building_topic = "sensor_Reldoor_"+str(sensor.buildingID)
    sensor.mySubscribe("SaveThePycket/telegram/doors/"+building_topic) 
    while True:
        sensor.door_is_open = "False"
        sensor.myPublish(sensor.door_is_open, sensor.sensor_location, sensor.sensor_type, sensor.sensor_unit) # publish the sensor data
        time.sleep(100)   
        