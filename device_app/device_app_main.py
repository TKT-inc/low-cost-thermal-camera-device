import cv2
import numpy as np
import face_recognition
import time
from collections import OrderedDict
from threading import Thread
from submodules.rgb_camera.rgb_camera import RgbCam
from submodules.thermal_camera.thermal_camera import ThermalCam
from submodules.face_detection.face_detection import FaceDetection, LightFaceDetection, FaceDetectionLightRfb
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


def create_measure_thread(rgb, lep, faceDetect, objects):
    time.sleep(1)
    while (1):
        objects_measurement = objects
        ct_temp = ct
        gp_temp = rgb.getFrame()
        thermal, temp = lep.getFrame()        
        raw = thermal
        thermal = cv2.resize(thermal,(640,480))
        color = cv2.applyColorMap(thermal, cv2.COLORMAP_JET)
        rgp_temp = rgb.getFrame()
        rects_measurement = faceDetect.detectFaces(rgp_temp)
        objects_measurement = ct_temp.update(rects_measurement)
        
        measureTemperature(color, temp, objects, objects_measurement)
        cv2.imshow('temp_rgp', color)
        cv2.imshow('temp_thermal',rgp_temp )
        time.sleep(1)


def create_send_thread(conn,objects, personID):
        while personID in objects:
            #print('send: ' + str(personID) + " " + str(objects[personID].coor))
            coor = objects[personID].coor
            embedding = faceRec(rgb.getOriginFrame(), (int(coor[1]*2.5), int(coor[2]*2.5), int(coor[3]*2.5), int(coor[0]*2.5)))
            conn.message_sending(personID, embedding, objects[personID])
            time.sleep(2)
        #print('KILLED')

def face_checking(frame, objects,trackableObjects, rects, conn):
    for (objectID, obj) in objects.items():
        text = "ID {}".format(objectID)
        centroid = obj.coor
        
        y = centroid[1] - 10 if centroid[1] - 10 > 10 else centroid[1] + 10
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
            # measureTemperature()
        elif (not to.counted):
            to.counted = True
        cv2.putText(frame, str(obj.temperature), (centroid[0], y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        trackableObjects[objectID] = to




CONNECTION_STRING = "HostName=thesis.azure-devices.net;DeviceId=device-test;SharedAccessKey=OYzTSkft0kli1VzJuoF9NIfw63tFqGKn3fFNuWroJbg="

RGB_SOURCE = "nvarguscamerasrc ! video/x-raw(memory:NVMM), " \
	"width=(int)1920, height=(int)1080,format=(string)NV12, " \
	"framerate=(fraction)29/1 ! nvvidconv flip-method=2 ! video/x-raw, " \
	"format=(string)BGRx ! videoconvert ! video/x-raw, " \
	"format=(string)BGR ! appsink" 
CAFFEMODEL = "./submodules/face_detection/models/res10_300x300_ssd_iter_140000.caffemodel"
PROTOTEXTPATH = "./submodules/face_detection/models/deploy.prototxt.txt"
MODEL = "./submodules/face_detection/models/slim-320.caffemodel"
PROTO = "./submodules/face_detection/models/slim-320.prototxt"
ONNX = "./submodules/face_detection/models/version-slim-320_simplified.onnx"

rgb = RgbCam(RGB_SOURCE,768, 432)
lep = ThermalCam(640, 480)
faceDetect = LightFaceDetection(PROTO, MODEL)
faceDetectTemp = LightFaceDetection(PROTO, MODEL)
# faceDetect = FaceDetection(CAFFEMODEL, PROTOTEXTPATH)
#faceDetect = FaceDetectionLightRfb()
ct = CentroidTracker()
ct_temp = CentroidTracker()
trackableObjects = {}
objects = ct.update([])
conn = IotConn(CONNECTION_STRING, objects)

measure_thread = Thread(target=create_measure_thread, args=(rgb, lep, faceDetectTemp, objects,),daemon=True).start()

while (1):
    start = time.time()
    frame = rgb.getFrame()
    rects = faceDetect.detectFaces(frame)
    objects = ct.update(rects)
    face_checking(frame, objects, trackableObjects, rects, conn)
    cv2.imshow('frame', frame)
    # cv2.imshow('heat', color)
    end = time.time()
    print('Inference: {:.6f}s'.format(end-start))
    key = cv2.waitKey(1) & 0xFF
    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        rgb.capture.release()
        cv2.destroyAllWindows()
        break