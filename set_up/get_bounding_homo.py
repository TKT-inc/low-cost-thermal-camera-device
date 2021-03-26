import numpy as np
import cv2 as cv
import math
import yaml
with open("../configuration.yaml") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
from pylepton import Lepton

drawing = False # true if mouse is pressed
src_x, src_y = -1,-1
dst_x, dst_y = -1,-1

src_list = []
dst_list = []

src_path = 'imgs/thermal.png' 
dst_path = 'imgs/rgb.png' 
raw_path = 'imgs/raw.png'

H = [[ 3.32909508e-01, -3.54937924e-01,  1.15943911e+02],
 [-1.15060046e-01,  5.02427632e-01,  5.26859359e+01],
 [-5.58344967e-04, -7.89069807e-04,  1.00000000e+00]]

# mouse callback function
def select_points_src(event,x,y,flags,param):
    global src_x, src_y, drawing
    if event == cv.EVENT_LBUTTONDOWN:
        drawing = True
        src_x, src_y = x,y
        cv.circle(thermal_frame,(x,y),5,(0,0,255),-1)
    elif event == cv.EVENT_LBUTTONUP:
        drawing = False

# mouse callback function
def select_points_dst(event,x,y,flags,param):
    global dst_x, dst_y, drawing
    if event == cv.EVENT_LBUTTONDOWN:
        drawing = True
        dst_x, dst_y = x,y
        cv.circle(rgb_frame,(x,y),5,(0,0,255),-1)
    elif event == cv.EVENT_LBUTTONUP:
        drawing = False


def convertCoordinates(x, y, H_raw):
    H = np.linalg.inv(H_raw)
    convert_x = round((H[0][0] * x + H[0][1] * y + H[0][2]) / (H[2][0] * x + H[2][1] * y + H[2][2]))
    convert_y = round((H[1][0] * x + H[1][1] * y + H[1][2]) / (H[2][0] * x + H[2][1] * y + H[2][2]))
    return convert_x, convert_y 

def get_plan_view(src_list, dst_list):
    print(len(src_list))
    src_pts = np.array(src_list).reshape(-1,1,2)
    dst_pts = np.array(dst_list).reshape(-1,1,2)
    H, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC,3.0)
    str1 = '['
    for i in range(len(H)):
        str1 += '['
        for j in range(len(H[i])):
            str1 = str1 + f'{H[i][j]:.60f}'
            if j != 2:
                str1 += ','
        str1 += ']'
        if (i != 2):
            str1 += ','
    str1 += ']'
    print(str1)

def select_points_planview(event,x,y,flags,param):
    global planview_x, planview_y, drawing, planview_copy
    if event == cv.EVENT_LBUTTONDOWN:
        drawing = True
        planview_x, planview_y = x,y
        cv.circle(planview_copy,(round(planview_x / 8), round(planview_y / 8)),1,(0,0,255),-1)
    elif event == cv.EVENT_LBUTTONUP:
        drawing = False

def merge_views(src, dst):
    plan_view = get_plan_view(src, dst)
    for i in range(0,dst.shape[0]):
        for j in range(0, dst.shape[1]):
            if(plan_view.item(i,j,0) == 0 and \
                plan_view.item(i,j,1) == 0 and \
                plan_view.item(i,j,2) == 0):
                    plan_view.itemset((i,j,0),dst.item(i,j,0))
                    plan_view.itemset((i,j,1),dst.item(i,j,1))
                    plan_view.itemset((i,j,2),dst.item(i,j,2))
    plan_view = cv.addWeighted(dst, 0.7, plan_view, 0.3, 0.0)
    return plan_view


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
event = 1
def click(event,x,y,flags, params):
    global src_list, dst_list
    if event == cv.EVENT_LBUTTONDBLCLK:
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
cv.setMouseCallback('rgb', click)
while (1):
    try:
        _, rgb_ori = rgb_cam.read()
        with Lepton(THERMAL_SOURCE) as l:
            a,_ = l.capture()
            cv.normalize(a, a, 0, 65535, cv.NORM_MINMAX)
            np.right_shift(a, 8, a)
            thermal =   np.uint8(a)
            thermal_frame = cv.resize(thermal,(640,480))
            thermal_frame = cv.applyColorMap(thermal_frame, cv.COLORMAP_INFERNO)
        rgb_frame = cv.resize(rgb_ori, (RGB_WIDTH, RGB_HEIGHT))
        cv.imshow("rgb", rgb_frame)
        cv.imshow("thermal", thermal_frame)
        k = cv.waitKey(1) & 0xFF
        if k == ord('q'):
            print('create plan view')
            #get_plan_view(src_list, dst_list)
            cv.imwrite("thermal-map.png", thermal_frame)
            cv.imwrite("rgb-map.png", rgb_ori)
            print("Complete")
            cv.destroyAllWindows()
            break
    except Exception as identifier:
        pass
    

cv.namedWindow('src')
cv.moveWindow("src", 80, 80)
#cv.setMouseCallback('src', select_points_src)

cv.namedWindow('dst')
cv.moveWindow("dst", 780, 80)
#cv.setMouseCallback('dst', select_points_dst)


# while(1):
    # cv.imshow('src',thermal_frame)
    # cv.imshow('dst',rgb_frame)
    # # cv.imshow('raw', raw_copy)
    # k = cv.waitKey(1) & 0xFF
    # if k == ord('s'):
    #     print('save points')
    #     cv.circle(thermal_frame,(src_x,src_y),5,(0,255,0),-1)
    #     cv.circle(rgb_frame,(dst_x,dst_y),5,(0,255,0),-1)
    #     src_list.append([src_x, src_y])
    #     dst_list.append([dst_x,dst_y])
    #     print("src points:")
    #     print(src_list)
    #     print("dst points:")
    #     print(dst_list)
    # elif k == ord('h'):
    #     print('create plan view')
    #     plan_view = get_plan_view()
    # elif k == ord('q'):
    #     break
    
cv.destroyAllWindows()