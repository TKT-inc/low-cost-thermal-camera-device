import numpy as np
import cv2 as cv
import math
import yaml
with open("../configuration.yaml") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
from pylepton import Lepton



RGB_SOURCE = cfg['camera']['rgb']['source']
RGB_WIDTH = cfg['camera']['rgb']['scaleWidth']
RGB_HEIGHT = cfg['camera']['rgb']['scaleHeight']
RGB_SCALE = 1920 / RGB_WIDTH
THERMAL_SOURCE = cfg['camera']['thermal']['source']
THERMAL_WIDTH = cfg['camera']['thermal']['scaleWidth']
THERMAL_HEIGHT = cfg['camera']['thermal']['scaleHeight']

# thermal_cam = cv.VideoCapture(THERMAL_SOURCE)
rgb_cam = cv.VideoCapture(RGB_SOURCE)


cv.namedWindow('thermal')
cv.moveWindow("thermal", 80, 80)

cv.namedWindow('rgb')
cv.moveWindow('rgb', 780, 80)

while (1):
    try:
        _, rgb_ori = rgb_cam.read()
        with Lepton(THERMAL_SOURCE) as l:
            a,_ = l.capture()
            print(a[30][40]/100.0 - 273.15)
            cv.normalize(a, a, 0, 65535, cv.NORM_MINMAX)
            np.right_shift(a, 8, a)
            thermal =   np.uint8(a)
            thermal_frame = cv.resize(thermal,(THERMAL_WIDTH,THERMAL_HEIGHT))
        rgb_frame = cv.resize(rgb_ori, (RGB_WIDTH, RGB_HEIGHT))
        cv.circle(thermal_frame, (320,240), 5, (0,255,0), -1)
        cv.imshow("rgb", rgb_frame)
        cv.imshow("thermal", thermal_frame)
        k = cv.waitKey(1) & 0xFF
        if k == ord('q'):
            cv.destroyAllWindows()
            rgb_cam.release()
            break
    except Exception as identifier:
        pass