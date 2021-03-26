import numpy as np
import cv2 as cv
import math
import os, sys
import yaml

Affine = [[0.658674180507659912109375000000000000000000000000000000000000,0.012693935073912143707275390625000000000000000000000000000000,201.842025756835937500000000000000000000000000000000000000000000],[0.077574044466018676757812500000000000000000000000000000000000,0.406205922365188598632812500000000000000000000000000000000000,254.944992065429687500000000000000000000000000000000000000000000]]

def AffineConvertCoor(x, y):
    convert_x = int(Affine[0][0] * x + Affine[0][1] * y + Affine[0][2])
    convert_y = int(Affine[1][0] * x + Affine[1][1] * y + Affine[1][2])
    print((convert_x, convert_y))
    return convert_x, convert_y 

def getAffineMatrix(src_list, dst_list):
    src_pts = np.array(src_list).astype(np.float32)
    dst_pts = np.array(dst_list).astype(np.float32)
    Affine = cv.getAffineTransform(src_pts, dst_pts)
    Affine = np.asarray(Affine, dtype=np.float32)
    return Affine

