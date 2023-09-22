#!/usr/bin/env python

import random 
import sys 
import time
sys.path.append('/shared')
from Sensor_Manager import *
if __name__ == "__main__":
    print("Sensor Temp and Hum")
    sensor1 = SensorManager()
    
    sensor1.registration(sys.argv[1],"/shared/service_catalog_settings.json")
   
    
    if sensor1.sensorID=='NOT FOUND' and sensor1.topic=='NOT FOUND' and sensor1.sensor_type =='NOT FOUND' and sensor1.sensor_unit=='NOT FOUND'and sensor1.sensor_location=='NOT FOUND' and sensor1.broker=='NOT FOUND' and sensor1.port=='NOT FOUND':
        print("Error: Service Catalog not found")
        exit()
    sensor1.start() # start the sensor manager

    temp_ref = 20 # base temperature
    hum_ref = 35 # base humidity
    while True:

        temp1 = random.uniform(temp_ref-0.5, temp_ref+0.5)

        print("temp1: ", temp1)
        unit_temp = "Celsius"
        type_meas_temp = "temperature" # generate a random temperature around the base temperature 
        print(f"Publishing temperature: {temp1} on {sensor1.topic}")

        sensor1.myPublish(temp1, sensor1.sensor_location, type_meas_temp, unit_temp) # publish the temperature 

        hum1 = random.uniform(hum_ref-5, hum_ref+5)
        print("hum1: ", hum1)
        unit_hum = "%"
        type_meas_hum = "humidity" # generate a random humidity around the base humidity 

        sensor1.myPublish(hum1, sensor1.sensor_location, type_meas_hum ,unit_hum) # publish the humidity
        time.sleep(10)