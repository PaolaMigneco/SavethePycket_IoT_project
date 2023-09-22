#!/usr/bin/env python

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
import matplotlib.pyplot as plt
import random
import time
import calendar
from datetime import datetime, timedelta
import numpy as np
from matplotlib import dates as mpl_dates
import matplotlib.ticker as plticker
import streamlit as st
import time
import json
import requests
#libraries to authentification
import pickle
from pathlib import Path
import streamlit_authenticator as stauth
import json
from streamlit_option_menu import option_menu
import os
from datetime import datetime
import matplotlib.dates as mdates
import statistics
import math
import sys
#sys.path.append('/shared')
#from MyMQTT import *

st.title(":package: SaveThePycket :package:")

def info_resource_cat(service_settings):
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

def info_mongodb(service_settings):
    with open(service_settings) as f: # get the settings of the service catalog
            data_service = json.load(f)
            ip_address = data_service["ip_address"]
            ip_port = data_service["ip_port"]  
    info_request = "http://" + ip_address + ":" + str(ip_port) + "/mongodb_adaptor" # request of information to the service catalog about the mongodb adaptor
    mongo_info = requests.get(info_request) #get the ip address and port of mongodb adaptor
    mongo_info_dict = mongo_info.json()
    ip_mongo = mongo_info_dict["ip_address"]
    port_mongo = mongo_info_dict["ip_port"]
    return ip_mongo, port_mongo

def convertion_ore_minuti_secondi(contatore_seconds):
    ore = contatore_seconds // 3600
    resto_seconds = contatore_seconds % 3600
    minuti = resto_seconds // 60
    secondi = resto_seconds % 60
    return ore,minuti,secondi

if __name__=="__main__":
    service_settings = "/shared/service_catalog_settings.json"
    settings = "./dashboard_settings.json"
    with open(settings) as file:
        config = json.load(file) 

    with open(service_settings) as file:
        service_config = json.load(file)   
    registration_request = "http://" + service_config["ip_address"] + ":" + str(service_config["ip_port"]) + "/register" # registration request to the service catalog
    requ = requests.post(registration_request, data = json.dumps(config)) # register the dashboard in the service catalog

    ip_rc, port_rc = info_resource_cat(service_settings)
    resource_request = "http://" + ip_rc + ":" + str(port_rc) + "/" + "resources"
    resources = requests.get(resource_request)
    data = resources.json()

    ip_mongo, port_mongo = info_mongodb(service_settings)
    mongo_request = "http://" + ip_mongo + ":" + str(port_mongo) + "/" + "url"
    url_mongo = requests.get(mongo_request)
    url_mongo = url_mongo.json()
    uri=url_mongo["url"]


    # take data from resource catalog of admin
    dict_data_admin = []
    for admin in data["admins"]:
        address_roads = []
        address_numbers=[]
        for building_id in admin["buildingID"]:
            for building in data["buildings"]:
                if building["buildingID"] == building_id:
                    address_roads.append(building["address_road"])
                    address_numbers.append(building["address_number"])
        admin_data = {
            "adminname": admin["admin_name"],
            "buildingID": admin["buildingID"],
            "address_road": address_roads,
            "address_number": address_numbers
        }
        dict_data_admin.append(admin_data)
    adminname=[admin_data["adminname"] for admin_data in dict_data_admin]

    file_path= Path(__file__).parent / os.path.join('..','shared', 'hashed_admin_pw.pickle')
    with file_path.open("rb") as file:
        hashed_admin_password= pickle.load(file)

    # take data from resource catalog of users
    dict_data_users = []
    for user in data["users"]:
        for building in data["buildings"]:
            if user["buildingID"] == building["buildingID"]:
                user_data = {
                    "username": user["user_name"],
                    "buildingID": user["buildingID"],
                    "chatID": user["chatID"],
                    "address_road": building["address_road"],
                    "address_number": building["address_number"]
                    
                }
                dict_data_users.append(user_data)  # Aggiungi l'oggetto user_data alla lista

    usernames = [user_data["username"] for user_data in dict_data_users]

    file_path= Path(__file__).parent / os.path.join('..','shared', 'hashed_user_pw.pickle')
    with file_path.open("rb") as file:
        hashed_user_password= pickle.load(file)

    #append dei due file hasher_user_pw e hashed_admin_pw
    hashed_password = hashed_admin_password + hashed_user_password
    username_total = adminname + usernames

    authenticator= stauth.Authenticate( username_total, username_total , hashed_password, "SaveThePycket", "abcdef", cookie_expiry_days=30)
    name, authentication_status, username = authenticator.login("Login", "main")

    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))

    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)

    db = client["SaveThePycketDb"]

    def query(coll):
        result = db[coll].aggregate([ {
                "$project":
                    {
                    "_id":0,
                    "info_sensor.type":1,
                    "info_sensor.value":1,
                    "info_sensor.timestamp":1,
                    "info_sensor.buildingID":1,
                    "info_sensor.boxID":1
            }
            },
        ])
        return pd.DataFrame(list(result))

    if authentication_status == False:
        st.error("User/password not valid. Please try again.")
    if authentication_status == None:
        st.warning("Please login to access the app.")
    if authentication_status == True:
        authenticator.logout("Logout", "sidebar")
        if username in adminname:
            st.sidebar.title(f":raised_hand_with_fingers_splayed: WELCOME {name.upper()}!")
            def query_all_collections(db):
                #prendi tutti i Building ID relativi a username
                building_id = None
                dict_data_admin_current={}
                collection_names =[]
                for admin_data in dict_data_admin:
                    if admin_data["adminname"] == username:
                        building_id = admin_data["buildingID"]
                        collection_names = ["Building"+str(num) for num in building_id]
                        break
                results = []

                for coll in collection_names:
                    result = query(coll)
                    results.append(result)

                combined_df = pd.concat(results, ignore_index=True)
                return combined_df
            admindf=query_all_collections(db)
            admindf=pd.json_normalize(admindf["info_sensor"])
            # normalizza i dati JSON in nuove colonne
            admindf_normalize = pd.json_normalize(admindf[0])

            # concatena i dati normalizzati al DataFrame originale
            dfadmin = pd.concat([admindf, admindf_normalize], axis=1)

            # rimuovi la colonna originale
            dfadmin = dfadmin.drop(0, axis=1)

            dfadmin["timestamp"] = dfadmin["timestamp"].astype(float).apply(datetime.fromtimestamp) # converte i timestamp in datetime
            dfadmin['timestamp'] = pd.to_datetime(dfadmin['timestamp'])

            # estrae la data e l'ora in due colonne separate
            dfadmin['data'] = dfadmin['timestamp'].dt.date
            dfadmin['ora'] = dfadmin['timestamp'].dt.time 
            dfadmin['ora'] = dfadmin['ora'].astype(str).str.split('.').str[0] # rimuove i millisecondi
            # rimuove la colonna "timestamp"
            dfadmin = dfadmin.drop('timestamp', axis=1)
            #visualize the building 
            st.title("_Building Info_")
            st.subheader("Here you can see the information about the buildings you are responsible for:")
            
            #per ogni buildingID del mio username, prendi l'indirizzo e mettilo in un menu a tendina
            admin_address = []
            admincomplete=[]
            for admin_data in dict_data_admin:
                if admin_data["adminname"] == username:
                    for i in range(len(admin_data['buildingID'])):
                        building_id = admin_data['buildingID'][i]
                        address_roads = admin_data['address_road'][i]
                        address_numbers = admin_data['address_number'][i]
                        admin_address.append(address_roads+ " "+str(address_numbers))
                        
                        # Create a dictionary for each entry and append it to admincomplete
                        admin_entry = {
                            "buildingID": building_id,
                            "address": address_roads + " " + str(address_numbers)
                        }
                        admincomplete.append(admin_entry)  # Append the dictionary to the list     
            admin_address.append("All")


            selected = option_menu(
                menu_title= "Select the building you want to visualize",
                options= admin_address,    
                default_index=0,
                orientation="horizontal")
            
            if selected == "All":
                st.success(":derelict_house_building: You have selected to visualize all the buildings :derelict_house_building:")
    
                df=dfadmin[dfadmin['type']=='relay']
                df["data"] = df["data"].astype(str) + " " + df["ora"].astype(str)
                df = df.drop('ora', axis=1)
                # Convertire la colonna "data" in un oggetto datetime
                df["data"] = pd.to_datetime(df["data"])
                df=df.sort_values(['buildingID','data'])
                df['value'] = df['value'].replace({'True': True, 'False': False}).astype(bool)
                fig1, ax = plt.subplots(figsize=(15, 10))
                building_ids = df['buildingID'].unique()  # Get unique building IDs from the DataFrame


                
                st.title(":derelict_house_building: STATUS OF BUILDING BOXES :derelict_house_building:")
                st.caption("Please, select how to visualize your data:")
                time_periods = ["Today", "Week", "Month"]
                selected_periods = st.radio("Select time period(s):", time_periods, key='struttura_1')

                if selected_periods == "Today":
                    start_date = pd.Timestamp.today() - pd.DateOffset(days=1)
                    df_period = df[df["data"] >= start_date]
                elif selected_periods == "Week":
                    start_date = pd.Timestamp.today() - pd.DateOffset(weeks=1)
                    df_period = df[df["data"] >= start_date]
                elif selected_periods == "Month":
                    start_date = pd.Timestamp.today() - pd.DateOffset(months=1)
                    df_period = df[df["data"] >= start_date]
                start_date = start_date.replace(microsecond=0)
                if df_period.empty:
                    st.warning("The period you have selected has no information to show")
                else:

                    grouped=df_period.groupby(['buildingID','data'])
                    df_period['alltrue'] =grouped["value"].transform(lambda x: x.all())
                    df_period['count']=grouped["alltrue"].transform(lambda x: x[x == True].count())

                    for building_id in building_ids:
                        building_data = df_period[df_period['buildingID'] == building_id]  # Filter data for the current building ID
                        
                        for item in admincomplete:
                            if item["buildingID"] == building_id:
                                selected_address = item["address"]
                                break
                        x_values = building_data["data"]
                        x_labels = x_values.dt.strftime('%Y-%m-%d %H:%M:%S')
                        y = building_data['alltrue'].astype(int)  # Convert 'alltrue' values to integers (0 or 1)
                        
                        ax.plot(x_values, y, label= selected_address)
                    ax.set_title('All the buildings')
                    plt.xticks(rotation=45)
                    plt.yticks([0, 1], ['Not all the boxes occupied', 'All the box occupied'])
                    plt.xlabel('ora')
                    plt.ylabel('value')
                    plt.legend()
                    plt.show()
                    st.pyplot(fig1)
                    


                

                st.title(":rotating_light: NUMBER OF OCCUPIED BOXES IN EACH BUILDING :rotating_light:")
                st.caption("Please, select how to visualize your data:")
                time_periods_building= ["Today", "Week", "Month"]
                selected_periods_building = st.radio("Select time period(s):", time_periods_building, key='struttura_2')
                fig2, ax = plt.subplots( figsize=(15, 10))
                building_ids = df['buildingID'].unique()  # Get unique building IDs from the DataFrame # Get unique building IDs from the DataFrame

                if selected_periods_building == "Today":
                    start_date_building = pd.Timestamp.today() - pd.DateOffset(days=1)
                    df_period = df[df["data"] >= start_date_building]
                elif selected_periods_building == "Week":
                    start_date_building = pd.Timestamp.today() - pd.DateOffset(weeks=1)
                    df_period = df[df["data"] >= start_date_building]
                elif selected_periods_building == "Month":
                    start_date_building = pd.Timestamp.today() - pd.DateOffset(months=1)
                    df_period = df[df["data"] >= start_date_building]
                start_date_building = start_date_building.replace(microsecond=0)
                if df_period.empty:
                    st.warning("The period you have selected has no information to show")
                else:
                
                    grouped=df_period.groupby(['buildingID','data'])
                    df_period['alltrue'] =grouped["value"].transform(lambda x: x.all())
                    df_period['count']=grouped["alltrue"].transform(lambda x: x[x == True].count())
                    
                    for building_id in building_ids:
                        building_data = df_period[df_period['buildingID'] == building_id]  # Filter data for the current building ID
                        #check for the maximum number of boxes in the building
                        max_number = building_data['boxID'].max()
                        x = building_data['data']
                        y = building_data['count'] 
                        

                        # Trova il building con il building_id specificato
                        matching_building = next((building for building in admincomplete if building['buildingID'] == building_id), None)

                        if matching_building:
                            # Prendi l'indirizzo associato al building_id
                            address = matching_building['address']
                            mask = (building_data['buildingID'] == building_id)
                            building_data.loc[mask, 'countvolte'] = ((building_data['alltrue'].loc[mask] & (building_data['alltrue'].loc[mask] != building_data['alltrue'].loc[mask].shift())) | (building_data['buildingID'].loc[mask] != building_data['buildingID'].loc[mask].shift())).cumsum()
                            count=(building_data['countvolte'].loc[(df['buildingID'] == building_id)].max())
                            if math.isnan(count):
                                st.warning(':warning: no data in  '+str(address).strip('[]').strip("''")+' :warning:')
                            else:
                                st.warning(':warning: The users of the building '+str(address).strip('[]').strip("''")+' cannot use the boxes for '+str(building_data['countvolte'].loc[(df['buildingID'] == building_id)].max())+' times, because all the boxes were occupied! :warning:')
                            # Ora puoi utilizzare l'indirizzo in altre operazioni
                            plt.plot(x, y, label='Number of boxes occupied wrt the '+ str(max_number)+' boxes in building '+ address)
                    plt.legend()
                            
                    st.pyplot(fig2)

                        
                           
                st.title(":100: PERCENTAGE OF OCCUPIED BOXES :100:")
                st.caption("Please, select how to visualize your data:")
                time_periods_building = ["Today", "Week", "Month"]
                selected_period_building = st.radio("Select a time period:", time_periods_building, index=0, key='struttura_10')
                building_ids = df['buildingID'].unique()  # Get unique building IDs from the DataFrame

                if selected_period_building:
                    if selected_period_building == "Today":
                        start_date_building = pd.Timestamp.today() - pd.DateOffset(days=1)
                    elif selected_period_building == "Week":
                        start_date_building = pd.Timestamp.today() - pd.DateOffset(weeks=1)
                    elif selected_period_building == "Month":
                        start_date_building = pd.Timestamp.today() - pd.DateOffset(months=1)
                    start_date_building = start_date_building.replace(microsecond=0)
                    df_period = df[df["data"] >= start_date_building]
                    
                    if df_period.empty:
                        st.warning("The period you have selected has no information to show")
                    else:
                        for building_id in building_ids:
                            if any(building['buildingID'] == building_id for building in admincomplete):
                                address = [building['address'] for building in admincomplete if building['buildingID'] == building_id]
                                subset = df_period[df_period['buildingID'] == building_id]  # Filter the DataFrame for the current building ID
                                percentage = round((subset['value'] == True).sum() / subset['value'].count() * 100, 2)
                                #se non ci sono dati avvisa l'utente

                                if  math.isnan(percentage):
                                    st.warning(' :warning:  ' + str(address).strip('[]').strip("''") + ' has no data to show. :warning:')
                                elif percentage < 50:
                                    st.warning(' :warning: The percentage of OCCUPIED BOXES in ' + str(address).strip('[]').strip("''") + ' is: ' + str(percentage) + '%' + ' Boxes are occupied less than half of the time. Perhaps you can consider lowering the number of boxes. :warning:')
                                elif percentage > 50 and percentage < 90:
                                    st.success('The percentage of OCCUPIED BOXES in ' + str(address).strip('[]').strip("''") + ' is: ' + str(percentage) + '%' + '. The number of boxes in your building is right')
                                else:
                                    st.warning(':warning: The percentage of OCCUPIED BOXES in ' + str(address).strip('[]').strip("''") + ' is: ' + str(percentage) + '%' + 'Boxes are used almost to the limit of their capacity. Perhaps it would be fair to consider buying a new one! :warning:')
            elif selected != "All":
                st.success(":derelict_house_building: You have selected to visualize the building: {} :derelict_house_building:".format(selected))
                #prendi il buildingID corrispondente all'indirizzo selezionato
                for admin_data in dict_data_admin:
                    if admin_data["adminname"] == username:
                        for i in range(len(admin_data['buildingID'])):
                            building_id = admin_data['buildingID'][i]
                            address_roads = admin_data['address_road'][i]
                            address_numbers = admin_data['address_number'][i]
                            if address_roads+ " "+str(address_numbers) == selected:
                                selected_building_id = building_id
                                break
                
                st.header("Here you can see the information about the building you have selected:")
                dfadmin = dfadmin[dfadmin['buildingID'] == selected_building_id]  #building selection

                st.title(":thermometer: :droplet: MEAN TEMPERATURE AND HUMIDITY IN THE BOXES :droplet: :thermometer: ")
                st.caption("Please, select how to visualize your data:")
                time_periods_building= ["Today", "Week", "Month"]
                selected_periods_building = st.radio("Select time period(s):", time_periods_building, key='struttura_3')

                if selected_periods_building == "Today":
                    start_date_building = pd.Timestamp.today() - pd.DateOffset(days=1)
                elif selected_periods_building == "Week":
                    start_date_building = pd.Timestamp.today() - pd.DateOffset(weeks=1)
                elif selected_periods_building == "Month":
                    start_date_building = pd.Timestamp.today() - pd.DateOffset(months=1)
                start_date_building = start_date_building.replace(microsecond=0)
                dfadmin_period = dfadmin[dfadmin["data"] >= start_date_building]
                dfadmin_period["data"] = pd.to_datetime(dfadmin_period["data"])

                
                if dfadmin_period.empty:
                    st.warning("The period you have selected has no information to show")
                else:
                    average_temperatures = dfadmin_period[dfadmin_period['type'] == 'temperature'].groupby(['buildingID', 'boxID']).mean()

                    for row in average_temperatures.itertuples():
                        building_id = row.Index[0]
                        box_id = row.Index[1]
                        temperature = round(row.value,2)
                        #controlla il buildingID e vedi a che address road e address number corrisponde
                        st.write(f":thermometer: The mean  temperature in the box {box_id} is: {temperature}°C")
                        if temperature > 25:
                                            st.warning(f":warning: ATTENTION :warning:\n The mean temperature in the box {box_id} is {temperature}°C, that is above the threshold!")
                                            
                        
                    average_humidity = dfadmin_period[dfadmin_period['type'] == 'humidity'].groupby(['buildingID', 'boxID']).mean()

                    for row in average_humidity.itertuples():
                        building_id = row.Index[0]
                        box_id = row.Index[1]
                        humidity = round(row.value,2)
                        #controlla il buildingID e vedi a che address road e address number corrisponde
                        st.write(f":droplet: The mean humidity in the box {box_id} is: {humidity}%")
                        if humidity > 45:
                                print(f":warning: ATTENTION  :warning: \n The mean humidity in the box {box_id} in: {address_roads} {address_numbers} is {humidity}%, that is above the threshold!")                



                
                
                st.title(":iphone: STATISTICS ON SAVETHEPYCKET USERS IN THE BUILDING :iphone:")
                countbuildingid=0
                countchatid=0
                for user_data in dict_data_users:
                    if user_data["buildingID"] == selected_building_id:
                        countbuildingid += 1
                        if user_data["chatID"] != 0:
                            countchatid += 1

                st.write(" :iphone: " + str(countchatid) + "   users have registered to SavethePycket in the building " +str(selected) )
                
                if st.button('Click to see the percentage of users who use SavethePycket in the building'):
                    

                    # Pie chart, where the slices will be ordered and plotted counter-clockwise:
                    labels = 'All the people in the building', 'SavethePycket users'
                    sizes = [countbuildingid, countchatid]
                    explode = (0, 0.1)  # only "explode" the 2nd slice 

                    fig1, ax1 = plt.subplots()
                    ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
                    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

                    st.pyplot(fig1)


                #visualizzo solo i dati relativi a led
                dfadmin_led = dfadmin[dfadmin['type'] == "relay"]
                dfadmin_led["data"] = dfadmin_led["data"].astype(str) + " " + dfadmin_led["ora"].astype(str)

                # Convertire la colonna "data" in un oggetto datetime
                dfadmin_led["data"] = pd.to_datetime(dfadmin_led["data"])
                dfadmin_led['value'] = dfadmin_led['value'].replace({'True': True, 'False': False}).astype(bool)
                dfadmin_led = dfadmin_led.sort_values(['data'])
                grouped = dfadmin_led.groupby(['data'])
                

                time_periods_building = ["Today", "Week", "Month"]
                selected_period_building = st.radio("Select time period(s):", time_periods_building, key='struttura_3bis')

                if selected_period_building == "Today":
                    start_date_building = pd.Timestamp.today() - pd.DateOffset(days=1)
                elif selected_period_building == "Week":
                    start_date_building = pd.Timestamp.today() - pd.DateOffset(weeks=1)
                elif selected_period_building == "Month":
                    start_date_building = pd.Timestamp.today() - pd.DateOffset(months=1)
                start_date_building = start_date_building.replace(microsecond=0)
                dfadmin_led_period = dfadmin_led[dfadmin_led["data"] >= start_date_building]
                if dfadmin_led_period.empty:
                    st.warning("The period you have selected has no information to show")
                else:
                    count_box_used=0
                    lista_valori = [int(valore) for valore in dfadmin_led_period["value"].tolist()]  
                    
                    for i in range(1, len(lista_valori)):
                        if lista_valori[i]==1:
                            if lista_valori[i-1]==0:
                                count_box_used= count_box_used+1
                        
                    st.write("In the building the boxes were used " + str(count_box_used) + " times")

                    
                    if countchatid>0:
                        st.write("The average usage rate of the application per each user is"+ str( round( (count_box_used/countchatid), 2))) 


                #reset index
                dfadmin_led.reset_index(drop=True, inplace=True)
                dfadmin_led['alltrue'] = grouped['value'].transform(lambda x: x.all())

                st.title(":100: PERCENTAGE OF OCCUPATION OF THE BOXES IN THE BUILDING :100:")

                time_periods_building = ["Today", "Week", "Month"]
                selected_period_building = st.radio("Select time period(s):", time_periods_building, key='struttura_4')

                if selected_period_building == "Today":
                    start_date_building = pd.Timestamp.today() - pd.DateOffset(days=1)
                elif selected_period_building == "Week":
                    start_date_building = pd.Timestamp.today() - pd.DateOffset(weeks=1)
                elif selected_period_building == "Month":
                    start_date_building = pd.Timestamp.today() - pd.DateOffset(months=1)
                start_date_building = start_date_building.replace(microsecond=0)
                dfadmin_led_period = dfadmin_led[dfadmin_led["data"] >= start_date_building]
                if dfadmin_led_period.empty:
                    st.warning("The period you have selected has no information to show")
                else:

                    # Calculate the percentage of time boxes are occupied within the selected period
                    percentuale = round((dfadmin_led_period['value'] == True).sum() / len(dfadmin_led_period['value']) * 100, 2)

                    st.write(f":100: Boxes are occupied {percentuale}% of the time within the selected period.")

                    if percentuale < 50:
                        st.warning(":warning: Boxes are occupied less than half of the time. Perhaps you can consider lowering the number of boxes. :warning:")
                    elif percentuale > 50 and percentuale < 90:
                        st.success("The number of boxes in your building is right")
                    else:
                        st.warning(":warning: Boxes are used almost to the limit of their capacity. Perhaps it would be fair to consider buying a new one! :warning:")
                
                ######################

                dfadmin_led["data"] = pd.to_datetime(dfadmin_led["data"])


                # Define a function to calculate the average time difference of stay
                def calculate_average_difference(group):
                    if group["value"].any():
                        start_time = None
                        end_time = None
                        for index, row in group.iterrows():
                            if row["value"]:
                                if start_time is None:
                                    start_time = row["data"]
                            elif start_time is not None:
                                end_time = row["data"]
                                break  # Stop when the first False value is encountered

                        if start_time is not None and end_time is not None:
                            average_difference = end_time - start_time
                        else:
                            average_difference = pd.Timedelta(0)  # Only one True value or no valid interval

                        return average_difference
                    else:
                        return pd.Timedelta(0)  # Return 0 if no True values in the group

                    

                # AVERAGE TIME OF STAY IN THE BOXES
                st.title(":package: AVERAGE TIME OF STAY IN THE BOXES :package:")

                st.caption("Please, select how to visualize your data:")
                time_periods_building= ["Today", "Week", "Month"]
                selected_periods_building = st.radio("Select time period(s):", time_periods_building, key='struttura_5')

                if selected_periods_building == "Today":
                    start_date_building = pd.Timestamp.today() - pd.DateOffset(days=1)
                elif selected_periods_building == "Week":
                    start_date_building = pd.Timestamp.today() - pd.DateOffset(weeks=1)
                elif selected_periods_building == "Month":
                    start_date_building = pd.Timestamp.today() - pd.DateOffset(months=1)
                start_date_building = start_date_building.replace(microsecond=0)
                dfadmin_led_period = dfadmin_led[dfadmin_led["data"] >= start_date_building]
                dfadmin_led_period["data"] = pd.to_datetime(dfadmin_led_period["data"])


                #reindex group
                average_per_box = dfadmin_led_period.groupby(['buildingID', 'boxID']).apply(calculate_average_difference)
                average_per_box= average_per_box.apply(lambda avg_time: avg_time.floor('s'))
                # Print the average time difference of stay for each box
                selected_box = st.selectbox("Select a box:", dfadmin_led_period["boxID"].unique(), key='struttura_6')

                # Check if a box is selected
                if selected_box:
                    
                    # Filter the average_per_box DataFrame for the selected box
                    selected_box_average = average_per_box[average_per_box.index.get_level_values('boxID') == selected_box]

                    # Print the average time difference for the selected box
                    if not selected_box_average.empty:
                        average = selected_box_average.iloc[0]  # Get the average time difference for the selected box

                        if average == pd.Timedelta(0):
                            st.write(f"Box {selected_box}: 0 seconds")
                        else:
                            days = average.days
                            total_seconds = average.seconds
                            hours = total_seconds // 3600
                            minutes = (total_seconds % 3600) // 60
                            seconds = total_seconds % 60

                            if days == 0:
                                if hours == 0:
                                    if minutes == 0:
                                        st.write(f"Box {selected_box}: {seconds} seconds")
                                    else:
                                        st.write(f"Box {selected_box}: {minutes} minutes and {seconds} seconds")
                                else:
                                    st.write(f"Box {selected_box}: {hours} hours, {minutes} minutes and {seconds} seconds")
                            else:
                                st.write(f"Box {selected_box}: {days} days, {hours} hours, {minutes} minutes and {seconds} seconds")

                            # Calculate the overall average considering all boxes
                        averagetot = average_per_box.mean()
                        st.write(averagetot)
                    
                    
                        if averagetot == pd.Timedelta(0):
                            print("The overall average time of stay within the boxes for the selected period is: 0 seconds")
                        else:
                            days_tot = averagetot.days
                            total_seconds_tot = averagetot.seconds
                            hours_tot = total_seconds_tot // 3600
                            minutes_tot = (total_seconds_tot % 3600) // 60
                            seconds_tot = total_seconds_tot % 60

                            # Formatting the overall average
                            if days_tot == 0:
                                if hours_tot == 0:
                                    if minutes_tot == 0:
                                        st.write("The overall average time of stay within the boxes for the selected period is:", seconds_tot, "seconds")
                                    else:
                                        st.write("The overall average time of stay within the boxes for the selected period is:", minutes_tot, "minutes and", seconds_tot, "seconds")
                                else:
                                    st.write("The overall average time of stay within the boxes for the selected period is:", hours_tot, "hours,", minutes_tot, "minutes and", seconds_tot, "seconds")
                            else:
                                st.write("The overall average time of stay within the boxes for the selected period is:", days_tot, "days,", hours_tot, "hours,", minutes_tot, "minutes and", seconds_tot, "seconds")

                    else:
                            st.warning("There is no data for the selected box in the chosen period")

                
                else:
                    st.warning("No box selected")


                    
                st.title(":rotating_light: STATUS OF BOXES :rotating_light:")

                st.caption("Please, select how to visualize your data:")
                time_periods_building= ["Today", "Week", "Month"]
                selected_periods_building = st.multiselect("Select time period(s):", time_periods_building, key='struttura_7')

                for period_building in selected_periods_building:
                    if period_building == "Today":
                        start_date_building = pd.Timestamp.today() - pd.DateOffset(days=1)
                    elif period_building == "Week":
                        start_date_building = pd.Timestamp.today() - pd.DateOffset(weeks=1)
                    elif period_building == "Month":
                        start_date_building = pd.Timestamp.today() - pd.DateOffset(months=1)
                    start_date_building = start_date_building.replace(microsecond=0)
                    dfadmin_led_period = dfadmin_led[dfadmin_led["data"] >= start_date_building]
                    if dfadmin_led_period.empty:
                        st.warning("The period you have selected has no information to show")

                    else:
                
                        fig2, ax = plt.subplots(figsize=(15, 10))
                        if period_building == "Today":
                            ax.plot(dfadmin_led_period['ora'], dfadmin_led_period['alltrue'], color='red', marker='o', linestyle='dashed', linewidth=2, markersize=12)
                        else:
                            ax.plot(dfadmin_led_period['data'], dfadmin_led_period['alltrue'], color='red', marker='o', linestyle='dashed', linewidth=2, markersize=12)
                        # Set labels, title, and other plot configurations
                        ax.set_xlabel('Time')
                        ax.set_ylabel('All Boxes Occupied')
                        ax.set_title('All Boxes Occupied in Building ' + str(selected_building_id) + ' - ' + str(selected))
                        # Set y-axis ticks and labels
                        ax.set_yticks([0, 1])
                        ax.set_yticklabels(['False', 'True'])
                        # Display the plot in Streamlit
                        st.pyplot(fig2)
                
                percentuale=(dfadmin_led['value'].sum() / len(dfadmin_led)) * 100
                
                st.title(" :ballot_box_with_check: NUMBER OF OCCUPIED BOXES  :ballot_box_with_check:")
                st.caption("Please, select how to visualize your data:")
                time_periods_building= ["Today", "Week", "Month"]
                selected_periods_building = st.multiselect("Select time period(s):", time_periods_building, key='struttura_8')

                for period_building in selected_periods_building:
                    if period_building == "Today":
                        start_date_building = pd.Timestamp.today() - pd.DateOffset(days=1)
                    elif period_building == "Week":
                        start_date_building = pd.Timestamp.today() - pd.DateOffset(weeks=1)
                    elif period_building == "Month":
                        start_date_building = pd.Timestamp.today() - pd.DateOffset(months=1)
                    start_date_building = start_date_building.replace(microsecond=0)
                    dfadmin_led_period = dfadmin_led[dfadmin_led["data"] >= start_date_building]
                    if dfadmin_led_period.empty:
                        st.warning(f"The period you have selected has no information to show for {period_building}")
                    else:
                        dfadmin_led_period['count'] = dfadmin_led_period.groupby('data')['alltrue'].transform(lambda x: x[x == True].count())

                        
                        fig3, ax = plt.subplots(figsize=(15, 10))
                        if period_building == "Today":
                            ax.plot(dfadmin_led_period['ora'], dfadmin_led_period['alltrue'], color='red', marker='o', linestyle='dashed', linewidth=2, markersize=12)
                        else:
                            ax.plot(dfadmin_led_period['data'], dfadmin_led_period['alltrue'], color='red', marker='o', linestyle='dashed', linewidth=2, markersize=12)
                        ax.set_xlabel('ora')
                        ax.set_ylabel('# occupied box')
                        ax.set_title('num box occupied')
                        ax.set_yticks(np.arange(0, max(dfadmin_led['boxID'])+1, 1))
                        ax.legend()
                        st.pyplot(fig3)
                        # Incrementa il count ogni volta che cambia lo stato di 'alltrue'
                        #se il primo valore è true allora il count parte da 1
                        dfadmin_led_period['countvolte'] = (dfadmin_led_period['alltrue'] & (dfadmin_led_period['alltrue'] != dfadmin_led_period['alltrue'].shift())).cumsum()

                        
                        st.warning(':warning: Users were unable to use the boxes in '+str(selected)+' for '+str(dfadmin_led_period['countvolte'].max())+' times! :warning:')




        elif username in usernames:
            st.sidebar.title(f":raised_hand_with_fingers_splayed: WELCOME {name.upper()}!")
            st.caption(f"Hello {name.upper()},  you are in your home page!")

            #DEFINITION OF THE QUERY
            building_id = None
            for user_data in dict_data_users:
                if user_data["username"] == username:
                    building_id = user_data["buildingID"]
                    address_road=user_data["address_road"]
                    number_road=user_data["address_number"]
                    break
            num_building=building_id  #LO USERNAME DEVE ESSERE UGUALE AL NOME DELLA COLLECTION

            res_building="Building"+str(num_building)
            res=query(res_building)

            # CREAZIONE DEL DATAFRAME
            res=pd.json_normalize(res["info_sensor"])
            # normalizza i dati JSON in nuove colonne
            res_normalized = pd.json_normalize(res[0])

            # concatena i dati normalizzati al DataFrame originale
            df = pd.concat([res, res_normalized], axis=1)
            # rimuovi la colonna originale
            df = df.drop(0, axis=1)
            df["timestamp"] = df["timestamp"].astype(float).apply(datetime.fromtimestamp) # converte i timestamp in datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            # estrae la data e l'ora in due colonne separate
            df['data'] = df['timestamp'].dt.date
            df['ora'] = df['timestamp'].dt.time 
            df['ora'] = df['ora'].astype(str).str.split('.').str[0] # rimuove i millisecondi
            # rimuove la colonna "timestamp"
            df = df.drop('timestamp', axis=1)

            #WORKING WITH STREAMLIT
            current_building=int(df["buildingID"][0])
            #TEMPERATURE
            #prendo il numero delle boxes dal numero massimo di boxID
            df = df[df['boxID'] != '']
            df['boxID'] = df['boxID'].astype(int)

            boxes=int(df["boxID"].max())
            #crea un array da 1 al numero di boxes
            boxes=np.arange(1,boxes+1)
            df['data'] = df['data'].astype(str)
            df['ora'] = df['ora'].astype(str)
            df['data'] = df['data'] + ' ' + df['ora']
            df['data'] = pd.to_datetime(df['data'], format='%Y-%m-%d %H:%M:%S')
        
            st.header("You are visualizing the building number " + str(current_building) + " in " + address_road + " " + str(number_road))
            state_box= st.selectbox("*Select the number of the box you want to visualize*",boxes,key=2)
            st.success("You selected the box number: " + str(state_box))

            list_sensor=["Temperature","Humidity", "Weight", "Status of the box"]

            for i in range(len(boxes)):
                if state_box==boxes[i]:

                    state_box=st.radio(":red[Choose the sensor you want to visualize:]", list_sensor ,key=3)
                    #''''''''''''''''''''''''temperature''''''''''''''''''''''''''''  
                    if state_box == "Temperature":
                        st.header(":thermometer: TEMPERATURE :thermometer:")
                        st.subheader("Temperature in the current box:")

                        current_box = boxes[i]
                        current_box_data = df[
                            (df["boxID"] == current_box)
                            & (df["type"] == "temperature")
                            & (df["buildingID"] == current_building)
                        ]

                        last_value = round(current_box_data["value"].iloc[-1], 2)
                        last_data= current_box_data["data"].iloc[-1]
                        st.success(f"The last registered temperature of the box is: {last_value} °C")
                        st.text(f"Recorded on {last_data}")
                        if last_value > 28:
                            st.warning(f":warning: ATTENTION :warning:\n The temperature in the box {current_box} is above the threshold!")

                        st.caption("Please, select how to visualize your data:")
                        time_periods = ["Today", "Week", "Month"]
                        selected_periods = st.multiselect("Select time period(s):", time_periods)

                        for period in selected_periods:
                            if period == "Today":
                                start_date = pd.Timestamp.today() - pd.DateOffset(days=1)
                            elif period == "Week":
                                start_date = pd.Timestamp.today() - pd.DateOffset(weeks=1)
                            elif period == "Month":
                                start_date = pd.Timestamp.today() - pd.DateOffset(months=1)
                            start_date = start_date.replace(microsecond=0)

                            df_period = current_box_data[current_box_data["data"] >= start_date]
                            if df_period.empty:
                                st.warning("The period you have selected has no information to show")
                            else:
                                mean_temp = round(df_period["value"].mean(), 2)
                                st.write(f"The mean temperature of the box {current_box} for the {period.lower()} period is: {mean_temp} °C")

                                fig, ax = plt.subplots()
                                if period == "Today":                                
                                    ax.plot(df_period["ora"], df_period["value"], label=f"Temperature in the box {current_box}")
                                else:
                                    ax.plot(df_period["data"], df_period["value"], label=f"Temperature in the box {current_box}")

                                ax.legend()
                                ax.xaxis.set_major_locator(plt.MaxNLocator(6))  # Limit the number of x-axis ticks for readability
                                plt.grid()
                                plt.xlabel("Time")
                                plt.ylabel("Temperature (°C)")
                                plt.xticks(rotation=45)
                                plt.title(f"Temperature in the box {current_box} for the {period.lower()} period")
                                st.pyplot(fig)
                            

                        
                        #''''''''''''''''''''''''humidity''''''''''''''''''''''''''''  
                    if state_box == "Humidity":
                        st.header(":droplet: HUMIDITY :droplet:")
                        st.subheader("Humidity in the Boxes:")

                        current_box = boxes[i]
                        current_box_data = df[
                            (df["boxID"] == current_box)
                            & (df["type"] == "humidity")
                            & (df["buildingID"] == current_building)
                        ]


                        last_value = round(current_box_data["value"].iloc[-1], 2)
                        last_data= current_box_data["data"].iloc[-1]
                        
                        st.success(f"The last registered humidity of the box is: {last_value} %")
                        st.text(f"Recorded on {last_data}")

                        st.caption("Please, select how to visualize your data:")
                        time_periods = ["Today", "Week", "Month"]
                        selected_periods = st.multiselect("Select time period(s):", time_periods)

                        for period in selected_periods:
                            if period == "Today":
                                start_date = pd.Timestamp.today() - pd.DateOffset(days=1)
                            elif period == "Week":
                                start_date = pd.Timestamp.today() - pd.DateOffset(weeks=1)
                            elif period == "Month":
                                start_date = pd.Timestamp.today() - pd.DateOffset(months=1)
                            start_date = start_date.replace(microsecond=0)

                            df_period = current_box_data[current_box_data["data"] >= start_date]
                            if df_period.empty:
                                st.warning("The period you have selected has no information to show")
                            else:
                                mean_period = round(df_period["value"].mean(), 2)
                                
                                st.write(
                                    f"The mean humidity of the box {current_box}  for the {period.lower()} period is: {mean_period} %"
                                )

                                fig, ax = plt.subplots()
                                if period == "Today":                                
                                    ax.plot(df_period["ora"], df_period["value"], label=f"Humidity in the box {current_box}")
                                    
                                else:
                                    ax.plot(df_period["data"], df_period["value"], label=f"Humidity in the box {current_box}")
                                    
                                ax.legend()
                                ax.xaxis.set_major_locator(plt.MaxNLocator(6))  # Limit the number of x-axis ticks for readability
                                plt.grid()
                                plt.xlabel("Time")
                                plt.ylabel("Humidity (%)")
                                plt.xticks(rotation=45)
                                plt.title(f"Humidity in the box {current_box} for the {period.lower()} period")
                                st.pyplot(fig)


                        #''''''''''''''''''''''''weight''''''''''''''''''''''''''''  
                    if state_box == "Weight":
                        st.header(":man-lifting-weights: WEIGHT :man-lifting-weights:")
                        st.subheader("Weight in the Box:")

                        current_box = boxes[i]
                        current_box_data = df[
                            (df["boxID"] == current_box)
                            & (df["type"] == "weight")
                            & (df["buildingID"] == current_building)
                        ]

                        last_value = current_box_data["value"].iloc[-1]
                        last_data= current_box_data["data"].iloc[-1]
                        now = datetime.now()

                            # Definisci un intervallo di 1 minuto
                        one_minute_ago = now - timedelta(minutes=1)
                        if last_value == 0:
                            if one_minute_ago <= last_data <= now:
                                st.error("the box is empty")
                                st.text(f"Recorded on {last_data}")
                            else:
                                st.error("the box was empty")
                                st.text(f"Recorded on {last_data}")
                            
                        else:

                            st.success(f"The last registered weight of the box is: {round(last_value,2)} kg")
                            st.text(f"Recorded on {last_data}")

                        st.caption("Please, select how to visualize your data:")
                        time_periods = ["Today", "Week", "Month"]
                        selected_periods = st.multiselect("Select time period(s):", time_periods)

                        for period in selected_periods:
                            if period == "Today":
                                start_date = pd.Timestamp.today() - pd.DateOffset(days=1)
                            elif period == "Week":
                                start_date = pd.Timestamp.today() - pd.DateOffset(weeks=1)
                            elif period == "Month":
                                start_date = pd.Timestamp.today() - pd.DateOffset(months=1)

                            start_date = start_date.replace(microsecond=0)

                            df_period = current_box_data[current_box_data["data"] >= start_date]
                            if df_period.empty:
                                st.warning("The period you have selected has no information to show")
                            else:

                                # Filtra i valori diversi da zero
                                non_zero_values = df_period[df_period["value"] != 0]["value"]

                                # Calcola la media dei valori unici diversi da zero
                                if len(non_zero_values) > 0:
                                    mean_wg_period = round(np.mean(non_zero_values.unique()), 2)
                                else:
                                    mean_wg_period = 0

                                st.write(
                                    f"The mean weight of the box {current_box}  for the {period.lower()} period is: {mean_wg_period} kg"
                                )

                                fig, ax = plt.subplots()
                                if period == "Today":                                
                                    ax.plot(df_period["ora"], df_period["value"], label=f"Weight in the box{current_box}")
                                else:
                                    ax.plot(df_period["data"], df_period["value"], label=f"Weight in the box {current_box}")
                                
                                ax.legend()
                                ax.xaxis.set_major_locator(plt.MaxNLocator(6))  # Limit the number of x-axis ticks for readability
                                plt.grid()
                                plt.xlabel("Time")
                                plt.ylabel("Weight (kg)")
                                plt.xticks(rotation=45)
                                plt.title(f"Weight in the box {current_box} for the {period.lower()} period")
                                st.pyplot(fig)



                    #''''''''''''''''''''''''led''''''''''''''''''''''''''''      
                    if state_box == "Status of the box":
                        st.header(":rotating_light: STATUS OF THE BOX :rotating_light:")

                        current_box = boxes[i]
                        current_box_data = df[
                            (df["boxID"] == current_box)
                            & (df["type"] ==  "weight")  
                            & (df["buildingID"] == current_building)
                        ]


                        for key, value in current_box_data["value"].items():
                            if value == 0:
                                current_box_data["value"][key] = False
                            else:
                                current_box_data["value"][key] = True

                        last_value = current_box_data["value"].iloc[-1]
                        last_data= current_box_data["data"].iloc[-1]  
                        now = datetime.now()

                            # Definisci un intervallo di 1 minuto
                        one_minute_ago = now - timedelta(minutes=1)
                        if last_value == False:
                            if one_minute_ago <= last_data <= now:
                                st.success("The box is free")
                                st.text(f"Recorded on {last_data}")
                            else:
                                st.warning("In the last registered status, the box was free")
                                st.text(f"Recorded on {last_data}")
                        elif last_value == True:
                            if one_minute_ago <= last_data <= now:
                                st.warning("The box is occupied")
                                st.text(f"Recorded on {last_data}")
                            else:
                                st.warning("In the last registered status, the box was occupied")
                                st.text(f"Recorded on {last_data}")

                        st.caption("Please, select how to visualize your data:")
                        time_periods = ["Today", "Week", "Month"]
                        selected_periods = st.multiselect("Select time period(s):", time_periods)

                        for period in selected_periods:
                            if period == "Today":
                                start_date = pd.Timestamp.today() - pd.DateOffset(days=1)
                            elif period == "Week":
                                start_date = pd.Timestamp.today() - pd.DateOffset(weeks=1)
                            elif period == "Month":
                                start_date = pd.Timestamp.today() - pd.DateOffset(months=1)

                            start_date = start_date.replace(microsecond=0)

                            df_period = current_box_data[current_box_data["data"] >= start_date]
                            if df_period.empty:
                                st.warning("The period you have selected has no information to show")
                            else:
                                true_val_period = ( df_period["value"] == True ).sum() 
                                all_value_period = len(df_period["value"])
                                perc_box_occupied_period = round((true_val_period / all_value_period) * 100, 2)

                                st.write(
                                    f"The box has been occupied for {perc_box_occupied_period}% of the time during the {period.lower()}"
                                )

                                fig, ax = plt.subplots()
                                if period == "Today":                                
                                    ax.plot(df_period["ora"], df_period["value"], label=f"Status of the box {current_box}")
                                else:
                                    ax.plot(df_period["data"], df_period["value"], label=f"Status of the box {current_box}")
                               
                                ax.legend()
                                ax.xaxis.set_major_locator(plt.MaxNLocator(6))
                                plt.grid()
                                plt.xlabel("Time")
                                plt.ylabel("Box Occupied")
                                # Set y-axis ticks and labels
                                ax.set_yticks([0, 1])
                                ax.set_yticklabels(['False', 'True'])
                                plt.xticks(rotation=45)
                                plt.title(f"Status of the box {current_box} for the {period.lower()} period")
                                st.pyplot(fig)

                                            