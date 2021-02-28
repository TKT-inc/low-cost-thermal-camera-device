import numpy as np
import imutils
import time
import cv2
import face_recognition
import pickle
import dlib
import time
import json
from threading import Thread
from pylepton import Lepton
import threading
from objecttracking import CentroidTracker
from Tracker import TrackableObject
from azure.iot.device import IoTHubDeviceClient, Message, MethodResponse

# Configuration for iot hub
CONNECTION_STRING = "HostName=thesis.azure-devices.net;DeviceId=device-test;SharedAccessKey=OYzTSkft0kli1VzJuoF9NIfw63tFqGKn3fFNuWroJbg="

# Homography matrix
H = [[ 9.65618052e-01,  1.64519945e-02, -2.23755740e+01],
 [-1.42094632e-02,  1.26760427e+00, -2.37487801e+01],
 [ 7.58731430e-05, -3.62088057e-05,  1.00000000e+00]]


# Source for RGB camera
RGB_SOURCE = "nvarguscamerasrc ! video/x-raw(memory:NVMM), " \
	"width=(int)960, height=(int)540,format=(string)NV12, " \
	"framerate=(fraction)30/1 ! nvvidconv flip-method=2 ! video/x-raw, " \
	"format=(string)BGRx ! videoconvert ! video/x-raw, " \
	"format=(string)BGR ! appsink" 

# Thread sleep
INTERVAL = 1
#Define W,H
MAX_WIDTH = 640
MAX_HEIGHT = 480
# class Stream:
#     def __init__(self, src, width, height, heat):
#         self.width = width
#         self.height = height
#         self.heat = heat
#         self.temp = np.zeros((60,80,1), np.uint16)
#         self.frame = np.zeros((480,640,3), np.uint8)
#         if self.heat is False:
#             self.capture = cv2.VideoCapture(src)
#         self.thread = Thread(target=self.update, args=(heat,))
#         self.thread.daemon = True
#         self.thread.start()
    
#     def update(self, heat):
#         while True:
#             if heat is False:
#                 _, self.ori = self.capture.read()
#                 if self.ori is not None:
#                     self.frame = cv2.resize(self.ori, (self.width, self.height))
#             else:
#                 with Lepton("/dev/spidev0.0") as l:
#                     a,_ = l.capture()
#                     self.temp = np.float32(a)
#                     cv2.normalize(a, a, 0, 65535, cv2.NORM_MINMAX)
#                     np.right_shift(a, 8, a)
#                     self.frame = np.uint8(a)
#     def getFrame(self):
#         return self.frame, self.temp

# # Define the JSON message to send to IoT Hub.
# MSG_TXT = '{{"personID": "{personID}","temperature":"{temperature}","embedding": "{embedding}"}}'
# MSG_PEOPLE = []



# def iothub_client_init():
#     # Create an IoT Hub client
#     client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
#     return client

# def message_listener(client):
#     global receive_dict
#     print("Begin listen")
#     while True:
#         print('Run')         
#         message = client.receive_message()
#         message = message.data.decode('utf-8')
#         json_data = json.loads(message, strict = False)
#         receive_dict[json_data['personID']] = json_data['personName'] 
#         print(receive_dict[json_data['personID']])

# def message_sending(client, personID, embedding, temperature):
#     person_record = MSG_TXT.format(personID=personID, temperature=temperature, embedding=embedding)
#     message = Message(person_record)
#     # Send the message.
#     client.send_message(message)
#     print( "Message sent" )  

# def faceRec(frame, faceTuple):
#     rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     boxes = [faceTuple]
#     encodings = face_recognition.face_encodings(rgb, boxes)
#     embedding = ' '.join(map(str,encodings[0]))
#     return embedding
    
# def storePersonRecord(personID, temperature, embedding):
#     global MSG_PEOPLE
#     person_record = MSG_TXT.format(personID=personID, temperature=temperature, embedding=embedding)
#     MSG_PEOPLE.append(person_record)

# def detectionToRecognition(faceTuple):
#     top = faceTuple[1]
#     right = faceTuple[2]
#     bottom = faceTuple[3]
#     left = faceTuple[0]
#     return (top, right, bottom, left)

# def convertRGBToThermalCoor(x, y, H_raw):
#     global MAX_WIDTH, MAX_HEIGHT
#     H = np.linalg.inv(H_raw)
#     convert_x = int((H[0][0] * x + H[0][1] * y + H[0][2]) / (H[2][0] * x + H[2][1] * y + H[2][2]))
#     convert_y = int((H[1][0] * x + H[1][1] * y + H[1][2]) / (H[2][0] * x + H[2][1] * y + H[2][2]))
#     if(convert_x > MAX_WIDTH):
#         convert_x = MAX_WIDTH - 1
#     if(convert_y > MAX_HEIGHT):
#         convert_y = MAX_HEIGHT - 1
#     return convert_x, convert_y 



# def measureTemperature(coordinates):
#     global frame, H
#     thermal_start_x, thermal_start_y = convertRGBToThermalCoor(coordinates[0], coordinates[1], H)
#     thermal_end_x, thermal_end_y = convertRGBToThermalCoor(coordinates[2], coordinates[3], H)
#     cv2.rectangle(color, (int(thermal_start_x), int(thermal_start_y)), (int(thermal_end_x), int(thermal_end_y)), (0, 0, 255), 2)
    
#     max_temp = np.max(temp[int(thermal_start_y/8):int(thermal_end_y/8), int(thermal_start_x/8):int(thermal_end_x/8)], initial=15394)
#     temperature = "{:.2f}".format(max_temp*36.5/30788) + " oC"
#     return temperature
    
# def centroid_detect(x, y, w, h):
#     x1 = int(w/2)
#     y1 = int(h/2)
#     cx = x + x1
#     cy = y + y1
#     return (cx,cy)
# def face_checking(objects, rects):
#     global frame, trackableObjects, sending_dict, receive_dict
#     for (objectID, centroid) in objects.items():
#         text = "ID {}".format(objectID)
#         temperature = 0.0
#         temperature = measureTemperature(centroid)
#         #print('ID:{objectID}, temp:{temperature}'.format(objectID=objectID, temperature=centroid))
#         y = centroid[1] - 10 if centroid[1] - 10 > 10 else centroid[1] + 10
#         cv2.putText(frame, str(temperature), (centroid[0], y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
#         center = centroid_detect(centroid[0], centroid[1], centroid[2]-centroid[0], centroid[3]-centroid[1])
#         print(receive_dict)
#         if str(objectID) in receive_dict:
#             cv2.putText(frame, text + str(receive_dict[str(objectID)]), (center[0] - 10, center[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
#         else:
#             cv2.putText(frame, text + "???", (center[0] - 10, center[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
#         cv2.circle(frame, (center[0], center[1]), 4, (0, 255, 0), -1) 
#         to = trackableObjects.get(objectID, None)
#         # if there is no existing trackable object, create one
#         if to is None:
#             to = TrackableObject(objectID, centroid)
#             send_thread = threading.Thread(target=createSendThread, args=(objectID, temperature, frame,),daemon=True).start()
#             sending_dict[objectID] = send_thread
#         elif (not to.counted) and (center[0] > 250):
#             to.counted = True
#         trackableObjects[objectID] = to

# def createSendThread(objectID, temperature, frame):
#     global client, objects
#     while objectID in objects:
#         print('send: ' + str(objectID))
#         (top, right, bottom, left) = detectionToRecognition(objects[objectID])
#         embedding = faceRec(frame, (top, right, bottom, left))
#         message_sending(client, objectID, embedding, temperature)
#         time.sleep(3)
#     print('KILLED')
        
        

# def initSystem():
#     print("[INFO] Loading all models...................")
#     caffeModel = "./models/res10_300x300_ssd_iter_140000.caffemodel"
#     prototextPath = "./models/deploy.prototxt.txt"
#     rgb = Stream(RGB_SOURCE,640, 480, heat = False)
#     lep = Stream(RGB_SOURCE,640, 480, heat = True)
#     net = cv2.dnn.readNetFromCaffe(prototextPath,caffeModel)
#     net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
#     net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
#     client = iothub_client_init()
#     initThread(client)
#     ct = CentroidTracker()
#     return client, ct, rgb, lep, net

# def initThread(client):
#     # Create a thread for receiving message from server
#     device_listener = threading.Thread(target=message_listener, args=(client,))
#     device_listener.daemon = True
#     device_listener.start()


sending_dict = {}
receive_dict = {}
trackers = []
trackableObjects = {}
# Setup system
client, ct, rgb, lep, net = initSystem() 

# Flag start for scheduler
flag = 0

while (1):
    frame,_ = rgb.getFrame()
    thermal, temp = lep.getFrame()
    raw = thermal
    thermal = cv2.resize(thermal,(640,480))
    color = cv2.applyColorMap(thermal, cv2.COLORMAP_JET)
    (h, w) = frame.shape[:2]
    # blobImage convert RGB (104.0, 177.0, 123.0)
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0,
                                (300, 300), (104.0, 177.0, 123.0))
    # passing blob through the network to detect and pridiction
    net.setInput(blob) 
    detections = net.forward()
    # loop over the detections
    rects = []
    for i in range(0, detections.shape[2]):
        # extract the confidence and prediction
        confidence = detections[0, 0, i, 2]
        # filter detections by confidence greater than the minimum confidence
        if confidence < 0.8 :
            continue
        # Determine the (x, y)-coordinates of the bounding box for the

        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        (startX, startY, endX, endY) = box.astype("int")
        (cx, cy) = centroid_detect(startX, startY, endX-startX, endY-startY)
        rects.append((startX, startY, endX, endY))
        (top, right, bottom, left) = detectionToRecognition((startX, startY, endX, endY))
        

        #device_measure_temperature.join()
        # cv2.putText(frame, str(temperature), (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 0, 255), 2)
    objects = ct.update(rects)
    face_checking(objects, rects)
    cv2.imshow('frame', frame)
    cv2.imshow('heat', color)
    key = cv2.waitKey(1) & 0xFF

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        rgb.capture.release()
        #lep.thread.join()
        cv2.destroyAllWindows()
        break

        
