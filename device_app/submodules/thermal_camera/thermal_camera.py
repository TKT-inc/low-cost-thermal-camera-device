from threading import Thread
import numpy as np
import time
from submodules.thermal_camera.pylepton.Lepton import Lepton
import cv2
import ctypes
import pathlib

libname = pathlib.Path().absolute() / "device_app/submodules/thermal_camera/LeptonSDKWrapper/LeptonWrapper.so"
LeptonWrapper = ctypes.CDLL(libname)
"""
int lepton_connect();
void lepton_reboot();
void lepton_perform_ffc(); 
void lepton_manualFFC();
"""

class ThermalCam:
    def __init__(self, source):
        LeptonWrapper.lepton_perform_ffc()
        LeptonWrapper.lepton_manualFFC()
        self.temp = np.zeros((60,80,1), np.uint16)
        self.frame = np.zeros((480,640,3), np.uint8)
        self.source = source
        self.isWorking = True

    def checkWorkingStatus(self):
        return self.isWorking

    def updateFrame(self):
        try:
            with Lepton(self.source) as l:
                a,_ = l.capture(garbage_frame_print=True)
                self.temp = np.float32(a)
                cv2.normalize(a, a, 0, 65535, cv2.NORM_MINMAX)
                np.right_shift(a, 8, a)
                self.frame = np.uint8(a)
        except Exception as e:
            print(e)
            self.isWorking = False
            self.reset()
            raise

    def reset(self):
        print('reset thermal camera') 
        LeptonWrapper.lepton_reboot()
        self.isWorking = True
        return

    def autoCalibrate(self):
        LeptonWrapper.lepton_perform_ffc()
        return
    
    def getFrame(self):
        self.updateFrame()
        return self.frame, self.temp