import sys
import cv2
import numpy as np
import time
import yaml
import base64
with open("configuration.yaml") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
from threading import Thread
from submodules.rgb_camera.rgb_camera import RgbCam
from submodules.thermal_camera.thermal_camera import ThermalCam
from submodules.face_detection.face_detection import FaceDetection, LightFaceDetection, FaceDetectionLightRfb, LandmarkDetection
from submodules.object_tracking.objecttracking import CentroidTracker
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
MODEL_RFB320 = cfg['faceDetection']['modelRfb320']
PROTO_RFB320 = cfg['faceDetection']['protoRfb320']
ONNX_SLIM320 = cfg['faceDetection']['onnxSlim320']
FACE_SIZE = cfg['faceDetection']['faceSize']
LANDMARK_MODEL = cfg['faceDetection']['landmarkDetectionModel']

# Set up time params
TIME_MEASURE_TEMP = cfg['periodTime']['measureTemp']
TIME_SEND_REC = cfg['periodTime']['sendRecMess']

# Set up tracking params
MAX_DISAPEARED_FRAMES = cfg['personTracking']['NoOfDisapearFrames']
BUFFER_TEMP = cfg['personTracking']['bufSizeTempPersonTracking']
BUFFER_NAME_ID = cfg['personTracking']['bufSizeNameAndIdPersonTracking']
THRESHOLD_TEMP_FEVER = cfg['personTracking']['thresholdTempOfFever']

# Set up registeration params
NUM_FRONT_PICS = cfg['registration']['numFontPics']
NUM_LEFT_PICS = cfg['registration']['numLeftPics']
NUM_RIGHT_PICS = cfg['registration']['numRightPics']
STACK_NUMBER = cfg['registration']['stackNumberPics']
LEFT_THRESHOLD = cfg['registration']['leftThreshold']
RIGHT_THRESHOLD = cfg['registration']['rightThreshold']
FRONT_RANGE = cfg['registration']['frontRange']
FRAMES_BETWEEN_CAP = cfg['registration']['frameBetweenCapture']

# Flags of mode
ENABLE_SENDING_TO_CLOUD = cfg['iotHub']['enableSending']

#setup threshold of face mask detection
FACEMASK_DETECTION_THRESHOLD = cfg['thresholdFaceMaskDetection']


class DeviceAppFunctions():

    def __init__(self):
        self.color = np.zeros((480,640,3), np.uint8)
        self.rgb_temp = np.zeros((480,640,3), np.uint8)
        self.MODE = 'NORMAL'

        #init the system
        self.initCamera()
        self.initModel()
        self.initObjectTracking()
        self.initIoTConnection()

        self.measureTemp = Thread(target=self.measureTemperatureAllPeople,daemon=True)
        self.measureTemp.start()

        self.process()


    def initCamera(self):
        self.rgb = RgbCam(RGB_SOURCE, RGB_WIDTH, RGB_HEIGHT)
        self.lep = ThermalCam(THERMAL_SOURCE)


    def initModel(self):
        self.faceDetect = LightFaceDetection(PROTO_RFB320, MODEL_RFB320)
        self.faceDetectTemp = LightFaceDetection(PROTO_RFB320, MODEL_RFB320)
        # self.faceDetect = FaceDetection(MODEL_SSD, PROTO_SSD)
        # self.faceDetectTemp = FaceDetection(MODEL_SSD, PROTO_SSD)
        #self.faceDetect = FaceDetectionLightRfb()
        #self.faceDetectTemp = FaceDetectionLightRfb()
        self.landmarkDetect = LandmarkDetection(FACEMASK_DETECTION_THRESHOLD, LANDMARK_MODEL)


    def initObjectTracking(self):
        self.ct = CentroidTracker(MAX_DISAPEARED_FRAMES, BUFFER_NAME_ID, BUFFER_TEMP, THRESHOLD_TEMP_FEVER)
        # self.trackableObjects = {}
        self.objects, _ = self.ct.update([],[],RGB_SCALE)


    def initIoTConnection(self):
        self.conn = IotConn(self.MODE, CONNECTION_STRING_DEVICE, CONNECTION_STRING_BLOB , self.objects)


    def process(self):
        start = time.time()
        self.frame, self.ori = self.rgb.getFrame()
        rects = self.faceDetect.detectFaces(self.frame)

        if (self.MODE == 'NORMAL'):
            self.objects, self.deletedObject = self.ct.update(rects, self.ori, RGB_SCALE)
            
            if (self.deletedObject):
                Thread(target=self.sendRecordsInfo, args=(self.deletedObject, ),daemon=True).start()
                print("send records")
                
            self.drawInfoOnFrameAndCheckRecognize(rects)
            
        elif (self.MODE == 'REGISTER'):
            if (len(rects) == 1):
                img_points = self.landmarkDetect.detectLandmarkForRegister(self.frame, rects)
                self.store_registered_imgs, status = self.register.update(self.frame,img_points, self.ori, rects, RGB_SCALE)

                if status == "REGISTER_SUCCESS":
                    print('Register Ok')
                    del self.register
                    self.MODE = 'WAITING'

                self.displayFrame = self.frame
                return status
        elif (self.MODE == 'CALIBRATING'):
            # self.objects, self.deletedObject = self.ct.update(rects, self.ori, RGB_SCALE)
            # if (self.objects.items):
            time.sleep(0.1)

        elif (self.MODE == 'WAITING'):
            time.sleep(0.1)


        # print('time frame: {:.5f}'.format(time.time() - start))
        self.displayFrame = self.frame
        return "NORMAL"

    def measureTemperatureAllPeople(self):
        time.sleep(1)
        while (self.MODE == 'NORMAL'):
            try:
                objects_measurement = self.objects
                ct_temp = self.ct
                self.lep.update()
                self.rgb_temp, rgb_ori = self.rgb.getFrame()
                thermal, temp = self.lep.getFrame()
                raw = thermal

                thermal = cv2.resize(thermal,(THERMAL_WIDTH,THERMAL_HEIGHT))
                self.color = cv2.applyColorMap(thermal, cv2.COLORMAP_JET)
                
                rects_measurement = self.faceDetectTemp.detectFaces(self.rgb_temp, 35)
                objects_measurement, _ = ct_temp.update(rects_measurement,rgb_ori,RGB_SCALE)

                for (objectID, obj) in list(self.objects.items()):
                    obj.have_mask = self.landmarkDetect.faceMaskDetected(obj.face_rgb)

                measureTemperature(self.color, temp, self.objects, objects_measurement,  RGB_SCALE)
                
                              
            except Exception as identifier:
                print(identifier)
            time.sleep(TIME_MEASURE_TEMP)


    def sendRecordsInfo(self, DeletedObjects):
        for (objectID, obj) in DeletedObjects.items():
            _, buffer = cv2.imencode('.jpg', cv2.resize(obj.face_rgb,(FACE_SIZE,FACE_SIZE)))
            pic_str = base64.b64encode(buffer)
            pic_str = pic_str.decode()

            if (ENABLE_SENDING_TO_CLOUD):
                self.conn.sendRecord(BUILDING_ID, obj.id, obj.name, obj.record_temperature, pic_str)


    def drawInfoOnFrameAndCheckRecognize( self, rects):
        for (objectID, obj) in self.objects.items():
            text = "ID {}".format(objectID)
            centroid = obj.coor        
            y = centroid[1] - 10 if centroid[1] - 10 > 10 else centroid[1] + 10
            center = self.centroidDetect(centroid[0], centroid[1], centroid[2]-centroid[0], centroid[3]-centroid[1])
            cv2.putText(self.frame, text + obj.name, (center[0] - 10, center[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.circle(self.frame, (center[0], center[1]), 4, (0, 255, 0), -1) 
            cv2.putText(self.frame, str(obj.temperature), (centroid[0], y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            if not obj.sending_recs_img:
                print('start sending msg')
                Thread(target=self.sendImageForRec, args=(objectID,),daemon=True).start()
                obj.sending_recs_img = True
    
    def sendImageForRec(self, personID):
        while personID in self.objects and self.MODE == 'NORMAL':
            try:
                _, buffer = cv2.imencode('.jpg', cv2.resize(self.objects[personID].face_rgb, (FACE_SIZE,FACE_SIZE)))
                pic_str = base64.b64encode(buffer)
                pic_str = pic_str.decode()

                if (ENABLE_SENDING_TO_CLOUD):
                    self.conn.messageSending(BUILDING_ID ,DEVICE_ID, personID, pic_str)
                    
                time.sleep(TIME_SEND_REC)
            except Exception as identifier:
                pass

    def centroidDetect(self, x, y, w, h):
        x1 = int(w/2)
        y1 = int(h/2)
        cx = x + x1
        cy = y + y1
        return (cx,cy)

    def getMode(self):
        return self.MODE

    def getRgbFrame(self):
        return self.displayFrame

    def getThermalFrame(self):
        return self.color

    def getRecordsInfo(self):
        return self.deletedObject

    def selectRegisterMode(self):
        self.store_registered_imgs = None
        self.MODE = 'REGISTER'
        self.register = CaptureRegisterFace(NUM_FRONT_PICS,NUM_LEFT_PICS,NUM_RIGHT_PICS, LEFT_THRESHOLD, RIGHT_THRESHOLD, FRONT_RANGE, STACK_NUMBER, FRAMES_BETWEEN_CAP)

    def selectNormalMode(self):
        self.initObjectTracking()
        self.measureTemp.join()
        self.measureTemp = Thread(target=self.measureTemperatureAllPeople, daemon=True)
        self.measureTemp.start()
        self.MODE = 'NORMAL'
        self.conn.restartListener(self.objects)

    def sendRegisteredInfoToServer(self, name_of_new_user):
        if (self.store_registered_imgs is not None and ENABLE_SENDING_TO_CLOUD):
            Thread(target=self.conn.registerToAzure, args=(BUILDING_ID ,name_of_new_user, self.store_registered_imgs, FACE_SIZE, ), daemon=True).start()
        self.store_registered_imgs = None
        print('Registered')
    
    def stop(self):
        self.MODE = "OFF"
        self.rgb.stop()