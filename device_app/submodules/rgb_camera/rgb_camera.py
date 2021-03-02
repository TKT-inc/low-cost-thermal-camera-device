import numpy as np
from threading import Thread
import cv2

class RgbCam:
    def __init__(self, src, width, height):
        self.width = width
        self.height = height
        self.frame = np.zeros((480,640,3), np.uint8)
        self.capture = cv2.VideoCapture(src)
    
    def getFrame(self):
        _, self.ori = self.capture.read()
        return cv2.resize(ori, (self.width, self.height))

    def getOriginFrame(self):
        return self.capture.read()