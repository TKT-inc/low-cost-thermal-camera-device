import numpy as np
from threading import Thread
import cv2

class RgbCam:
    def __init__(self, src, width, height):
        self.width = width
        self.height = height
        self.capture = cv2.VideoCapture(src)
        _, self.ori = self.capture.read()
        self.frame = cv2.resize(self.ori, (self.width, self.height))
        # self.capture.set(cv2.CAP_PROP_EXPOSURE, 40)
        self.working = True
        self.thread = Thread(target=self.update, daemon=True)
        self.thread.start()

    
    def update(self):
        while self.working:
            try:
                _, self.ori = self.capture.read()                
                if self.ori is not None:
                    self.frame = cv2.resize(self.ori, (self.width, self.height))
            except Exception as identifier:
                pass
            

    def getFrame(self):
        return self.frame, self.ori

    def stop(self):
        self.working = False
        self.thread.join()
        self.capture.release()
