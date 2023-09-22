#!/usr/bin/env python
#Create a Resource Catalog for the IoT platform
import json
import cherrypy
import requests

class ResourceCatalog():  
    exposed = True

    def __init__(self):
        self.settings = "./resource_catalog_settings.json"

        with open(self.settings) as file:
            self.config = json.load(file)
            
        self.sensor_file = "resources.json" # file with the list of resources in the catalog
        with open(self.sensor_file, "w") as outfile: # create the file if it does not exist
            outfile.write(json.dumps({
                "building_sensors": [],
                "buildings": [],
                "boxes": [], 
                "box_sensors": [],
                "users": [],
                "admins":[]
            }))

        with open(self.sensor_file) as file:
            self.sensors = json.load(file) # initial empty list of resources in the catalog
        
        self.service_settings = "/shared/service_catalog_settings.json" # settings file with ip, port of the service catalog
        with open(self.service_settings) as file:
            self.service_config = json.load(file)
        
        registration_request = "http://" + self.service_config["ip_address"] + ":" + str(self.service_config["ip_port"]) + "/register" # registration request to the service catalog
        requ = requests.post(registration_request, data = json.dumps(self.config)) # register the resource catalog in the service catalog
    
    def POST(self, *uri, **params): # registration of a new resource in the catalog
        with open(self.sensor_file) as file:
            self.sensors = json.load(file)
        request_body = cherrypy.request.body.read()
        body = json.loads(request_body) # get the body of the request
        
        if len(uri) == 1 and uri[0] == "register_sensor":
            
            for sensor in self.sensors["building_sensors"]: # check if sensor already exists
                if sensor["sensorID"] == body["sensorID"]:
                    raise cherrypy.HTTPError(400, "Building sensor already exists")
                
            for sensor in self.sensors["box_sensors"]: # check if sensor already exists
                if sensor["sensorID"] == body["sensorID"]:
                    raise cherrypy.HTTPError(400, "Box sensor already exists")

            # check if a key of the sensor dictionary exists or not
            if "boxID" not in body: # if the sensor is a building sensor
                self.sensors["building_sensors"].append(body) 
            elif "boxID" in body: # if the sensor is a box sensor
                self.sensors["box_sensors"].append(body) 
                #check that the combination of boxID and buildingID is not already in the "boxes" list
                for box in self.sensors["boxes"]:
                    if box["buildingID"] == body["buildingID"] and box["boxID"] == body["boxID"]:
                        with open(self.sensor_file, "w") as outfile: # save the new list of sensors
                            json.dump(self.sensors, outfile, indent=4)  
                        return "Sensor registered, box already exists"
                self.sensors["boxes"].append({"buildingID":body["buildingID"], "boxID":body["boxID"], "status":"False"}) # add the box to the list of boxes   
            else:
                raise cherrypy.HTTPError(400, "Invalid request") 
            
            with open(self.sensor_file, "w") as outfile: # save the new list of sensors
                json.dump(self.sensors, outfile, indent=4) 
            
            
            return "Sensor registered"
        
        elif len(uri) == 1 and uri[0] == "register_building":
            
            for new_building in body["buildings"]:   
                if self.sensors["buildings"]!=[]:
                    for building in self.sensors["buildings"]:
                        if building["buildingID"] == new_building["buildingID"]:
                            raise cherrypy.HTTPError(400, "Building already exists")
                    self.sensors["buildings"].append(new_building) # add the new building to the list of buildings
                else:
                    self.sensors["buildings"].append(new_building)
            
            with open(self.sensor_file, "w") as outfile: # save the new list of resources
                json.dump(self.sensors, outfile, indent=4)
            
            return "Buildings registered"
        
        elif len(uri) == 1 and uri[0] == "register_user":
            
            for new_user in body["users"]:   
                if self.sensors["users"]!=[]:
                    for user in self.sensors["users"]:
                        if user["user_name"] == new_user["user_name"]:
                            raise cherrypy.HTTPError(400, "User already exists")
                    self.sensors["users"].append(new_user) # add the new user to the list of users
                else:
                    self.sensors["users"].append(new_user)
            
            with open(self.sensor_file, "w") as outfile: # save the new list of resources
                json.dump(self.sensors, outfile, indent=4)
            
            return "Users registered"
        elif len(uri) == 1 and uri[0] == "register_user_telegram":
            self.sensors["users"].append(body)
            with open(self.sensor_file, "w") as outfile: # save the new list of resources
                json.dump(self.sensors, outfile, indent=4)

        elif len(uri) == 1 and uri[0] == "register_admins":
            
            for new_admin in body["admins"]:   
                if self.sensors["admins"]!=[]:
                    for admin in self.sensors["admins"]:
                        if admin["admin_name"] == new_admin["admin_name"]:
                            raise cherrypy.HTTPError(400, "Admin already exists")
                    self.sensors["admins"].append(new_admin) # add the new admin to the list of the admins
                else:
                    self.sensors["admins"].append(new_admin)
            
            with open(self.sensor_file, "w") as outfile: # save the new list of resources
                json.dump(self.sensors, outfile, indent=4)
            
            return "Admin registered"

        else:
            raise cherrypy.HTTPError(400, "Invalid request") 

    def GET(self, *uri, **params): 
        with open(self.sensor_file) as file:
            self.sensors = json.load(file)        
        if len(uri) == 1 and uri[0] == "users":
            return json.dumps(self.sensors["users"])        
        elif len(uri) == 1 and uri[0] == "buildings":
            return json.dumps(self.sensors["buildings"])
        elif len(uri) == 1 and uri[0] == "admin":
            return json.dumps(self.sensors["admin"])
        elif len(uri) == 1 and uri[0] == "boxes":
            return json.dumps(self.sensors["boxes"])
        elif len(uri) == 1 and uri[0] == "box_sensors":
            return json.dumps(self.sensors["box_sensors"])
        elif len(uri) == 1 and uri[0] == "sensors":
            return json.dumps(self.sensors["box_sensors"])
        elif len(uri) == 1 and uri[0] == "resources":
            return json.dumps(self.sensors)
        elif len(uri) == 1 and uri[0] == "box_status" and len(params)==2: #see the status of a box
            print("Get status of box")
            boxID = params["boxID"]
            buildingID = params["buildingID"]
            print("boxID received by rc: ", boxID)
            print("buildingID received by rc: ", buildingID)
            for box in self.sensors["boxes"]:
                if box["boxID"]==int(boxID) and box["buildingID"] == int(buildingID):
                    #get the status of the box
                    status = box["status"]
                    print(f"STATUS OF THE BOX: {status}")
                    return json.dumps({"status":status})
        
    def PUT(self, *uri, **params): # update the information of a resource
        body = json.loads(cherrypy.request.body.read()) # get the body of the request
        if len(uri) == 1 and uri[0] == "user":
            #modify chatID of user sent in the uri inside the resource catalog
            for user in self.sensors["users"]:
                if user["user_name"] == body['user_name']:
                    #change the chatID of user
                    user["chatID"] = body['chatID']
                    with open(self.sensor_file, "w") as outfile:
                        json.dump(self.sensors, outfile, indent=4)
                    return "User modified", 200
            with open(self.sensor_file, "w") as outfile:
                json.dump(self.sensors, outfile, indent=4)
            return "User not found", 404
        elif len(uri)== 1 and uri[0] == "change_box_status" and len(params)==2:
            boxID = params["boxID"]
            buildingID = params["buildingID"]
            for box in self.sensors["boxes"]:
                if box["boxID"]==int(boxID) and box["buildingID"]==int(buildingID):
                    #change the status of the box
                    box["status"] = body
            with open(self.sensor_file, "w") as outfile:
                json.dump(self.sensors, outfile, indent=4)
    
    def GET_ALL(self): # get the list of resources in the catalog
        return json.dumps(self.sensors)

if __name__ == '__main__':
    print("RESOURCE CATALOG")
    with open("resource_catalog_settings.json") as outfile:
        resource_info = json.load(outfile)
    
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        }
    }
    cherrypy.tree.mount(ResourceCatalog(), '/', conf)
    cherrypy.config.update(conf)
    cherrypy.config.update({'server.socket_host': resource_info["ip_address"]})
    cherrypy.config.update({'server.socket_port': resource_info["ip_port"]})
    cherrypy.engine.start()
    cherrypy.engine.block()

