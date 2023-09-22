#!/usr/bin/env python


import json
import cherrypy

class ServiceCatalog(): 

    exposed = True

    def __init__(self):
        self.settings = "./service_catalog_settings.json" # default settings file with ip, port
        with open(self.settings) as file:
            self.config = json.load(file)
        
        self.catalog = "services.json"
        with open(self.catalog, "w") as outfile: # create the file if it does not exist
            outfile.write(json.dumps({
                "services": [{
            "id": "mqtt_connection",
            "broker": "test.mosquitto.org",
            "broker_port": 1883
        }]
            }))

        with open(self.catalog) as file:
            self.services = json.load(file)

    def GET(self, *uri, **params): # GET to the service catalog in order to get the service information
        if len(uri) == 0: # return all services
            return self.services["services"] 
        elif len(uri) == 1: # return one service information
            for service in self.services["services"]:#look for the service in the list of services
                if service["id"] == uri[0]:
                    return json.dumps(service)
            raise cherrypy.HTTPError(404, "Service not found") # raise a 404 error with a message that the service is not found
        else:
            raise cherrypy.HTTPError(402, "Invalid request") # raise a 402 error with a message that the request is invalid

    def POST(self, *uri, **params): # POST to the service catalog in order to register a new service
        if len(uri) == 1 and uri[0] == "register": # register new service in the catalog 
            body = json.loads(cherrypy.request.body.read()) # get the body of the request
            for service in self.services["services"]:
                # check if service already exists
                if service["id"] == body["id"]: 
                    # raise a 402 error with a message that the service already exists
                    raise cherrypy.HTTPError(402, "Service already exists")
            new_service = {"id":body["id"],"ip_address":body["ip_address"],"ip_port":body["ip_port"]}
            self.services["services"].append(new_service) # add service to the list of services
            with open(self.catalog, "w") as outfile: # save the new list of services
                json.dump(self.services, outfile, indent=4) 
            return "Service registered" 
        else:
            raise cherrypy.HTTPError(402, "Invalid request") 

    def PUT(self, *uri, **params): # PUT to the service catalog in order to update a service
        if len(uri) == 1: # update service with id
            body = json.loads(cherrypy.request.body.read()) # get the body of the request
            for service in self.services["services"]:
                if service["id"] == uri[0]: # service found
                    service = body # update service
                    with open(self.catalog, "w") as outfile:
                        json.dump(self.services, outfile, indent=4)
                   
                    return "Service updated", 200
            return "Service not found", 404
        else:
            return "Invalid request", 400

    def DELETE(self, *uri, **params): # DELETE to the service catalog in order to delete a service
        if len(uri) == 1: # delete service with id
            for service in self.services["services"]:
                if service["id"] == uri[0]:
                    self.services["services"].remove(service)
                    with open(self.catalog, "w") as outfile:
                        json.dump(self.services, outfile, indent=4)
                    return "Service deleted", 200
            return "Service not found", 404
        else:
            return "Invalid request", 400

if __name__ == '__main__':
    print("SERVICE CATALOG")
    with open("./service_catalog_settings.json") as file:
        service_info = json.load(file)
        
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        }
    }
    cherrypy.tree.mount(ServiceCatalog(), '/', conf)
    cherrypy.config.update(conf)
    cherrypy.config.update({'server.socket_host':service_info["ip_address"]})
    cherrypy.config.update({'server.socket_port': service_info["ip_port"]})
    cherrypy.engine.start()
    cherrypy.engine.block() 




