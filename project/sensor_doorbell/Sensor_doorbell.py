#!/usr/bin/env python

import random 
import sys 
import time
sys.path.append('/shared')
from Sensor_Manager import *

class SensorDoorbell(SensorManager):
    def __init__(self):
        SensorManager.__init__(self)
        self.doorbell_is_ringing = "False"


if __name__ == "__main__":
    print("Doorbell sensor")
    sensor = SensorDoorbell()
    
    sensor.registration("doorbell_settings.json","/shared/service_catalog_settings.json")
    
    if sensor.sensorID=='NOT FOUND' and sensor.topic=='NOT FOUND' and sensor.sensor_type =='NOT FOUND' and sensor.sensor_unit=='NOT FOUND'and sensor.sensor_location=='NOT FOUND' and sensor.broker=='NOT FOUND' and sensor.port=='NOT FOUND':
        print("Error: Service Catalog not found")
        exit()
    sensor.start() # start the sensor manager
    sound_ref = 70 # base sound
    time.sleep(30) 
    while True:
        sound = random.uniform(sound_ref, sound_ref+20)
        # adding a threshold
        if sound > 75:
            sensor.myPublish(sound, sensor.sensor_location, sensor.sensor_type, sensor.sensor_unit) # publish the sound
            print("Doorbell is ringing!!!!", flush=True)
            time.sleep(60) 

         
