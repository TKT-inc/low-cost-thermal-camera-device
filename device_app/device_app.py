import cv2
import numpy as np
import face_recognition
import time
from collections import OrderedDict
from threading import Thread
from submodules.rgb_camera.rgb_camera import RgbCam
from submodules.thermal_camera.thermal_camera import ThermalCam
from submodules.face_detection.face_detection import FaceDetection
from submodules.object_tracking.objecttracking import CentroidTracker
from submodules.object_tracking.Tracker import TrackableObject
from submodules.measure_temperature.measure_temperature import measureTemperature
from submodules.iot_hub.iot_conn import IotConn
def centroid_detect(x, y, w, h):
    x1 = int(w/2)
    y1 = int(h/2)
    cx = x + x1
    cy = y + y1
    return (cx,cy)


def faceRec(frame, faceTuple):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    boxes = [faceTuple]
    encodings = face_recognition.face_encodings(rgb, boxes)
    embedding = ' '.join(map(str,encodings[0]))
    return embedding

def create_send_thread(conn,objects, personID):
        while personID in objects:
            print('send: ' + str(personID))
            coor = objects[personID].coor
            embedding = faceRec(frame, (coor[1], coor[2], coor[3], coor[0]))
            conn.message_sending(personID, embedding, objects[personID])
            time.sleep(3)
        print('KILLED')

def face_checking(frame,color,temp, objects,trackableObjects, rects, conn):
    for (objectID, obj) in objects.items():
        text = "ID {}".format(objectID)
        centroid = obj.coor
        temperature =  measureTemperature(frame,color,temp, objects, objectID, centroid)
        y = centroid[1] - 10 if centroid[1] - 10 > 10 else centroid[1] + 10
        cv2.putText(frame, str(temperature), (centroid[0], y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        center = centroid_detect(centroid[0], centroid[1], centroid[2]-centroid[0], centroid[3]-centroid[1])
        if objectID in objects:
            cv2.putText(frame, text + obj.name, (center[0] - 10, center[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        else:
            cv2.putText(frame, text, (center[0] - 10, center[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.circle(frame, (center[0], center[1]), 4, (0, 255, 0), -1) 
        to = trackableObjects.get(objectID, None)
        # if there is no existing trackable object, create one
        if to is None:
            to = TrackableObject(objectID, centroid)
            send_thread = Thread(target=create_send_thread, args=(conn, objects, objectID,),daemon=True).start()
        elif (not to.counted):
            to.counted = True
        trackableObjects[objectID] = to




CONNECTION_STRING = "HostName=thesis.azure-devices.net;DeviceId=device-test;SharedAccessKey=OYzTSkft0kli1VzJuoF9NIfw63tFqGKn3fFNuWroJbg="

RGB_SOURCE = "nvarguscamerasrc ! video/x-raw(memory:NVMM), " \
	"width=(int)960, height=(int)540,format=(string)NV12, " \
	"framerate=(fraction)30/1 ! nvvidconv flip-method=2 ! video/x-raw, " \
	"format=(string)BGRx ! videoconvert ! video/x-raw, " \
	"format=(string)BGR ! appsink" 
CAFFEMODEL = "./submodules/face_detection/models/res10_300x300_ssd_iter_140000.caffemodel"
PROTOTEXTPATH = "./submodules/face_detection/models/deploy.prototxt.txt"

rgb = RgbCam(RGB_SOURCE,640, 480)
lep = ThermalCam(640, 480)
faceDetect = FaceDetection(model = CAFFEMODEL, proto = PROTOTEXTPATH)
ct = CentroidTracker()
trackableObjects = {}
objects = ct.update([])
conn = IotConn(CONNECTION_STRING, objects)
while (1):
    frame = rgb.getFrame()
    thermal, temp = lep.getFrame()
    raw = thermal
    thermal = cv2.resize(thermal,(640,480))
    color = cv2.applyColorMap(thermal, cv2.COLORMAP_JET)
    rects = faceDetect.detectFaces(frame)
    objects = ct.update(rects)
    face_checking(frame,color,temp, objects, trackableObjects, rects, conn)
    cv2.imshow('frame', frame)
    cv2.imshow('heat', color)
    key = cv2.waitKey(1) & 0xFF
    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        rgb.capture.release()
        #lep.thread.join()
        cv2.destroyAllWindows()
        break