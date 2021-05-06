import numpy as np
import json
import uuid
import cv2
import yaml
import asyncio
with open("configuration.yaml") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
from submodules.common.log import Log
from threading import Thread
import threading
import time
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message
from azure.storage.blob import BlobServiceClient


MSG_REC = cfg['iotHub']['msgFormat']['recMsg']
MSG_REGISTER = cfg['iotHub']['msgFormat']['registerMsg']
MSG_RECORD = cfg['iotHub']['msgFormat']['recordMsg']
MSG_ACTIVE = cfg['iotHub']['msgFormat']['activeDeviceMsg']


def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            Log('CONNECTION', 'Create new event loop')
            asyncio.set_event_loop(asyncio. SelectorEventLoop())
            return asyncio.get_event_loop()

def listeningEventLoopThread(fn, *args):
    loop = get_or_create_eventloop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(fn(*args))
    return loop

def sendingEventLoopThread(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

class IotConn:
    def __init__(self, internetSignal, mode, connStringDevice, connStringBlob, objects):
        # Create an IoT Hub client
        self.mode = mode
        self.buildingIdActiveDevice = None
        self.registerStatus = None
        self.connectionAvailable = self.ConnectionStatus(internetSignal)   

        self.connStringDev = connStringDevice
        self.connStringBlob = connStringBlob
        self.currentObj = objects
        if (not self.initConnection()):
            Thread(target=self.retryConnection, daemon=True).start() 
            
        self.sending_event_loop = get_or_create_eventloop()

        self.thread_sending = Thread(target=sendingEventLoopThread, args=(self.sending_event_loop, ), daemon=True)
        self.thread_sending.start()

    class ConnectionStatus:
        def __init__(self, connectionSignal):
            self.connectionSignal = connectionSignal
            self.connectionAvailable = True

        def emit(self, availableConn):
            self.connectionAvailable = availableConn
            self.connectionSignal.emit(availableConn)

        def isConnAvailable(self):
            return self.connectionAvailable

    def initConnection(self):
        try:
            self.client = IoTHubDeviceClient.create_from_connection_string(self.connStringDev)
            loop = get_or_create_eventloop()
            loop.run_until_complete(self.client.connect())
            # loop.run_in_executor(self.messageListener(self.client, objects))
            
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connStringBlob)
            
            self.thread_listening = Thread(target=listeningEventLoopThread, args=(self.messageListener, self.client,), daemon=True)
            self.thread_listening.start()
            
            self.connectionAvailable.emit(True)
            Log('CONNECTION', 'CONNECT DEVICE TO IOT-HUB SUCCESSFUL')
            return True
        except Exception as e:
            print(e)
            self.connectionAvailable.emit(False)
            return False

    def retryConnection(self):
        while (not self.initConnection()):
            time.sleep(5)

    def restartListener(self, objects):
        self.currentObj = objects
        if self.thread_listening.is_alive():
            Log('CONNECTION', 'Listening thread still alive')
        elif (not self.connectionAvailable.isConnAvailable()):
            Log('CONNECTION', 'Can restart listener because the connection is not established')
        else:
            self.thread_listening = Thread(target=listeningEventLoopThread, args=(self.messageListener, self.client,))
            self.thread_listening.daemon = True
            self.thread_listening.start()

    async def messageListener(self, client):
        Log('CONNECTION', 'Start Listener')
        while (self.mode == 'NORMAL' or self.mode == 'OFF'): 
            try:
                message = await client.receive_message()
                message = message.data.decode('utf-8')
                Log('RECEIVE_DATA', message)
                json_data = json.loads(message, strict = False)
                if 'trackingId' in json_data and int(json_data['trackingId']) in self.currentObj:
                    self.currentObj[int(json_data['trackingId'])].updateInfo(str(json_data['personName']), str(json_data['personId']), str(json_data['mask']))
                elif 'authorizeStatus' in json_data:
                    if json_data['authorizeStatus'] == 'SUCCESS':
                        self.buildingIdActiveDevice = json_data['buildingId']
                    else:
                        self.buildingIdActiveDevice = -1
                elif json_data['method'] == 'userRegister' and self.registerStatus == 'WAITING':
                    self.registerStatus = json_data['data']['status']

                self.connectionAvailable.emit(True)
            except Exception as identifier:
                print(identifier)
                pass

    def handleSendingStatus(self, result):
        try:
            result.result()
            self.connectionAvailable.emit(True)
        except Exception as e:
            Log('CONNECTION', e)
            self.connectionAvailable.emit(False)

    async def handleSendMessage(self, msg):
        if (self.connectionAvailable.isConnAvailable()):
            Log('SEND_DATA', msg)
            done, pending = await asyncio.wait({self.client.send_message(msg)},  timeout=7.0)
            if len(pending) > 0:
                self.connectionAvailable.emit(False)
                for task in pending:
                    task.add_done_callback(self.handleSendingStatus)
            else:
                self.connectionAvailable.emit(True)


    def activeDevice(self, deviceId, deviceLabel, pinCode):
        message = MSG_ACTIVE.format(deviceId=deviceId, deviceLabel=deviceLabel, pinCode=pinCode)
        message_object = Message(message)
        message_object.custom_properties["level"] = "common"
        asyncio.run_coroutine_threadsafe(self.handleSendMessage(message_object),self.sending_event_loop)
        startTime = time.time()
        while (self.buildingIdActiveDevice is None) and (time.time() - startTime < 8):
            time.sleep(0.2)
        returnValue = self.buildingIdActiveDevice
        self.buildingIdActiveDevice = None
        return returnValue

    def messageSending(self, buildingId, deviceId, trackingId, face_img):
        message = MSG_REC.format(buildingId=buildingId, deviceId=deviceId, trackingId=trackingId, face=face_img)
        message_object = Message(message)
        message_object.custom_properties["level"] = "recognize"
        # Send the message.
        asyncio.run_coroutine_threadsafe(self.handleSendMessage(message_object),self.sending_event_loop)

    def sendRecord(self, deviceLabel, personID, temperature, face, masked, recordTime, internetAvailable):
        message = MSG_RECORD.format(deviceLabel=deviceLabel, personID=personID, temperature=temperature, face=face, masked=masked, recordTime=recordTime, internetAvailable=internetAvailable)
        message_object = Message(message)
        message_object.custom_properties["level"] = "common"
        # Send the message.
        asyncio.run_coroutine_threadsafe(self.handleSendMessage(message_object),self.sending_event_loop)       

    def registerToAzure(self, deviceId, buildingId, registerCode, imgs, size):
        containerName = str(uuid.uuid4())
        self.sendImageToBlob(imgs, containerName, size)
        self.registerPersonToServer(deviceId, buildingId ,containerName, registerCode)
        self.registerStatus = 'WAITING'
        startTime = time.time()
        while (self.registerStatus == 'WAITING' and (time.time() - startTime < 10)):
            time.sleep(0.2)
        status = self.registerStatus
        self.registerStatus = None
        if (status == 'WAITING'):
            return 'FAILED'
        return status

    def createContainer(self, containerName):
        print (containerName)
        self.container_client = self.blob_service_client.create_container(containerName)
    
    def uploadBlob(self, containerName, fileName, image):
        self.block_blob_client = self.blob_service_client.get_blob_client(containerName,fileName)
		# Upload blob
        _, encoded_img = cv2.imencode('.jpg',image)
        self.block_blob_client.upload_blob(encoded_img.tobytes())

    def registerPersonToServer(self, deviceId, buildingId, containerName, registerCode):
        message = MSG_REGISTER.format(
            deviceId = deviceId,
            buildingId = buildingId,
            containerName = containerName,
            registerCode = registerCode
        )
        # Set message property to level="register"
        message_object= Message(message)
        message_object.custom_properties["level"] = "register"
        asyncio.run_coroutine_threadsafe(self.handleSendMessage(message_object),self.sending_event_loop)
        Log('CONNECTION' , "Resgister sent to the server")

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

    
