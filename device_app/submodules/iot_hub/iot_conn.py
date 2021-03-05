import numpy as np
import json
from threading import Thread
import threading
from azure.iot.device import IoTHubDeviceClient, Message, MethodResponse

MSG_TXT = '{{"personID": "{personID}","temperature":"{temperature}","face": "{face}"}}'

class IotConn:
    def __init__(self, connString, objects):
        # Create an IoT Hub client
        self.client = IoTHubDeviceClient.create_from_connection_string(connString)
        self.thread = Thread(target=self.message_listener, args=(self.client, objects,))
        self.thread.daemon = True
        self.thread.start()

    def message_listener(self, client, objects):
        print("Start listening to server")
        while True:       
            message = client.receive_message()
            message = message.data.decode('utf-8')
            json_data = json.loads(message, strict = False)
            print(str(json_data))
            if int(json_data['personID']) in objects:
                objects[int(json_data['personID'])].name = str(json_data['personName'])

    def message_sending(self, personID, face_img, temperature):
        message = MSG_TXT.format(personID=personID, temperature=temperature, face=face_img)
        message_object = Message(message)
        message_object.custom_properties["level"] = "recognize"
        # Send the message.
        self.client.send_message(message_object)
        print( "Message sent" ) 
    
