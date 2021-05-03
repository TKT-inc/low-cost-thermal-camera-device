import numpy as np
import cv2 as cv
import math
import yaml
with open("../configuration.yaml") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
from pylepton import Lepton
import time


RGB_SOURCE = cfg['camera']['rgb']['source']
RGB_WIDTH = cfg['camera']['rgb']['scaleWidth']
RGB_HEIGHT = cfg['camera']['rgb']['scaleHeight']
RGB_SCALE = 1920 / RGB_WIDTH
THERMAL_SOURCE = cfg['camera']['thermal']['source']
THERMAL_WIDTH = cfg['camera']['thermal']['scaleWidth']
THERMAL_HEIGHT = cfg['camera']['thermal']['scaleHeight']

# thermal_cam = cv.VideoCapture(THERMAL_SOURCE)
# rgb_cam = cv.VideoCapture(RGB_SOURCE)


cv.namedWindow('thermal')


cv.namedWindow('rgb')


while (1):
    with Lepton(THERMAL_SOURCE) as l:
        a,_ = l.capture()
        thermal_matrix = a[int(120/8):int(360/8), int(200/8):int(400/8)]
        max_temp = np.max(thermal_matrix)
        temp = float(max_temp)/100.0 - 273.15
        print(f'{temp:.5f}')
        cv.normalize(a, a, 0, 65535, cv.NORM_MINMAX)
        np.right_shift(a, 8, a)
        thermal =   np.uint8(a)
        thermal_frame = cv.resize(thermal,(THERMAL_WIDTH,THERMAL_HEIGHT))
    thermal = cv.cvtColor(thermal_frame, cv.COLOR_GRAY2BGR)
    thermal = cv.applyColorMap(thermal, cv.COLORMAP_JET)
    cv.rectangle(thermal, (200, 120), (400, 360), (0,0,0), 2)
    cv.imshow("thermal", thermal)
    time.sleep(0.25)
    k = cv.waitKey(1) & 0xFF
    if k == ord('q'):
        cv.destroyAllWindows()
        break
