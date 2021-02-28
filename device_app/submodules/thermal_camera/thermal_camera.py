import threading
import numpy as np
import cv2

class ThermalCam:
    def __init__(self, src, width, height):
        self.width = width
        self.height = height
        self.heat = heat
        self.temp = np.zeros((60,80,1), np.uint16)
        self.frame = np.zeros((480,640,3), np.uint8)
        self.thread = Thread(target=self.update, args=(heat,))
        self.thread.daemon = True
        self.thread.start()
    
    def update(self, heat):
        while True:
            with Lepton("/dev/spidev0.0") as l:
                a,_ = l.capture()
                self.temp = np.float32(a)
                cv2.normalize(a, a, 0, 65535, cv2.NORM_MINMAX)
                np.right_shift(a, 8, a)
                self.frame = np.uint8(a)
    def getFrame(self):
        return self.frame, self.temp