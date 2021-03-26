from threading import Thread
import numpy as np
import time
from pylepton import Lepton
import cv2

class ThermalCam:
    def __init__(self, source):
        self.temp = np.zeros((60,80,1), np.uint16)
        self.frame = np.zeros((480,640,3), np.uint8)
        self.source = source
        self.available = False

    def updateFrame(self):
        with Lepton(self.source) as l:
            a,_ = l.capture()
            self.temp = np.float32(a)
            cv2.normalize(a, a, 0, 65535, cv2.NORM_MINMAX)
            np.right_shift(a, 8, a)
            self.frame = np.uint8(a)

    def update(self):
        self.thread = Thread(target=self.updateFrame, daemon=True)
        self.thread.start()

    def getFrame(self):
        self.thread.join()
        return self.frame, self.temp