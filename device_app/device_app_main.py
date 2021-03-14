import cv2
import numpy as np
import time
import yaml
import base64
with open("../configuration.yaml") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
from collections import OrderedDict
from threading import Thread
from submodules.rgb_camera.rgb_camera import RgbCam
from submodules.thermal_camera.thermal_camera import ThermalCam
from submodules.face_detection.face_detection import FaceDetection, LightFaceDetection, FaceDetectionLightRfb, LandmarkDetection
from submodules.object_tracking.objecttracking import CentroidTracker
from submodules.object_tracking.Tracker import TrackableObject
from submodules.measure_temperature.measure_temperature import measureTemperature
from submodules.iot_hub.iot_conn import IotConn
from submodules.capture_register.capture_register import CaptureRegisterFace

# Set up device params
DEVICE_ID = cfg['deviceId']
BUILDING_ID = cfg['buildingId']

# Set up azure cloud params 
CONNECTION_STRING_DEVICE = cfg['iotHub']['connectionStringDevice']
CONNECTION_STRING_BLOB = cfg['iotHub']['connectionStringBlob']

# Set up camera params
RGB_SOURCE = cfg['camera']['rgb']['source']
RGB_WIDTH = cfg['camera']['rgb']['scaleWidth']
RGB_HEIGHT = cfg['camera']['rgb']['scaleHeight']
RGB_SCALE = 1920 / RGB_WIDTH
THERMAL_SOURCE = cfg['camera']['thermal']['source']
THERMAL_WIDTH = cfg['camera']['thermal']['scaleWidth']
THERMAL_HEIGHT = cfg['camera']['thermal']['scaleHeight']

# Set up face detection params
MODEL_SSD = cfg['faceDetection']['modelSsd']
PROTO_SSD = cfg['faceDetection']['protoSsd']
MODEL_SLIM320 = cfg['faceDetection']['modelSlim320']
PROTO_SLIM320 = cfg['faceDetection']['protoSlim320']
ONNX_SLIM320 = cfg['faceDetection']['onnxSlim320']
FACE_SIZE = cfg['faceDetection']['faceSize']

# Set up mapping param between 2 cameras
H_MATRIX = cfg['transMatrix']

# Set up time params
TIME_MEASURE_TEMP = cfg['periodTime']['measureTemp']
TIME_SEND_REC = cfg['periodTime']['sendRecMess']

# Set up tracking params
MAX_DISAPEARED_FRAMES = cfg['maxDisFramesObjectTracking']

# Set up registeration params
NUM_FRONT_PICS = cfg['registration']['numFontPics']
NUM_LEFT_PICS = cfg['registration']['numLeftPics']
NUM_RIGHT_PICS = cfg['registration']['numRightPics']
STACK_NUMBER = cfg['registration']['stackNumberPics']
LEFT_THRESHOLD = cfg['registration']['leftThreshold']
RIGHT_THRESHOLD = cfg['registration']['rightThreshold']
FRONT_RANGE = cfg['registration']['frontRange']
FRAMES_BETWEEN_CAP = cfg['registration']['frameBetweenCapture']

# FLags of display
ENABLE_SHOW_THERMAL_FRAME = cfg['display']['enableThermalFrame']





class DeviceAppMain():

    def __init__(self):
        self.color = np.zeros((480,640,3), np.uint8)
        self.rgb_temp = np.zeros((480,640,3), np.uint8)
        self.MODE = 'NORMAL'

        #init the system
        self.init_camera()
        self.init_model()
        self.init_object_tracking()
        self.init_conn()

        self.frame, self.ori = rgb.getFrame()

        Thread(target=self.measure_thread, args=(self.rgb, self.lep, self.faceDetectTemp, self.objects,),daemon=True).start()

        cv2.namedWindow('Main Monitor')
        cv2.moveWindow("Main Monitor", 600, 20)

        cv2.namedWindow('measure thermal')
        cv2.moveWindow('measure thermal', 120, 500)

        cv2.namedWindow('measure rgb')
        cv2.moveWindow('measure rgb', 1200, 500)


    def init_camera():
        self.rgb = RgbCam(RGB_SOURCE, RGB_WIDTH, RGB_HEIGHT)
        self.lep = ThermalCam(THERMAL_SOURCE)


    def init_model():
        self.faceDetect = LightFaceDetection(PROTO_SLIM320, MODEL_SLIM320)
        self.faceDetectTemp = LightFaceDetection(PROTO_SLIM320, MODEL_SLIM320)
        # faceDetect = FaceDetection(CAFFEMODEL, PROTOTEXTPATH)
        #faceDetect = FaceDetectionLightRfb()
        self.landmarkDetect = LandmarkDetection()


    def init_object_tracking():
        self.ct = CentroidTracker(MAX_DISAPEARED_FRAMES)
        self.ct_temp = CentroidTracker(MAX_DISAPEARED_FRAMES)
        self.trackableObjects = {}
        self.objects, _ = ct.update([],[],RGB_SCALE)


    def init_conn():
        self.conn = IotConn(MODE, CONNECTION_STRING_DEVICE, CONNECTION_STRING_BLOB , objects)


    def process(self):
        while (1):
            # start = time.time()
            self.frame, self.ori = self.rgb.getFrame()
            rects = self.faceDetect.detectFaces(self.frame)
            if (self.MODE == 'NORMAL'):
                self.objects, deletedObject = ct.update(rects,ori, RGB_SCALE)
                
                if (deletedObject):
                    Thread(target=self.send_records, args=(self.conn, self.deletedObject, ),daemon=True).start()
                    print("send records")
                    
                self.face_checking(self.frame, self.objects, self.trackableObjects, rects, self.conn)
                
                if (ENABLE_SHOW_THERMAL_FRAME):
                    cv2.imshow('measure thermal', self.color)
                    cv2.imshow('measure rgb', self.rgb_temp)
                
            elif (self.MODE == 'REGISTER'):
                if (len(rects) == 1):
                    img_points = self.landmarkDetect.detectLandmark(self.frame, rects)
                    store = temp.update(self.frame,img_points, self.ori, rects, RGB_SCALE)

                    if store is not None:
                        Thread(target=self.conn.registerToAzure, args=(BUILDING_ID ,'Tien',store, FACE_SIZE, ), daemon=True).start()
                        del temp
                        self.MODE = "NORMAL"
                        self.ct, self.ct_temp, self.trackableObjects, self.objects = self.init_object_tracking()
                        Thread(target=self.measure_thread, args=(self.rgb, self.lep, self.faceDetectTemp, self.objects,),daemon=True).start()
                        self.conn.restart_listener(objects)

            cv2.imshow('Main Monitor', frame)
            end = time.time()
            # print('Inference: {:.6f}s'.format(end-start))

            key = cv2.waitKey(1) & 0xFF
            # if the `q` key was pressed, break from the loop
            if key == ord("q"):# quit
                rgb.capture.release()
                cv2.destroyAllWindows()
                break
            if key == ord("r"): # registration mode
                MODE = 'REGISTER'
                temp = CaptureRegisterFace(NUM_FRONT_PICS,NUM_LEFT_PICS,NUM_RIGHT_PICS, LEFT_THRESHOLD, RIGHT_THRESHOLD, FRONT_RANGE, STACK_NUMBER, FRAMES_BETWEEN_CAP)


    def centroid_detect(x, y, w, h):
        x1 = int(w/2)
        y1 = int(h/2)
        cx = x + x1
        cy = y + y1
        return (cx,cy)


    def measure_thread(rgb, lep, faceDetect, objects):
        time.sleep(1)
        while (MODE == 'NORMAL'):
            objects_measurement = self.objects
            ct_temp = self.ct
            self.rgb_temp, rgp_ori = self.rgb.getFrame()
            thermal, temp = self.lep.getFrame()        
            raw = thermal
            thermal = cv2.resize(thermal,(THERMAL_WIDTH,THERMAL_HEIGHT))
            self.color = cv2.applyColorMap(thermal, cv2.COLORMAP_JET)
            
            rects_measurement = self.faceDetect.detectFaces(self.rgb_temp)
            objects_measurement, _ = ct_temp.update(rects_measurement,rgp_ori,RGB_SCALE)
            
            measureTemperature(self.color, temp, self.objects, objects_measurement, H_MATRIX)
        
            time.sleep(TIME_MEASURE_TEMP)


    def send_pics_for_rec(conn,objects, personID):
        while personID in self.objects and self.MODE == 'NORMAL':
            try:
                _, buffer = cv2.imencode('.jpg', cv2.resize(self.objects[personID].face_rgb, (FACE_SIZE,FACE_SIZE)))
                pic_str = base64.b64encode(buffer)
                pic_str = pic_str.decode()

                self.conn.message_sending(BUILDING_ID ,DEVICE_ID, personID, pic_str)
                time.sleep(TIME_SEND_REC)
            except Exception as identifier:
                pass


    def send_records(conn, DeletedObjects):
        for (objectID, obj) in DeletedObjects.items():
            _, buffer = cv2.imencode('.jpg', cv2.resize(obj.face_rgb,(FACE_SIZE,FACE_SIZE)))
            pic_str = base64.b64encode(buffer)
            pic_str = pic_str.decode()
            self.conn.send_record(BUILDING_ID, obj.id, obj.name, obj.temperature, pic_str)


    def face_checking(frame, objects,trackableObjects, rects, conn):
        for (objectID, obj) in self.objects.items():
            text = "ID {}".format(objectID)
            centroid = obj.coor        
            y = centroid[1] - 10 if centroid[1] - 10 > 10 else centroid[1] + 10
            center = centroid_detect(centroid[0], centroid[1], centroid[2]-centroid[0], centroid[3]-centroid[1])

            if objectID in objects:
                cv2.putText(self.frame, text + obj.name, (center[0] - 10, center[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            else:
                cv2.putText(self.frame, text, (center[0] - 10, center[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.circle(self.frame, (center[0], center[1]), 4, (0, 255, 0), -1) 
            to = self.trackableObjects.get(objectID, None)

            # if there is no existing trackable object, create one
            if to is None:
                to = TrackableObject(objectID, centroid)
                _ = Thread(target=self.send_pics_for_rec, args=(self.conn, self.objects, self.objectID,),daemon=True).start()
            elif (not to.counted):
                to.counted = True

            cv2.putText(self.frame, str(obj.temperature), (centroid[0], y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            self.trackableObjects[objectID] = to