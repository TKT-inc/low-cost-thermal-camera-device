import sys
import cv2
import numpy as np
import time
import yaml
import base64
with open("configuration.yaml") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
with open("user_settings.yaml") as settings:
    user_cfg = yaml.safe_load(settings)
from threading import Thread
from collections import OrderedDict
from submodules.rgb_camera.rgb_camera import RgbCam
from submodules.thermal_camera.thermal_camera import ThermalCam
from submodules.face_detection.face_detection import FaceDetection, LightFaceDetection, FaceDetectionLightRfb, LandmarkDetection
from submodules.object_tracking.objecttracking import CentroidTracker
from submodules.measure_temperature.measure_temperature import measureTemperature
from submodules.iot_hub.iot_conn import IotConn
from submodules.capture_register.capture_register import CaptureRegisterFace
from copy import deepcopy

# Set up device params
DEVICE_ID = cfg['deviceIdAzure']
DEVICE_LABEL = cfg['deviceLabel']
BUILDING_ID = user_cfg['buildingId']

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
REC_THRESHOLD = cfg['faceDetection']['threshold']

# Set up time params
TIME_MEASURE_TEMP = cfg['periodTime']['measureTemp']
TIME_SEND_REC = cfg['periodTime']['sendRecMess']

# Set up tracking params
MAX_DISAPEARED_FRAMES = cfg['personTracking']['NoOfDisapearFrames']
BUFFER_TEMP = cfg['personTracking']['bufSizeTempPersonTracking']
BUFFER_NAME_ID = cfg['personTracking']['bufSizeNameAndIdPersonTracking']
THRESHOLD_TEMP_FEVER = user_cfg['feverTemperature']

# Set up registeration params
NUM_FRONT_PICS = cfg['registration']['numFontPics']
NUM_LEFT_PICS = cfg['registration']['numLeftPics']
NUM_RIGHT_PICS = cfg['registration']['numRightPics']
STACK_NUMBER = cfg['registration']['stackNumberPics']
LEFT_THRESHOLD = user_cfg['registration']['leftThreshold']
RIGHT_THRESHOLD = user_cfg['registration']['rightThreshold']
FRONT_RANGE = user_cfg['registration']['frontRange']
FRAMES_BETWEEN_CAP = cfg['registration']['frameBetweenCapture']

# Flags of mode
ENABLE_SENDING_TO_CLOUD = cfg['iotHub']['enableSending']

#setup threshold of face mask detection
FACEMASK_DETECTION_THRESHOLD = cfg['thresholdFaceMaskDetection']

#setup calibration params
CALIBRATE_TIME = user_cfg['calibrationTimeForUser']

# user offset
USER_TEMP_OFFSET = user_cfg['offsetTemperature']


class DeviceAppFunctions():

    def __init__(self):
        self.color = np.zeros((480,640,3), np.uint8)
        self.rgb_temp = np.zeros((480,640,3), np.uint8)
        self.MODE = 'WAITING'

        self.deletedObjectRecord = OrderedDict()

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
        self.faceDetect = LightFaceDetection(PROTO_RFB320, MODEL_RFB320, REC_THRESHOLD)
        self.faceDetectTemp = LightFaceDetection(PROTO_RFB320, MODEL_RFB320, REC_THRESHOLD)
        # self.faceDetect = FaceDetection(MODEL_SSD, PROTO_SSD)
        # self.faceDetectTemp = FaceDetection(MODEL_SSD, PROTO_SSD)
        #self.faceDetect = FaceDetectionLightRfb()
        #self.faceDetectTemp = FaceDetectionLightRfb()
        self.landmarkDetect = LandmarkDetection(FACEMASK_DETECTION_THRESHOLD, LANDMARK_MODEL)


    def initObjectTracking(self):
        self.ct = CentroidTracker(MAX_DISAPEARED_FRAMES, BUFFER_NAME_ID, BUFFER_TEMP)
        # self.trackableObjects = {}
        self.objects, _ = self.ct.update([],[],RGB_SCALE, THRESHOLD_TEMP_FEVER)


    def initIoTConnection(self):
        self.conn = IotConn(self.MODE, CONNECTION_STRING_DEVICE, CONNECTION_STRING_BLOB , self.objects)


    def process(self):
        start = time.time()
        self.frame, self.ori = self.rgb.getFrame()
        rects = self.faceDetect.detectFaces(self.frame)

        if (self.MODE == 'NORMAL' or self.MODE == 'CALIBRATE'):
            self.objects,deletedObject = self.ct.update(rects, self.ori, RGB_SCALE, THRESHOLD_TEMP_FEVER)
            
            if (deletedObject):
                Thread(target=self.sendRecordsInfo, args=(deletedObject, ),daemon=True).start()
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

        elif (self.MODE == 'WAITING'):
            time.sleep(0.02)

        self.displayFrame = self.frame

        if (self.MODE == 'CALIBRATE'):
            if (len(self.objects.items()) == 1):
                if (self.calibrate_person_ID != list(self.objects.items())[0][0]):
                    self.calibrate_time = time.time()
                    self.calibrate_person_ID =  list(self.objects.items())[0][0]
                    print ('reset' )
                elif (time.time() - self.calibrate_time > CALIBRATE_TIME):
                    self.camera_input_calibrate_temp = list(self.objects.items())[0][1].record_temperature
                    return 'CALIBRATE_SUCCESS'
            return 'CALIBRATE_TOO_MUCH_PEOPLE'

        # print('time frame: {:.5f}'.format(time.time() - start))
        
        return "NORMAL"

    def measureTemperatureAllPeople(self):
        time.sleep(1)
        while (self.MODE == 'NORMAL' or self.MODE == 'CALIBRATE'):
            try:
                objects_measurement = deepcopy(self.objects)
                ct_temp = deepcopy(self.ct)
                self.rgb_temp, rgb_ori = self.rgb.getCurrentFrame()
                self.lep.update()
                thermal, temp = self.lep.getFrame()
                raw = thermal

                thermal = cv2.resize(thermal,(THERMAL_WIDTH,THERMAL_HEIGHT))
                self.color = cv2.applyColorMap(thermal, cv2.COLORMAP_JET)
                
                rects_measurement = self.faceDetectTemp.detectFaces(self.rgb_temp, 35)
                objects_measurement, _ = ct_temp.update(rects_measurement,rgb_ori,RGB_SCALE)


                measureTemperature(self.color, temp, self.objects, objects_measurement, USER_TEMP_OFFSET, RGB_SCALE)
                
                              
            except Exception as identifier:
                print(identifier)
            time.sleep(TIME_MEASURE_TEMP)


    def sendRecordsInfo(self, DeletedObjects):
        for (objectID, obj) in DeletedObjects.items():
            self.deletedObjectRecord[objectID] = obj

            _, buffer = cv2.imencode('.jpg', cv2.resize(obj.face_rgb,(FACE_SIZE,FACE_SIZE)))
            pic_str = base64.b64encode(buffer)
            pic_str = pic_str.decode()

            if (ENABLE_SENDING_TO_CLOUD):
                self.conn.sendRecord( DEVICE_LABEL, obj.id, obj.record_temperature, pic_str, obj.have_mask)


    def drawInfoOnFrameAndCheckRecognize( self, rects):
        for (objectID, obj) in list(self.objects.items()):
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
        while personID in self.objects and (self.MODE == 'NORMAL' or self.MODE == 'CALIBRATE'):
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
        return self.deletedObjectRecord

    def getSettingsParam(self):
        return CALIBRATE_TIME, THRESHOLD_TEMP_FEVER
    
    def selectRegisterMode(self):
        self.store_registered_imgs = None
        self.MODE = 'REGISTER'
        self.register = CaptureRegisterFace(NUM_FRONT_PICS,NUM_LEFT_PICS,NUM_RIGHT_PICS, LEFT_THRESHOLD, RIGHT_THRESHOLD, FRONT_RANGE, STACK_NUMBER, FRAMES_BETWEEN_CAP)

    def selectNormalMode(self):
        global USER_TEMP_OFFSET
        USER_TEMP_OFFSET = user_cfg['offsetTemperature']
        self.initObjectTracking()
        if (self.MODE != 'CALIBRATE'):
            self.measureTemp.join()
            self.measureTemp = Thread(target=self.measureTemperatureAllPeople, daemon=True)
            self.measureTemp.start()
        self.MODE = 'NORMAL'
        self.conn.restartListener(self.objects)
    
    def selectCalibrateMode(self):
        global USER_TEMP_OFFSET
        USER_TEMP_OFFSET = 0
        self.initObjectTracking()
        self.calibrate_person_ID = None
        self.camera_input_calibrate_temp = None
        self.MODE = 'CALIBRATE'

    def createUserTemperatureOffset(self, ground_truth_temp):
        global USER_TEMP_OFFSET, user_cfg
        USER_TEMP_OFFSET = float(ground_truth_temp) - self.camera_input_calibrate_temp
        user_cfg['offsetTemperature'] = float(USER_TEMP_OFFSET)
        self.MODE = 'NORMAL'
        with open("user_settings.yaml", "w") as f:
            yaml.dump(user_cfg, f)
        
    def updateSettingParams(self, time_calib=CALIBRATE_TIME, temp_fever=THRESHOLD_TEMP_FEVER):
        global CALIBRATE_TIME, THRESHOLD_TEMP_FEVER, user_cfg
        THRESHOLD_TEMP_FEVER = temp_fever
        CALIBRATE_TIME = time_calib
        user_cfg['feverTemperature'] = float(THRESHOLD_TEMP_FEVER)
        user_cfg['calibrationTimeForUser'] = int(CALIBRATE_TIME)
        with open("user_settings.yaml", "w") as f:
            yaml.dump(user_cfg, f)

    def sendRegisteredInfoToServer(self, name_of_new_user):
        if (self.store_registered_imgs is not None and ENABLE_SENDING_TO_CLOUD):
            Thread(target=self.conn.registerToAzure, args=(BUILDING_ID ,name_of_new_user, self.store_registered_imgs, FACE_SIZE, ), daemon=True).start()
        self.store_registered_imgs = None
        print('Registered')
    
    def activateDevice(self, pinCode):
        status = self.conn.activeDevice(DEVICE_ID, DEVICE_LABEL, pinCode)
        if (status):
            self.selectNormalMode()
        return status

    def deactivateDevice(self):
        self.MODE = 'WAITING'

    def stop(self):
        self.MODE = "OFF"
        self.rgb.stop()