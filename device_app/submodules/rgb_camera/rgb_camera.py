import numpy as np
from threading import Thread
import cv2

class RgbCam:
    def __init__(self, src, width, height):
        self.width = width
        self.height = height
        self.frame = np.zeros((480,640,3), np.uint8)
        self.capture = cv2.VideoCapture(src)
        self.thread = Thread(target=self.update)
        self.thread.daemon = True
        self.thread.start()
    
    def update(self):
        while True:
            _, self.ori = self.capture.read()
            if self.ori is not None:
                self.frame = cv2.resize(self.ori, (self.width, self.height))
    def getFrame(self):
        return self.frame
    def getOriginFrame(self):
        return self.ori