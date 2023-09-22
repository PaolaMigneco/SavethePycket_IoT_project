#!/usr/bin/env python


import json
from datetime import datetime
import requests
import sys
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
import cherrypy
import pandas as pd
sys.path.append('/shared')
from MyMQTT import *



class MongoDBAdaptor:
    exposed = True
    def __init__(self, clientID, broker, port, db_name):
        self.settings = "./mongodb_adaptor_settings.json"
        with open(self.settings) as file:
            self.config = json.load(file) 

        self.service_settings = "/shared/service_catalog_settings.json" # settings file with ip, port of the service catalog
        with open(self.service_settings) as file:
            self.service_config = json.load(file)   

        registration_request = "http://" + self.service_config["ip_address"] + ":" + str(self.service_config["ip_port"]) + "/register" # registration request to the service catalog
        requ = requests.post(registration_request, data = json.dumps(self.config)) # register the mongodb adaptor in the service catalog
        self.clientID = clientID
        self.broker = broker
        self.port = port
        self.db_name = db_name 
        
        self.client_mqtt = MyMQTT(self.clientID, self.broker, self.port, self)

        uri = "mongodb+srv://savethepycketusername:savethepycketpassword@savethepycketdb.n4krejr.mongodb.net/?retryWrites=true&w=majority"

        # Create a new client and connect to the server
        self.mongoclient = MongoClient(uri, server_api=ServerApi('1'))

        # Send a ping to confirm a successful connection
        try:
            self.mongoclient.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)
        
        #Create the database if it does not exist
        if self.db_name not in self.mongoclient.list_database_names():
            self.db = self.mongoclient[self.db_name] # Create the database
            print(f"Database 'SaveThePycketDb' created successfully.")
        else:
            self.db = self.mongoclient[self.db_name]
            print(f"Database 'SaveThePycketDb' already exists.")

    def GET(self, *uri, **params): 
        #get data from mongodb through a query

        
        if len(uri)==1 and uri[0]=="measures" and len(params)==3:
            #query to mongodb


            buildingID = params["buildingID"]
            boxID = params["boxID"]

            selected_measure = params["sensor"]
            #Temperature%20and%20Humidity%20Sensor
            #strip the string from the %20
            selected_measure = selected_measure.replace("%20", "_")
            selected_measure_list = selected_measure.split("_")
            selected_measure_list = selected_measure_list[0].split(" ")
            selected_measure = selected_measure_list[0].lower() 
            print(f"Selected measure: {selected_measure}")

            def query(coll):
                result = self.db[coll].aggregate([
                                        
                        {
                            '$project': {
                                '_id': 0, 
                                'info_sensor.type': 1, 
                                'info_sensor.value': 1,
                                'info_sensor.unit': 1,  
                                'info_sensor.timestamp': 1, 
                                'info_sensor.buildingID': 1, 
                                'info_sensor.boxID': 1
                            }
                        }, {
                            '$match': {
                                'info_sensor.boxID': 1, 
                                'info_sensor.type': selected_measure
                            }
                        }, {
                            '$sort': {
                                'info_sensor.0.timestamp': -1
                            }
                        }, {
                            '$group': {
                                '_id': '$info_sensor.type', 
                                'value': {
                                    '$first': '$info_sensor.value'
                                }, 
                                'timestamp': {
                                    '$first': '$info_sensor.timestamp'
                                },
                                'unit': {
                                    '$first': '$info_sensor.unit'
                                }
                            }
                        }
                    
                ])
                documents = [doc for doc in result]
                # Serialize the list of dictionaries to JSON
                result_json = json.dumps(documents, indent=4)
                # Print the JSON string
                return result_json

            res_building="Building"+buildingID
            
            result_json=query(res_building)
            result = json.loads(result_json)
            measure = result[0]['value'][0]
            unit = result[0]['unit'][0]
            unix_timestamp = result[0]['timestamp'][0]
            unix_timestamp = unix_timestamp.split(".")[0]
            # Convert timestamp to a datetime object
            dt = datetime.fromtimestamp(int(unix_timestamp))
            timestamp = dt.strftime('%H:%M:%S')

            df_dict={"measure":round(measure,2),"unit":unit, "timestamp": timestamp}

        elif len(uri)==1 and uri[0]=="url":  
            df_dict={"url": "mongodb+srv://savethepycketusername:savethepycketpassword@savethepycketdb.n4krejr.mongodb.net/?retryWrites=true&w=majority" }

        
        return json.dumps(df_dict)
  
            
    def notify(self, topic, msg):
        
        msgJson = json.loads(msg)
        buildingID = msgJson["info_sensor"][0]["buildingID"]
        collection_name = "Building"+str(buildingID) # Find the collection name from the buildingID

        # Create a collection if it does not exist according to the buildingID. 
        # The idea is having a collection for each building.
        if collection_name not in self.db.list_collection_names():
            collection = self.db.create_collection(collection_name)
            print(f"Collection '{collection_name}' created successfully.")
        else:
            collection = self.db[collection_name]
            print(f"Collection '{collection_name}' already exists.")        

        # Insert the measurement in the collection with all the information, such as the buildingID, the boxID, the type...
        collection.insert_one(msgJson)

    def start(self, topic):
        self.client_mqtt.start()
        self.client_mqtt.mySubscribe(topic)
    
    def stop(self):
        self.client_mqtt.stop()

def info_mqtt(service_settings):
    with open(service_settings) as f: # get the settings of the service catalog
            data_service = json.load(f)
            ip_address = data_service["ip_address"]
            ip_port = data_service["ip_port"]  
    info_request = "http://" + ip_address + ":" + str(ip_port) + "/mqtt_connection" # request of information to the service catalog about the mqtt connection
    mqtt_info = requests.get(info_request) #get the broker ip and port of the mqtt connection
    moqtt_info_dict = mqtt_info.json()
    broker_mqtt = moqtt_info_dict["broker"]
    broker_port_mqtt = moqtt_info_dict["broker_port"]
    return broker_mqtt, broker_port_mqtt

if __name__ == "__main__":

    service_settings = "/shared/service_catalog_settings.json"
    broker_mqtt, broker_port_mqtt = info_mqtt(service_settings)

    mongodb_adaptor = MongoDBAdaptor("MongoDBAdaptor", broker_mqtt, broker_port_mqtt, "SaveThePycketDb")
    mongodb_adaptor.start("SaveThePycket/sensors/+")

    with open("./mongodb_adaptor_settings.json") as file:
        mongodb_info = json.load(file)
        
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        }
    }
    cherrypy.tree.mount(mongodb_adaptor, '/', conf)
    cherrypy.config.update(conf)
    cherrypy.config.update({'server.socket_host':mongodb_info["ip_address"]})
    cherrypy.config.update({'server.socket_port': mongodb_info["ip_port"]})
    cherrypy.engine.start()
    cherrypy.engine.block() 

    