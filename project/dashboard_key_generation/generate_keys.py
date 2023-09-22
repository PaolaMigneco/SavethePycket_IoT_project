#!/usr/bin/env python

import pickle 
from pathlib import Path
import json
import streamlit_authenticator as stauth
import requests
import time
import json
import requests
import sys
import os
import telebot
import time
sys.path.append('/shared')
from MyMQTT import *


def info_resource_cat (service_settings):
    with open(service_settings) as f: # get the settings of the service catalog
            data_service = json.load(f)
            ip_address = data_service["ip_address"]
            ip_port = data_service["ip_port"]  
    info_request = "http://" + ip_address + ":" + str(ip_port) + "/resource_catalog" # request of information to the service catalog about the resource catalog
    rc_info = requests.get(info_request) #get the ip address and port of resource catalog
    rc_info_dict = rc_info.json()
    ip_rc = rc_info_dict["ip_address"]
    port_rc = rc_info_dict["ip_port"]
    return ip_rc, port_rc

if __name__ == '__main__':
    service_settings = "/shared/service_catalog_settings.json"
    ip_rc, port_rc = info_resource_cat(service_settings)
    resource_request = "http://" + ip_rc + ":" + str(port_rc) + "/" + "resources"
    resources = requests.get(resource_request)
    data = resources.json()
    # Itera attraverso ogni oggetto utente nell'elenco e aggiungi il nome utente alla lista
    dict_data_users = []
    dict_data_admin=[]

    for user in data["users"]:
        for building in data["buildings"]:
            if user["buildingID"] == building["buildingID"]:
                user_data = {
                    "username": user["user_name"],
                    "buildingID": user["buildingID"],
                    "password": building["password"]
                }
                dict_data_users.append(user_data)
    print(dict_data_users)

    for admin in data["admins"]:
        admin_data = {
                    "adminname": admin["admin_name"],
                    "password": admin["password"],
                    "buildingID": admin["buildingID"] 
                }
        dict_data_admin.append(admin_data)
        
    print(dict_data_admin)
    #hashing password
    hashed_password_user = stauth.Hasher(user_data["password"] for user_data in dict_data_users).generate()
    hashed_password_admin = stauth.Hasher(admin_data["password"] for admin_data in dict_data_admin).generate()
    #after we have hashed password we will store in a folder 
    file_path= Path(__file__).parent / os.path.join('..','shared', 'hashed_user_pw.pickle')
    with file_path.open("wb") as file:
        pickle.dump(hashed_password_user, file)

    file_path= Path(__file__).parent / os.path.join('..','shared', 'hashed_admin_pw.pickle')
    with file_path.open("wb") as file:
        pickle.dump(hashed_password_admin, file)