import numpy as np
import json
from threading import Thread
import threading
from azure.iot.device import IoTHubDeviceClient, Message, MethodResponse

MSG_TXT = '{{"personID": "{personID}","temperature":"{temperature}","embedding": "{embedding}"}}'
MSG_PEOPLE = []

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

    def message_sending(self, personID, embedding, temperature):
        person_record = MSG_TXT.format(personID=personID, temperature=temperature, embedding=embedding)
        message = Message(person_record)
        # Send the message.
        self.client.send_message(message)
        print( "Message sent" ) 
    
