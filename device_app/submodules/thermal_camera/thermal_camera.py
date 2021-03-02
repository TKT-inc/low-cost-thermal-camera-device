from threading import Thread
import numpy as np
from pylepton import Lepton
import cv2

class ThermalCam:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.temp = np.zeros((60,80,1), np.uint16)
        self.frame = np.zeros((480,640,3), np.uint8)
        self.thread = Thread(target=self.update)
        self.thread.daemon = True
        self.thread.start()
    
    def update(self):
        while True:
            with Lepton("/dev/spidev0.0") as l:
                a,_ = l.capture()
                self.temp = np.float32(a)
                cv2.normalize(a, a, 0, 65535, cv2.NORM_MINMAX)
                np.right_shift(a, 8, a)
                self.frame = np.uint8(a)
    def getFrame(self):
        return self.frame, self.temp