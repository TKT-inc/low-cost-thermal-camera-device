import numpy as np
import json
import uuid
import cv2
from threading import Thread
import threading
from azure.iot.device import IoTHubDeviceClient, Message, MethodResponse
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient


MSG_TXT = '{{"personID": "{personID}","temperature":"{temperature}","face": "{face}"}}'
MSG_REGISTER = '{{"personName": "{personName}","containerName":"{containerName}"}}'

class IotConn:
    def __init__(self, connStringDevice, connStringBlob, objects):
        # Create an IoT Hub client
        self.client = IoTHubDeviceClient.create_from_connection_string(connStringDevice)
        self.blob_service_client = BlobServiceClient.from_connection_string(connStringBlob)
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

    def registerToAzure(self, personName, imgs, size):
        containerName = str(uuid.uuid4())
        self.sendImageToBlob(imgs, containerName, size)
        self.registerPersonToServer(containerName, personName)

    def createContainer(self, containerName):
        print (containerName)
        self.container_client = self.blob_service_client.create_container(containerName)
    
    def uploadBlob(self, containerName, fileName, image):
        self.block_blob_client = self.blob_service_client.get_blob_client(containerName,fileName)
		# Upload blob
        _, encoded_img = cv2.imencode('.jpg',image)
        self.block_blob_client.upload_blob(encoded_img.tobytes())

    def registerPersonToServer(self, containerName, personName):
        message = MSG_REGISTER.format(
            containerName = containerName,
            personName = personName
        )
        # Set message property to level="register"
        message_object= Message(message)
        message_object.custom_properties["level"] = "register"
        self.client.send_message(message_object)
        print("Resgister sent to the server")

    def sendImageToBlob(self, images, containerName, size):
        # Create container
        self.createContainer(containerName)
        # Upload image to azure blob storage
        parallels_run = len(images)
        threads = [None] * parallels_run
        for i in range(parallels_run):
            fileName = str(i) + ".jpg"
            send_image = cv2.resize(images[i], (size,size))
            t = threading.Thread(target=self.uploadBlob(containerName, fileName, send_image), daemon=True)
            threads[i] = t
            threads[i].start()
        for i in range(parallels_run):
            threads[i].join()

    
