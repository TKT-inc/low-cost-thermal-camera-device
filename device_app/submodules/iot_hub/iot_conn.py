import numpy as np
import json
from threading import Thread
import threading
from azure.iot.device import IoTHubDeviceClient, Message, MethodResponse

MSG_TXT = '{{"personID": "{personID}","temperature":"{temperature}","embedding": "{embedding}"}}'
MSG_PEOPLE = []

class IotConn
    def __init__(self, connString):
        # Create an IoT Hub client
        self.client = IoTHubDeviceClient.create_from_connection_string(connString)
        self.thread = Thread(target=self.message_listener, args=(heat,))
        self.thread.daemon = True
        self.thread.start()

    def message_listener():
        global receive_dict
        while True:       
            message = self.client.receive_message()
            message = message.data.decode('utf-8')
            json_data = json.loads(message, strict = False)
            receive_dict[json_data['personID']] = json_data['personName'] 
            return receive_dict[json_data['personID']]

    def message_sending(client, personID, embedding, temperature):
        person_record = MSG_TXT.format(personID=personID, temperature=temperature, embedding=embedding)
        message = Message(person_record)
        # Send the message.
        client.send_message(message)
        print( "Message sent" )  
