#!/usr/bin/env python

import json
import requests
import time


class BuildingManager(): # create a building manager class that registers the building in the resource catalog 
    def __init__(self, building_settings, service_catalog_settings):
        self.building_settings = building_settings
        self.service_settings = service_catalog_settings
        
    def registration(self):
        with open(self.building_settings) as f:
            data = json.load(f)
            
        #request to the service catalog about the resource catalog
        with open(self.service_settings) as f: # get the settings of the service catalog
            service_info = json.load(f)
            ip_service = service_info["ip_address"]
            service_port = service_info["ip_port"]
        info_request = "http://" + ip_service + ":" + str(service_port) + "/resource_catalog" # request of information to the service catalog about the resource catalog
        rc_info = requests.get(info_request) #get the ip address and port of resource catalog
        rc_info_dict = rc_info.json()
        ip_rc = rc_info_dict["ip_address"]
        port_rc = rc_info_dict["ip_port"]

        resource_request = "http://" + ip_rc + ":" + str(port_rc) + "/register_building"
        registration_req = requests.post(resource_request, data = json.dumps(data))
        print( str(registration_req.status_code)  + ": BUILDING REGISTRATION WAS SUCCESSFUL")


if __name__ == '__main__':
    building_manager = BuildingManager("building_settings.json", "/shared/service_catalog_settings.json")
    building_manager.registration()
    while True:
        time.sleep(1)
        
   


        
