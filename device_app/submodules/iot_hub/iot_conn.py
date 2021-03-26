import numpy as np
import json
import uuid
import cv2
import yaml
with open("configuration.yaml") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
from threading import Thread
import threading
import time
from azure.iot.device import IoTHubDeviceClient, Message, MethodResponse
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient


MSG_REC = cfg['iotHub']['msgFormat']['recMsg']
MSG_REGISTER = cfg['iotHub']['msgFormat']['registerMsg']
MSG_RECORD = cfg['iotHub']['msgFormat']['recordMsg']

class IotConn:
    def __init__(self, mode, connStringDevice, connStringBlob, objects):
        # Create an IoT Hub client
        self.client = IoTHubDeviceClient.create_from_connection_string(connStringDevice)
        self.blob_service_client = BlobServiceClient.from_connection_string(connStringBlob)
        self.mode = mode
        self.thread = Thread(target=self.messageListener, args=(self.client, objects,))
        self.thread.daemon = True
        self.thread.start()

    def restartListener(self, objects):
        self.thread = Thread(target=self.messageListener, args=(self.client, objects,))
        self.thread.daemon = True
        self.thread.start()

    def messageListener(self, client, objects):
        print("Start listening to server")
        while (self.mode == 'NORMAL'): 
            message = client.receive_message()
            message = message.data.decode('utf-8')
            json_data = json.loads(message, strict = False)
            if int(json_data['trackingId']) in objects:
                objects[int(json_data['trackingId'])].updateNameAndId(str(json_data['personName']), str(json_data['personId']))

    def messageSending(self, buildingId, deviceId, trackingId, face_img):
        message = MSG_REC.format(buildingId=buildingId, deviceId=deviceId, trackingId=trackingId, face=face_img)
        message_object = Message(message)
        message_object.custom_properties["level"] = "recognize"
        # Send the message.
        self.client.send_message(message_object)
        print( "Message sent" ) 

    def sendRecord(self, buildingId, personID, name, temperature, face):
        message = MSG_RECORD.format(buildingId=buildingId, personID=personID, personName=name, temperature=temperature, face=face)
        message_object = Message(message)
        message_object.custom_properties["level"] = "store"
        # Send the message.
        self.client.send_message(message_object)        

    def registerToAzure(self, buildingId, personName, imgs, size):
        containerName = str(uuid.uuid4())
        self.sendImageToBlob(imgs, containerName, size)
        self.registerPersonToServer(buildingId ,containerName, personName)

    def createContainer(self, containerName):
        print (containerName)
        self.container_client = self.blob_service_client.create_container(containerName)
    
    def uploadBlob(self, containerName, fileName, image):
        self.block_blob_client = self.blob_service_client.get_blob_client(containerName,fileName)
		# Upload blob
        _, encoded_img = cv2.imencode('.jpg',image)
        self.block_blob_client.upload_blob(encoded_img.tobytes())

    def registerPersonToServer(self, buildingId, containerName, personName):
        message = MSG_REGISTER.format(
            buildingId = buildingId,
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

    
