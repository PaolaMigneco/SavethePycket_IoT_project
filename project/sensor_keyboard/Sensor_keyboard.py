#!/usr/bin/env python

import random 
import sys 
import time

sys.path.append('/shared')
from Sensor_Manager import *


class SensorKeyboard(SensorManager):

    def __init__(self):
        SensorManager.__init__(self)

    def notify(self, topic, msg):
        topic_doorbell = topic.split("_") # split the topic of the doorbell in order to get the order userID  
        with open ("./code_postman.txt") as f:
            code = f.readline().strip()
        # now this code must be published on the topic of the keyboard in order to allow telegram to send this code to the user
        self.myPublish(code+"&"+topic_doorbell[-1], self.sensor_location, self.sensor_type, self.sensor_unit) 
        print(code+"&"+topic_doorbell[-1])

if __name__ == "__main__":
    print("Keyboard Sensor")
    sensor = SensorKeyboard()    
    sensor.registration("keyboard_settings.json","/shared/service_catalog_settings.json")
    
    if sensor.sensorID=='NOT FOUND' and sensor.topic=='NOT FOUND' and sensor.sensor_type =='NOT FOUND' and sensor.sensor_unit=='NOT FOUND'and sensor.sensor_location=='NOT FOUND' and sensor.broker=='NOT FOUND' and sensor.port=='NOT FOUND':
        print("Error: Service Catalog not found")
        exit()
        
    sensor.start() # start the sensor manager
    topic_to_subscribe = "SaveThePycket/sensors/doorbells/#" 
    sensor.mySubscribe(topic_to_subscribe) # subscribe to the topic of the doorbells 
    
    while True:
        time.sleep(1)


    