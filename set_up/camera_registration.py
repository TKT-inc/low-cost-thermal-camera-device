import numpy as np
import cv2 as cv
import math
import os, sys
import yaml
with open("../configuration.yaml") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
np.set_printoptions(suppress=True)
from affine import *
from homography import *
from stereoCalib import *
from pylepton import Lepton

drawing = False # true if mouse is pressed
src_x, src_y = -1,-1
dst_x, dst_y = -1,-1

src_list = []
src_list_3d = []

matrix_src_list = []
matrix_src_list_3d = []

dst_list = []
dst_list_3d = []

matrix_dst_list = []
matrix_dst_list_3d = []

map_flag = 1
case_flag = 0
method = 2 # 0: Affine, 1: Homo, 2: 3D

src_path = 'image/rgb.png' if map_flag == 1 else 'image/rgb-test.png'
dst_path = 'image/thermal.png' if map_flag == 1 else 'image/thermal-test.png'


def arrayToStringArray(array):
    str1 = '['
    for i in range(len(array)):
        str1 += '['
        for j in range(len(array[i])):
            str1 = str1 + f'{array[i][j]:.60f}'
            if j != (len(array[i]) - 1):
                str1 += ','
        str1 += ']'
        if (i != (len(array) - 1)):
            str1 += ','
    str1 += ']'
    print(str1)
    print("")
    return str1

RGB_SOURCE = cfg['camera']['rgb']['source']
RGB_WIDTH = cfg['camera']['rgb']['scaleWidth']
RGB_HEIGHT = cfg['camera']['rgb']['scaleHeight']
RGB_SCALE = 1920 / RGB_WIDTH
THERMAL_SOURCE = cfg['camera']['thermal']['source']
THERMAL_WIDTH = cfg['camera']['thermal']['scaleWidth']
THERMAL_HEIGHT = cfg['camera']['thermal']['scaleHeight']

thermal_cam = cv.VideoCapture(THERMAL_SOURCE)
rgb_cam = cv.VideoCapture(RGB_SOURCE)

cv.namedWindow('thermal')
cv.moveWindow("thermal", 80, 80)

cv.namedWindow('rgb')
cv.moveWindow('rgb', 780, 80)

event = 1
def click(event,x,y,flags, params):
	global src_list, dst_list
	if event == cv.EVENT_LBUTTONDBLCLK:
		if (method == 1):
			ROI_RGB = cv.selectROI(rgb_frame, False)
			ROI_THER = cv.selectROI(thermal_frame, False)
			src_list.append([ROI_THER[0], ROI_THER[1]])
			src_list.append([ROI_THER[0] + ROI_THER[2], ROI_THER[1]])
			src_list.append([ROI_THER[0] + ROI_THER[2], ROI_THER[1] + ROI_THER[3]])
			src_list.append([ROI_THER[0], ROI_THER[1] + ROI_THER[3]])

			dst_list.append([ROI_RGB[0], ROI_RGB[1]])
			dst_list.append([ROI_RGB[0] + ROI_RGB[2], ROI_RGB[1]])
			dst_list.append([ROI_RGB[0] + ROI_RGB[2], ROI_RGB[1] + ROI_RGB[3]])
			dst_list.append([ROI_RGB[0], ROI_RGB[1] + ROI_RGB[3]])
		elif (method == 0):
			ROI_RGB = cv.selectROI(rgb_frame, False)
			ROI_THER = cv.selectROI(thermal_frame, False)
			src_list.append([ROI_THER[0], ROI_THER[1]])
			src_list.append([ROI_THER[0] + ROI_THER[2], ROI_THER[1]])
			src_list.append([ROI_THER[0] + ROI_THER[2], ROI_THER[1] + ROI_THER[3]])

			dst_list.append([ROI_RGB[0], ROI_RGB[1]])
			dst_list.append([ROI_RGB[0] + ROI_RGB[2], ROI_RGB[1]])
			dst_list.append([ROI_RGB[0] + ROI_RGB[2], ROI_RGB[1] + ROI_RGB[3]])
		elif (method == 2):
			ROI_RGB = cv.selectROI(rgb_frame, False)
			ROI_THER = cv.selectROI(thermal_frame, False)
			src_list.append([ROI_THER[0], ROI_THER[1]])
			src_list_3d.append([[ROI_THER[0], ROI_THER[1], 0]])

			src_list.append([ROI_THER[0] + ROI_THER[2], ROI_THER[1]])
			src_list_3d.append([[ROI_THER[0] + ROI_THER[2], ROI_THER[1], 0]])

			src_list.append([ROI_THER[0] + ROI_THER[2], ROI_THER[1] + ROI_THER[3]])
			src_list_3d.append([[ROI_THER[0] + ROI_THER[2], ROI_THER[1] + ROI_THER[3], 0]])

			src_list.append([ROI_THER[0], ROI_THER[1] + ROI_THER[3]])
			src_list_3d.append([[ROI_THER[0], ROI_THER[1] + ROI_THER[3], 0]])

			dst_list.append([ROI_RGB[0], ROI_RGB[1]])
			dst_list_3d.append([[ROI_RGB[0], ROI_RGB[1], 0]])

			dst_list.append([ROI_RGB[0] + ROI_RGB[2], ROI_RGB[1]])
			dst_list_3d.append([[ROI_RGB[0] + ROI_RGB[2], ROI_RGB[1], 0]])

			dst_list.append([ROI_RGB[0] + ROI_RGB[2], ROI_RGB[1] + ROI_RGB[3]])
			dst_list_3d.append([[ROI_RGB[0] + ROI_RGB[2], ROI_RGB[1] + ROI_RGB[3], 0]])

			dst_list.append([ROI_RGB[0], ROI_RGB[1] + ROI_RGB[3]])
			dst_list_3d.append([[ROI_RGB[0], ROI_RGB[1] + ROI_RGB[3], 0]])

cv.setMouseCallback('rgb', click)

while (1):
	# try:
		_, rgb_ori = rgb_cam.read()
		with Lepton(THERMAL_SOURCE) as l:
			a,_ = l.capture()
			cv.normalize(a, a, 0, 65535, cv.NORM_MINMAX)
			np.right_shift(a, 8, a)
			thermal = np.fliplr(np.uint8(a))
			thermal_frame = cv.resize(thermal,(640,480))
			thermal_frame = cv.applyColorMap(thermal_frame, cv.COLORMAP_INFERNO)
		rgb_frame = cv.resize(rgb_ori, (RGB_WIDTH, RGB_HEIGHT))
		cv.imshow("rgb", rgb_frame)
		cv.imshow("thermal", thermal_frame)
		k = cv.waitKey(1) & 0xFF
		if k == ord('d'):
			print("get 3D")
			# 3D convert
			src_list_points_2d = np.asarray(src_list, dtype=np.float32)
			src_list_points_3d = np.asarray(src_list_3d, dtype=np.float32)
			dst_list_points_2d = np.asarray(dst_list, dtype=np.float32)
			dst_list_points_3d = np.asarray(dst_list_3d, dtype=np.float32)

			matrix_src_list.append(src_list_points_2d)
			matrix_src_list_3d.append(src_list_points_3d)

			matrix_dst_list.append(dst_list_points_2d)
			matrix_dst_list_3d.append(dst_list_points_3d)

			mtx_B = calculateIntrinsicMatrix(thermal_frame)
			dist_coeffs = np.zeros((4,1))
			(success, R2, T2) = cv.solvePnP(dst_list_points_3d, src_list_points_2d, mtx_B, dist_coeffs)
			print("Rotation vector:")
			arrayToStringArray(R2)
			print("Translation vector:")
			arrayToStringArray(T2)
			print("Camera intrinsic:")
			arrayToStringArray(mtx_B)
			print("Dist coeff:")
			arrayToStringArray(dist_coeffs)
		elif k == ord('h'):
			# Homograpgy
			H = getHomographyMatrix(src_list, dst_list)
			arrayToStringArray(H)
		elif k == ord('a'):
			# Affine
			Affine = getAffineMatrix(dst_list, src_list)
			arrayToStringArray(Affine)
		elif k == ord('q'):
			break
	# except Exception as identifier:
	# 	pass

cv.destroyAllWindows()

