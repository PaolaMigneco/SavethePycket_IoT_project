#!/usr/bin/env python
import time
import json
import sys
import requests
import telebot
sys.path.append('/shared')
from MyMQTT import *



class TelegramBot:
    def __init__(self, token, broker, port, clientID, service_catalog_settings):
        self.token = token
        self.bot = telebot.TeleBot(self.token)
        self.broker = broker
        self.port = port
        self.clientID = clientID
        self.mqttClient = MyMQTT(self.clientID, self.broker, self.port, self)
        self.service_settings = service_catalog_settings
        #in order to handle more users, we need to store the filters for each user at the same time
        self.filters = {} # dictionary of filters for the user
        self.names = {} # dictionary of names for the user
        self.users_ID = {}
        self.boxID = {} 
        print("boxIDs are ",self.boxID)
        self.methods()
    
    def start(self):
        self.mqttClient.start()
    
    def stop(self):
        self.mqttClient.stop()
    

    def notify(self, topic, msg):
        buttons=[]

        with open(self.service_settings) as f: # get the settings of the service catalog
            data_service = json.load(f)
            ip_address = data_service["ip_address"]
            ip_port = data_service["ip_port"]  
        info_request = "http://" + ip_address + ":" + str(ip_port) + "/resource_catalog" # request of information to the service catalog about the resource catalog
        rc_info = requests.get(info_request) #get the ip address and port of resource catalog
        rc_info_dict = rc_info.json()
        ip_rc = rc_info_dict["ip_address"]
        port_rc = rc_info_dict["ip_port"]

        resource_request = "http://" + ip_rc + ":" + str(port_rc) + "/users" #manage request to the resource catalog
        users = requests.get(resource_request)
        users_list = users.json() # get the list of users
   
        if topic.startswith('SaveThePycket/sensors/doorbells'): #react to the doorbell
            userID = topic.split('_')[-1]
            print("userID:", userID)
            for user in users_list:
                print("user[userID]:", user["userID"])
                if user["userID"]==int(userID) and user["chatID"]!=0:
                    chatID = user["chatID"]
                    self.users_ID[chatID] = userID
                    print("QUALCUNO HA SUONATO AL CHATID:", chatID)
                    self.bot.send_message(chatID, text = "Someone is ringing at your door! Wait for the postman to write your order number.")

        elif topic.startswith('SaveThePycket/sensors/keyboards'): #react to the keyboard
            jsonMsg=json.loads(msg)
            userID = jsonMsg['info_sensor'][0]['value'].split('&')[-1]
            print("userID:", userID)
            code = jsonMsg['info_sensor'][0]['value'].split('&')[-2]
            print("code:", code)
            for user in users_list:
                if user["userID"]==int(userID) and user["chatID"]!=0:
                    chatID = user["chatID"]
                    buttons.append(telebot.types.InlineKeyboardButton("Yes", callback_data = "open_door"))
                    buttons.append(telebot.types.InlineKeyboardButton("No", callback_data = "decline"))
                    keyboard = telebot.types.InlineKeyboardMarkup()
                    for button in buttons:
                        keyboard.add(button)
                    self.bot.send_message(chatID, text = f"Order number: {code}. Do you want to open the door?", reply_markup=keyboard)

    def methods(self):
        
        def menu(chat_id): 
            # create a drop-down menu according to the number of filters
            buttons = [] 
            ip_rc, port_rc = info_resource_cat(self.service_settings)
            resource_request = "http://" + ip_rc + ":" + str(port_rc) + "/buildings" 
            buildings = requests.get(resource_request)
            buildings_list = buildings.json()
            print("len filters: ", len(self.filters[chat_id]))
            if len(self.filters[chat_id]) == 0: # if there are no filters, the user can choose the road of the building he wants to monitor
                text = 'Welcome to SaveThePycket! Now you can choose the street name of the building you want to monitor:'
                addresses = []
                for building in buildings_list: 
                    if building["address_road"] not in addresses: 
                        addresses.append(building["address_road"]) # get the addresses of the buildings
                for address in addresses:
                    callback_data = f"address_{address}"
                    buttons.append(telebot.types.InlineKeyboardButton(address, callback_data = callback_data)) # create a button for each address  
                    # The callback_data attribute is a string that is passed to the bot when the user taps the button. 
                keyboard = telebot.types.InlineKeyboardMarkup()
                for button in buttons:
                    keyboard.add(button) # add the buttons to the keyboard

            elif len(self.filters[chat_id]) == 1: # if there is only one filter, the user can choose the number of the building he wants to monitor
                buttons = []
                selected_road = self.filters[chat_id][-1] # get the address selected by the user
                numbers_selected = [b['address_number'] for b in buildings_list if b['address_road'] == selected_road]
                for number in numbers_selected:
                    callback_data = f"number_{number}"
                    buttons.append(telebot.types.InlineKeyboardButton(number, callback_data = callback_data)) # create a button for each number   
                buttons.append(telebot.types.InlineKeyboardButton("\u2190 Go Back", callback_data='back'))
                keyboard = telebot.types.InlineKeyboardMarkup()
                for button in buttons:
                    keyboard.add(button) 
                text = "Select now the number of the building"
            
            elif len(self.filters[chat_id]) == 2: # if there are two filters, the user can choose the box he wants to monitor
                buttons = []
                print("FILTERS IN MENU: ", self.filters[chat_id])
                selected_road = self.filters[chat_id][-2] # get the road associated with the user
                selected_number = self.filters[chat_id][-1] # get the number associated with the user
                print("uselected_road: "+ str(selected_road), flush=True)
                print("selected_number: "+ str(selected_number) , flush=True)
                print("buildings_list: "+ str(buildings_list) , flush=True)
                buildingID = [b['buildingID'] for b in buildings_list if b["address_road"] == selected_road and b["address_number"] == int(selected_number)]
                print("BUILDING ID IN MENU: " +  str(buildingID), flush=True )
                text, keyboard = choose_resource(buildingID[0], ip_rc, port_rc, "boxes")

            return text, keyboard
        
        def choose_resource(buildingID, ip_rc, port_rc, resources_type, boxID = None):
            # create the drop-down menu according to the resource type (boxes or sensors)
            buttons=[]
            #ask the resource catalog the list of boxes  
            resource_request = "http://" + ip_rc + ":" + str(port_rc) + "/" +resources_type
            resources = requests.get(resource_request)
            resources = resources.json()
            if resources_type == "boxes":
                 # get the boxes of the building that are occupied 
                all_resources = [b["boxID"] for b in resources if b["buildingID"] == buildingID]
                resources_selected = [b["boxID"] for b in resources if b["buildingID"] == buildingID and b["status"] == "True"]
            elif resources_type == "sensors":
                resources_selected = [b["sensor_name"] for b in resources if b["buildingID"] == buildingID and b["boxID"] == int(boxID) and b["sensor_name"] not in ["LED status", "Relay Box status"]]
                #check if there is "Temperature and Humidity Sensor" in the list of sensors
                if "Temperature and Humidity Sensor" in resources_selected:
                    #split the string in order to get Temperature and Humidity Sensor separately
                    resources_selected.remove("Temperature and Humidity Sensor")
                    resources_selected.append("Temperature Sensor")
                    resources_selected.append("Humidity Sensor")
                buttons.append(telebot.types.InlineKeyboardButton("Open the box", callback_data='open'))

            if len(resources_selected) != 0:
                for resource in resources_selected:
                    callback_data = f"{resources_type}_{resource}"
                    buttons.append(telebot.types.InlineKeyboardButton(resource, callback_data = callback_data)) # create a button for each resource  
                   
                buttons.append(telebot.types.InlineKeyboardButton("\u2190 Go Back", callback_data='back')) 
                keyboard = telebot.types.InlineKeyboardMarkup()
                for button in buttons:
                    keyboard.add(button) # add the buttons to the keyboard
                if resources_type == "boxes":
                    free_boxes = [b["boxID"] for b in resources if b["buildingID"]== buildingID and b["status"] == "False"]
                    # say to the user which are the boxes free 
                    if len(free_boxes) != 0:
                        #count the numeber of free boxes and write the number
                        text = '\U0001F513 In your building there are ' + str(len(free_boxes)) + ' free boxes with number: ' + ', '.join(str(box) for box in free_boxes) + '.\n\U0001F510 The occupied boxes that you can monitor are:'
                    else:
                        text = '\U0001F513 There are not free boxes.\n\U0001F510 The occupied boxes that you can monitor are:'

                elif resources_type == "sensors":
                    # the user can choose to open the box or to monitor the sensors
                    text = 'You can choose to open the box ' +str(boxID)+ ' or to monitor a sensor:'
            else:
                keyboard = None
                if resources_type == "boxes" and len(all_resources) == 0:
                    text = "\u26A0\uFE0F There are still no boxes in this building! Try again later!"
                elif resources_type == "boxes" and len(all_resources) != 0:
                    text = '\U0001F513 In your building there are ' + str(len(all_resources)) + ' free boxes with number: ' + ', '.join(str(box) for box in all_resources) + '.'
                elif resources_type == "sensors":
                    print("There are not sensors")
                    text = "\u26A0\uFE0F There are still no sensors in box "+ str(boxID)+ "! Try again later!"
            return text, keyboard
        
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
        
        def info_mongodb_adap(service_settings):
            with open(service_settings) as f: # get the settings of the service catalog
                    data_service = json.load(f)
                    ip_address = data_service["ip_address"]
                    ip_port = data_service["ip_port"]  
            info_request = "http://" + ip_address + ":" + str(ip_port) + "/mongodb_adaptor" # request of information to the service catalog about the mogodb adaptor
            mongo_info = requests.get(info_request) #get the ip address and port of mongodb adaptor
            mongo_info_dict = mongo_info.json()
            ip_mongo = mongo_info_dict["ip_address"]
            port_mongo = mongo_info_dict["ip_port"]
            return ip_mongo, port_mongo
        
        def choose_associated_box(chat_id):
            # create a drop-down menu according to the associated box that the user has
            buttons = []
            for box in self.boxID[chat_id]:
                callback_data = f"boxes_{box}"
                buttons.append(telebot.types.InlineKeyboardButton(box, callback_data = callback_data)) # create a button for each associated box  
                 
            buttons.append(telebot.types.InlineKeyboardButton("\u2190 Go Back", callback_data='back')) 
            keyboard = telebot.types.InlineKeyboardMarkup()
            for button in buttons:
                keyboard.add(button) # add the buttons to the keyboard
                text = 'You can choose which associated box you want to monitor or open:'
            return text, keyboard

        def main_menu(inline_query):
            text, keyboard = menu(inline_query.chat.id) # get the drop-down menu
            if inline_query.text != "/start":
                text = 'Hi ' + self.names[inline_query.chat.id] + '! Now you can choose the street name of the building you want to monitor:' 
            self.bot.send_message(inline_query.chat.id, text = text, reply_markup = keyboard)
        
        #Note: all handlers are tested in the order in which they were declared
        #After that declaration, we need to register some so-called message handlers. Message handlers define filters which a message must pass. 
        #If a message passes the filter, the decorated function is called and the incoming message is passed as an argument
        
        @self.bot.message_handler(commands=['start']) #True if message.content_type == 'text' and message.text starts with a command that is in the list of strings.
        def first_menu(inline_query): #function_name (start) is not bound to any restrictions.
        #Any function name is permitted with message handlers. The function must accept at most one argument (inline_query), which will be the message that the function must handle. 
            self.filters[inline_query.chat.id] = []
            self.boxID[inline_query.chat.id] = []
            ip_rc, port_rc = info_resource_cat(self.service_settings)
            resource_request = "http://" + ip_rc + ":" + str(port_rc) + "/users" #manage request to the resource catalog
            users = requests.get(resource_request)
            users_list = users.json() # get the list of users
            resource_request = "http://" + ip_rc + ":" + str(port_rc) + "/buildings" 
            buildings = requests.get(resource_request)
            buildings_list = buildings.json()
            
            for user in users_list:
                if inline_query.chat.id == user["chatID"]:
                    buildingID_associated = [u['buildingID'] for u in users_list if u["chatID"] == inline_query.chat.id]
                    road_associated = [b['address_road'] for b in buildings_list if b["buildingID"] == buildingID_associated[0]]
                    number_associated = [b['address_number'] for b in buildings_list if b["buildingID"] == buildingID_associated[0]]
                    self.bot.send_message(inline_query.chat.id, text = f"You are already associated with the address {road_associated[0]} {number_associated[0]}! \U0001F642")
                    self.filters[inline_query.chat.id].append(road_associated[0])
                    self.filters[inline_query.chat.id].append(number_associated[0])
                    print(self.filters[inline_query.chat.id])
                    main_menu(inline_query)
                    return # exits from the function
            #HANDLE THE REGISTRATION OF A USER
            # ask for the user name and register the user in user_list with the current chatID
            text = 'Welcome to SaveThePycket! What is your name?'
            self.bot.send_message(inline_query.chat.id, text = text) # send the message to the user
            # read the message sent by the user 
            self.bot.register_next_step_handler(inline_query, get_name) # get_name is the function that will be called after the user sends the message
        
        @self.bot.message_handler(commands=[]) #True if message.content_type == 'text' and message.text starts with a command that is in the list of strings.
        def get_name(inline_query):
            buttons=[]
            
            name = inline_query.text
            
            self.names[inline_query.chat.id] = name
            ip_rc, port_rc = info_resource_cat(self.service_settings)
            resource_request = "http://" + ip_rc + ":" + str(port_rc) + "/users" #manage request to the resource catalog
            users = requests.get(resource_request)
            users_list = users.json() # get the list of users
            
            # check if the user_name is already registered
            for user in users_list:
                if self.names[inline_query.chat.id] == user["user_name"]:
                    # if the user_name is already registered change the chatID from zero to the inline_query.chat.id
                    main_menu(inline_query)
                    return
            #if the name is not in the user_list, send a inline_query to the user to inform him that the name is not registered
            text = '🏚️ The name you entered is not registered! Do you want to associate your name with a building or try with another name?' 
            #creare bottoni per scelte
            buttons.append(telebot.types.InlineKeyboardButton("Associate", callback_data = "associate"))  
            buttons.append(telebot.types.InlineKeyboardButton("Try again", callback_data = "name_try_again"))
            keyboard = telebot.types.InlineKeyboardMarkup() # create the keyboard
            for button in buttons:
                    keyboard.add(button) 

            self.bot.send_message(inline_query.chat.id, text = text, reply_markup=keyboard) # send the inline_query to the user

        @self.bot.message_handler(commands=[])
        def get_password(message):
            buttons=[]
            password = message.text 
            ip_rc, port_rc = info_resource_cat(self.service_settings)
            resource_request = "http://" + ip_rc + ":" + str(port_rc) + "/buildings" 
            buildings = requests.get(resource_request)
            buildings_list = buildings.json()
            resource_request = "http://" + ip_rc + ":" + str(port_rc) + "/users" #manage request to the resource catalog
            users = requests.get(resource_request)
            users_list = users.json() # get the list of users

            # check if the password is correct
            for building in buildings_list:
                
                if int(self.filters[message.chat.id][-1]) == building["address_number"] and self.filters[message.chat.id][-2] == building["address_road"] and password == building["password"]:
                    # if the password is correct show the menu for choosing the box
                    #regiter the user in the resource catalog
                    count_users=0
                    for user in users_list:
                        count_users+=1
                        if user["user_name"] == self.names[message.chat.id]: # if the user is already registered to the system
                            if user["chatID"] == 0:
                                user["chatID"] = message.chat.id                                
                                resource_request = "http://" + ip_rc + ":" + str(port_rc) + "/user" 
                                requests.put(resource_request, data = json.dumps(user))
                                text = 'Thanks for the registration!'
                                self.bot.send_message(message.chat.id, text)
                            text, keyboard = choose_resource(building["buildingID"], ip_rc, port_rc,"boxes")
                            self.bot.send_message(message.chat.id, text, reply_markup = keyboard)
                            return
                        
                    # if the user is not already registered
                    user = {"userID": count_users+1, "user_name": self.names[message.chat.id],"chatID": message.chat.id, "buildingID": building["buildingID"]}
                    # add the user to the user_list
                    resource_request = "http://" + ip_rc + ":" + str(port_rc) + "/register_user_telegram"
                    requests.post(resource_request, data = json.dumps(user))
                    self.bot.send_message(message.chat.id, text = 'Thanks for the registration!')
                    text, keyboard = choose_resource(building["buildingID"], ip_rc, port_rc,"boxes")
                    self.bot.send_message(message.chat.id, text, reply_markup = keyboard)
                    return
                
            #if the password is not correct send a message to the user to inform him that the password is not correct
            text = '🏚️ Sorry, but the password you entered is not correct! Try again!' 
            self.bot.send_message(message.chat.id, text = text)
            self.bot.register_next_step_handler(message, get_password)

        @self.bot.callback_query_handler(func = lambda call: True) 
        def callback_query(call): 
            ip_rc, port_rc = info_resource_cat(self.service_settings)
            
            resource_request = "http://" + ip_rc + ":" + str(port_rc) + "/buildings" #get the list of buildings
            buildings = requests.get(resource_request)
            buildings_list = buildings.json()
            resource_request = "http://" + ip_rc + ":" + str(port_rc) + "/users" #get the list of users
            users = requests.get(resource_request)
            users_list = users.json() # get the list of users
            resource_request = "http://" + ip_rc + ":" + str(port_rc) + "/box_sensors" #get the list of box_sensors
            box_sensors = requests.get(resource_request)
            if box_sensors == None:
                    box_sensors_list = []
            else:
                box_sensors_list = box_sensors.json() 
            
            #HANDLE THE BUTTONS
            if call.data.startswith('address_'):
                buttons = []
                selected_road = call.data.split('_')[1] # get the address selected by the user
                numbers_selected = [b['address_number'] for b in buildings_list if b['address_road'] == selected_road]
                for number in numbers_selected:
                    callback_data = f"number_{number}"
                    buttons.append(telebot.types.InlineKeyboardButton(number, callback_data = callback_data)) # create a button for each number  
                    
                buttons.append(telebot.types.InlineKeyboardButton("\u2190 Go Back", callback_data='back'))
                keyboard = telebot.types.InlineKeyboardMarkup()
                for button in buttons:
                    keyboard.add(button) # add the buttons to the keyboard
                self.bot.send_message(call.message.chat.id, text = 'Now you can choose the number of the building you want to monitor:', reply_markup = keyboard)
                self.filters[call.message.chat.id].append(selected_road) # add the address to the filters
            
            elif call.data.startswith('number_'):
                buttons=[]
                selected_number = call.data.split('_')[1]
                self.filters[call.message.chat.id].append(selected_number)
                for user in users_list:
                    if call.message.chat.id == user["chatID"]:
                        for building in buildings_list:
                            if int(selected_number) == building["address_number"] and self.filters[call.message.chat.id][-2] == building["address_road"]:
                                # if the user is already registered in the resource catalog
                                text, keyboard = choose_resource(building["buildingID"], ip_rc, port_rc, "boxes")
                                self.bot.send_message(call.message.chat.id, text, reply_markup = keyboard)
                                return
                        
                #ask for password of building and register the user in user_list with the current chatID
                text = 'What is the password of your building?'
                self.bot.send_message(call.message.chat.id, text = text) # send the message to the user
                self.bot.register_next_step_handler(call.message, get_password)
                

            elif call.data.startswith('boxes_'):
                selected_box = call.data.split('_')[1] # get the box selected by the user
                i = 0
                for building in buildings_list:
                    if self.filters[call.message.chat.id][0] == building["address_road"] and int(self.filters[call.message.chat.id][1]) == building["address_number"]:
                        
                        print("buildingID", building["buildingID"])
                        print("selected_box", selected_box)
                        text, keyboard = choose_resource(building["buildingID"], ip_rc, port_rc, "sensors", selected_box)
                        self.bot.send_message(call.message.chat.id, text, reply_markup = keyboard)
                        self.filters[call.message.chat.id].append(selected_box) # add the number to the filters
                        i += 1
                        
                
                if i == 0:
                    text = "\u26A0\uFE0F There are still no sensors in box "+ selected_box + "! Try again later!"
                    self.bot.send_message(call.message.chat.id, text = text)
                    return

            elif call.data.startswith('sensors_'):
                selected_sensor = call.data.split('_')[1] # get the sensor selected by the user
                #get the sensor measurements from mongodb database
                ip_mdb, port_mdb = info_mongodb_adap(self.service_settings)
                for building in buildings_list:
                    if building["address_road"] == self.filters[call.message.chat.id][0] and building["address_number"] == int(self.filters[call.message.chat.id][1]):
                        buildingID = building["buildingID"]
                for sensor in box_sensors_list:
                    if sensor["boxID"] == int(self.filters[call.message.chat.id][2]):
                        boxID = sensor["boxID"]
                mongodb_request= "http://" + ip_mdb + ":" + str(port_mdb) + "/measures?sensor=" + selected_sensor + "&boxID=" + str(boxID) + "&buildingID=" + str(buildingID)                
                measure_json = requests.get(mongodb_request)
                measure_json = measure_json.json() # get the measure
                self.bot.send_message(call.message.chat.id, text = f"The measure of the {selected_sensor} is {measure_json['measure']} {measure_json['unit']} at time {measure_json['timestamp']}") # send the message to the user
                
            elif call.data == 'name_try_again': 
                self.bot.send_message(call.message.chat.id, text = 'Please, enter another name:')
                self.bot.register_next_step_handler(call.message, get_name) 
                
            elif call.data == 'associate': #register new user
                main_menu(call.message) 
                
            elif call.data == 'back':
                self.filters[call.message.chat.id].pop(-1) # remove the last filter
                text, keyboard = menu(call.message.chat.id) # get the menu
                if len(self.filters[call.message.chat.id]) == 0:
                    text = "Try again! You can choose the road of the building you want to monitor:"
                elif len(self.filters[call.message.chat.id]) == 1:
                    text = "Try again!You can choose the number of the building you want to monitor:"
                elif len(self.filters[call.message.chat.id]) == 2:
                    text = "Try again!You can choose the box you want to monitor:"
                self.bot.send_message(call.message.chat.id, text = text, reply_markup = keyboard)

            elif call.data == 'open': #open the box to retrieve the packet
                #control if the user is associated with the box
                box_choosen = self.filters[call.message.chat.id][-1]
                buildingID = [u['buildingID'] for u in users_list if u["chatID"] == call.message.chat.id]
                
                if call.message.chat.id in self.boxID.keys() and int(box_choosen) in self.boxID[call.message.chat.id]:
                    topic_rel_box="SaveThePycket/telegram/boxes/sensor_Relbox_"
                    msg_to_open="False"
                    topic_rel_box_fin = topic_rel_box + str(buildingID[0]) + "_" + str(box_choosen)
                    

                    telegram.mqttClient.myPublish(topic_rel_box_fin, msg_to_open) # publish the message                     
                    text = f"You opened the box {box_choosen}"
                    self.bot.send_message(call.message.chat.id, text = text)
                    # remove the boxID from the list of boxes associated with the user
                    self.boxID[call.message.chat.id].remove(int(box_choosen))
                    #remove the filter regarding the box
                    self.filters[call.message.chat.id].pop(-1) # remove the last filter


                    time.sleep(5)
                    if len(self.filters[call.message.chat.id])<3:
                        #Send the menu to monitor the boxes of the building
                        text, keyboard = menu(call.message.chat.id) # get the menu
                        self.bot.send_message(call.message.chat.id, text = text, reply_markup = keyboard)
                    elif len(self.filters[call.message.chat.id]) ==3:
                        #return the list of sensors associated to that box
                        text, keyboard = choose_resource(int(buildingID[0]), ip_rc, port_rc, "sensors", int(self.filters[call.message.chat.id][2]))
                        self.bot.send_message(call.message.chat.id, text = text, reply_markup=keyboard)
                    else:
                        #return the list of boxes that are still associated with that chat id
                        text, keyboard = choose_associated_box(call.message.chat.id)
                        self.bot.send_message(call.message.chat.id, text = text, reply_markup=keyboard)
                    
                else:
                    self.bot.send_message(call.message.chat.id, text = "You are not associated with this box")
                    
            elif call.data == 'open_door': #open the door and box when the postman arrives
                for user in users_list:
                    if user["chatID"] == call.message.chat.id:
                        buildingID = user["buildingID"]

                topic_rel_door="SaveThePycket/telegram/doors/sensor_Reldoor_"
                topic_rel_box="SaveThePycket/telegram/boxes/sensor_Relbox_"
                msg_to_open = "True"

                #choose the first empty box available
                ip_rc, port_rc = info_resource_cat(self.service_settings)
                request = "http://" + ip_rc + ":" + str(port_rc) + "/boxes"
                boxes = requests.get(request) # get the boxes list
                boxes_json = boxes.json()
                boxID = None
                for box in boxes_json:
                    if box['status'] == "False":
                        boxID = box['boxID']
                        break
                if boxID != None:
                    topic_rel_door_fin=topic_rel_door+str(buildingID) #"SaveThePycket/telegram/doors/sensor_Reldoor_"
                    telegram.mqttClient.myPublish(topic_rel_door_fin, msg_to_open)
                    topic_rel_box_fin = topic_rel_box + str(buildingID) + "_" + str(boxID) #"SaveThePycket/telegram/boxes/sensor_Relbox_"
                    telegram.mqttClient.myPublish(topic_rel_box_fin, msg_to_open) # publish the message to the box
                    text = f"You opened the door. Your assigned box is {boxID}"
                    self.bot.send_message(call.message.chat.id, text = text)
                    #associate the chat id with the box id in a dictionary self.boxID
                    print(f"your associated box is {boxID}, your chatid is {call.message.chat.id}")
                    
                    self.boxID[call.message.chat.id].append(boxID)
                    
                    if len(self.boxID[call.message.chat.id])==1:
                        self.filters[call.message.chat.id].append(boxID)
                        #return directly the sensors of the box
                        text, keyboard = choose_resource(buildingID, ip_rc, port_rc, "sensors", boxID)
                        self.bot.send_message(call.message.chat.id, text = text, reply_markup=keyboard)
                    elif len(self.boxID[call.message.chat.id])>1:
                        #return the list of boxes assigned to that chat id in order to choose the sensor to monitor or open
                        text, keyboard = choose_associated_box(call.message.chat.id)
                        self.bot.send_message(call.message.chat.id, text = text, reply_markup=keyboard)

                else:
                    self.bot.send_message(call.message.chat.id, text = "There are no boxes available")

            elif call.data == 'decline': #decline the door
                    text = f"You declined the door"
                    self.bot.send_message(call.message.chat.id, text = text)
                    time.sleep(3)

                    #Send the menu to monitor the boxes of the building
                    text, keyboard = menu(call.message.chat.id) # get the menu
                    self.bot.send_message(call.message.chat.id, text = text, reply_markup = keyboard)

def info_mqtt(service_settings):
    with open(service_settings) as f: # get the settings of the service catalog
            data_service = json.load(f)
            ip_address = data_service["ip_address"]
            ip_port = data_service["ip_port"]  
    info_request = "http://" + ip_address + ":" + str(ip_port) + "/mqtt_connection" # request of information to the service catalog about the mqtt connection
    mqtt_info = requests.get(info_request) #get the ip address and port of mqtt connection
    moqtt_info_dict = mqtt_info.json()
    broker_mqtt = moqtt_info_dict["broker"]
    broker_port_mqtt = moqtt_info_dict["broker_port"]
    return broker_mqtt, broker_port_mqtt


if __name__ == '__main__':
    print("TELEGRAM")
    service_settings = "/shared/service_catalog_settings.json"
    broker_mqtt, broker_port_mqtt = info_mqtt(service_settings)
    token = "5976794917:AAHql6VjFn_DIw9tLvUIRg0CVUrqXP3NoLQ"
    clientID = "telegram_bot"
    telegram = TelegramBot(token, broker_mqtt, broker_port_mqtt, clientID, "/shared/service_catalog_settings.json")
    
    telegram.start() # starts the mqtt client
    topic_doorbells = "SaveThePycket/sensors/doorbells/#" 
    telegram.mqttClient.mySubscribe(topic_doorbells)
    topic_keyboard= "SaveThePycket/sensors/keyboards/#" 
    telegram.mqttClient.mySubscribe(topic_keyboard)
    telegram.bot.infinity_polling() # keeps the bot running
    telegram.stop() # stops the mqtt client