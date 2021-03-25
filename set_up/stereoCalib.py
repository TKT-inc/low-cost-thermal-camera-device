import numpy as np
import cv2 as cv
import math
import os, sys
import yaml

rvecs_B = np.asmatrix(np.asarray([[0.989578759940793251104196315282024443149566650390625000000000,0.028032132536062757954820057193501270376145839691162109375000,-0.141237662893161225463600771945493761450052261352539062500000],[-0.116964560652847743282833903322170954197645187377929687500000,0.728574805392132374137759143195580691099166870117187500000000,-0.674905952336399606039663012779783457517623901367187500000000],[0.083983149651152985692981189913552952930331230163574218750000,0.684392396577648165489904386049602180719375610351562500000000,0.724260918510294282590677994448924437165260314941406250000000]], 
dtype=np.float32))
tvecs_B =  np.asmatrix(np.asarray([[44.699818063989425809268141165375709533691406250000000000000000],[-278.436143950427549498272128403186798095703125000000000000000000],[257.925760686436490232154028490185737609863281250000000000000000]], 
dtype=np.float32))
mtx_B = np.asmatrix(np.asarray([[640.000000000000000000000000000000000000000000000000000000000000,0.000000000000000000000000000000000000000000000000000000000000,320.000000000000000000000000000000000000000000000000000000000000],[0.000000000000000000000000000000000000000000000000000000000000,640.000000000000000000000000000000000000000000000000000000000000,240.000000000000000000000000000000000000000000000000000000000000],[0.000000000000000000000000000000000000000000000000000000000000,0.000000000000000000000000000000000000000000000000000000000000,1.000000000000000000000000000000000000000000000000000000000000]], 
dtype=np.float32))
dist_B = np.asmatrix(np.asarray([[0.000000000000000000000000000000000000000000000000000000000000],[0.000000000000000000000000000000000000000000000000000000000000],[0.000000000000000000000000000000000000000000000000000000000000],[0.000000000000000000000000000000000000000000000000000000000000],[0.000000000000000000000000000000000000000000000000000000000000]], 
dtype=np.float32))

R_B = np.asarray([[0.132481257697653703742091124695434700697660446166992187500000],[0.098766456045620509840432532655540853738784790039062500000000],[0.046472273654710780088628041539777768775820732116699218750000]], dtype=np.float32)

T_B = np.asarray([[-158.451552483780091051812632940709590911865234375000000000000000],[-80.942344357704868684777466114610433578491210937500000000000000],[970.027323726767122025194112211465835571289062500000000000000000]], dtype=np.float32)

CMat = np.asarray([[640.000000000000000000000000000000000000000000000000000000000000,0.000000000000000000000000000000000000000000000000000000000000,320.000000000000000000000000000000000000000000000000000000000000],[0.000000000000000000000000000000000000000000000000000000000000,640.000000000000000000000000000000000000000000000000000000000000,240.000000000000000000000000000000000000000000000000000000000000],[0.000000000000000000000000000000000000000000000000000000000000,0.000000000000000000000000000000000000000000000000000000000000,1.000000000000000000000000000000000000000000000000000000000000]], dtype=np.float32)
dist_coeff_B = np.asarray([[0.000000000000000000000000000000000000000000000000000000000000],[0.000000000000000000000000000000000000000000000000000000000000],[0.000000000000000000000000000000000000000000000000000000000000],[0.000000000000000000000000000000000000000000000000000000000000]], dtype=np.float32)

def pre_calibration(imgpoints, objpoints, gray):
    # imgpoints -> 2D plane coordinates
    # objpoints -> 3D world coordinates
    ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
    rotation_mat = np.zeros(shape=(3, 3))
    R = cv.Rodrigues(rvecs[0], rotation_mat)[0]
    # P = np.matmul(mtx, np.column_stack((R, tvecs[0])))
    P = np.column_stack((np.matmul(mtx,R), tvecs[0]))
    return rvecs[0], tvecs[0], mtx, dist, P

def calculateIntrinsicMatrix(img):
    size = img.shape
    focal_length = size[1]
    center = (size[1]/2, size[0]/2)
    mtx = np.array([[focal_length, 0, center[0]],
                    [0, focal_length, center[1]],
                    [0, 0, 1]], dtype="double")
    return mtx

def projection_error(objpoints, imgpoints, rvecs, tvecs, mtx, dist):
    mean_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv.projectPoints(objpoints, rvecs, tvecs, mtx, dist)
        error = cv.norm(imgpoints[i], imgpoints2, cv.NORM_L2)/len(imgpoints2)
        print(error)
        mean_error += error
    print( "total error: {}".format(mean_error/len(objpoints)) )

def backProjectionConvert(src_x, src_y, rvecs, tvecs, mtx, dist):
    test= []
    test.append([[src_x, src_y, 1]])
    threed_point = np.asarray(test, dtype=np.float32)
    imgpoints2, _ = cv.projectPoints(threed_point, rvecs, tvecs, mtx, dist)
    print("Convert points: ")
    print((imgpoints2))
    return imgpoints2

# while(1):
#     cv.imshow('src',src_copy)
#     cv.imshow('dst',dst_copy)
#     k = cv.waitKey(1) & 0xFF
#     if k == ord('s'):
#         cv.circle(src_copy,(src_x,src_y),5,(0,255,0),-1)
#         cv.circle(dst_copy,(dst_x,dst_y),5,(0,255,0),-1)
#         src_list.append([[src_x, src_y]])
#         src_list_3d.append([[src_x, src_y, 0]])
#         dst_list.append([[dst_x, dst_y]])
#         dst_list_3d.append([[dst_x, dst_y, 0]])
#         print("src points:")
#         print(src_list)
#         print("dst points:")
#         print(dst_list)
#     elif k == ord('h'):
#         print('create plan view')
#         src_list_points_2d = np.asarray(src_list, dtype=np.float32)
#         src_list_points_3d = np.asarray(src_list_3d, dtype=np.float32)
#         dst_list_points_2d = np.asarray(dst_list, dtype=np.float32)
#         dst_list_points_3d = np.asarray(dst_list_3d, dtype=np.float32)

#         matrix_src_list.append(src_list_points_2d)
#         matrix_src_list_3d.append(src_list_points_3d)

#         matrix_dst_list.append(dst_list_points_2d)
#         matrix_dst_list_3d.append(dst_list_points_3d)

#         # mtx_A = calculateIntrinsicMatrix(src_copy)
#         mtx_B = calculateIntrinsicMatrix(dst_copy)
#         dist_coeffs = np.zeros((4,1))
#         (success, R2, T2) = cv.solvePnP(src_list_points_3d, dst_list_points_2d, mtx_B, dist_coeffs)

#         # flags = 0
#         # flags |= cv.CALIB_FIX_INTRINSIC
#         # criteria_stereo= (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
#         # retS, mtx_A, dist_A, mtx_B, dist_B, Rot, Trns, Emat, Fmat = cv.stereoCalibrate(matrix_src_list_3d, matrix_src_list, matrix_dst_list, mtx_A, 0, mtx_B, 0, dst_copy.shape[::-1], criteria_stereo, flags)
        
#         # rectify_scale = 1
#         # R1, R2, P1, P2, Q, validPixROI1, validPixROI2 = cv.stereoRectify(mtx_A, dist_A, mtx_B, dist_B, dst_copy.shape[::-1], Rot, Trns, rectify_scale,(0,0))
#         print("B:")
#         arrayToStringArray(R2)
#         arrayToStringArray(T2)
#         arrayToStringArray(mtx_B)
#         arrayToStringArray(dist_coeffs)
#         # # objpoints A, imgpoints A
#         # rvecs_A, tvecs_A, mtx_A, dist_A, P_A = pre_calibration(matrix_src_list, matrix_src_list_3d, src_gray)
#         # # objpoints B, imgpoints B
#         # rvecs_B, tvecs_B, mtx_B, dist_B, P_B = pre_calibration(matrix_dst_list, matrix_src_list_3d, dst_copy)
#         # print("B: ")
#         # arrayToStringArray(rvecs_B)
#         # arrayToStringArray(tvecs_B)
#         # arrayToStringArray(mtx_B)
#         # arrayToStringArray(dist_B)
#         # print("A: ")
#         # arrayToStringArray(rvecs_A)
#         # arrayToStringArray(tvecs_A)
#         # arrayToStringArray(mtx_A)
#         # arrayToStringArray(dist_A)
#         # get_plan_view()
#     elif k == ord('m'):
#         print("pre-calibration")
#     elif k == ord('q'):
#         break
# cv.destroyAllWindows()

