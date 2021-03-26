import numpy as np
import cv2 as cv
import math
import os, sys
import yaml

H = [[0.538015365600585937500000000000000000000000000000000000000000,0.014510816894471645355224609375000000000000000000000000000000,200.539199829101562500000000000000000000000000000000000000000000],[-0.041604161262512207031250000000000000000000000000000000000000,0.635743856430053710937500000000000000000000000000000000000000,188.270065307617187500000000000000000000000000000000000000000000],[-0.000245758274104446172714233398437500000000000000000000000000,0.000016881605915841646492481231689453125000000000000000000000,1.000000000000000000000000000000000000000000000000000000000000]]

def PerspectiveTrans(src_point,h):
    a = np.array([src_point]) 
    a=np.array(a.transpose())
    a=np.vstack((a,np.array(1)))
    a_transformed_homo = np.dot(h,a)
    scale_factor=a_transformed_homo[2][0]
    a_transformed_euk=np.divide(a_transformed_homo,scale_factor)
    return a_transformed_euk

def HomographyConvertCoor(x, y):
    convert_x = int((H[0][0] * x + H[0][1] * y + H[0][2]) / (H[2][0] * x + H[2][1] * y + H[2][2]))
    convert_y = int((H[1][0] * x + H[1][1] * y + H[1][2]) / (H[2][0] * x + H[2][1] * y + H[2][2]))
    print((convert_x, convert_y))
    return convert_x, convert_y 

def getHomographyMatrix(src_list, dst_list):
    src_pts = np.array(src_list).reshape(-1,1,2)
    dst_pts = np.array(dst_list).reshape(-1,1,2)
    H, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC, 5.0)
    H = np.asarray(H, dtype=np.float32)
    return H