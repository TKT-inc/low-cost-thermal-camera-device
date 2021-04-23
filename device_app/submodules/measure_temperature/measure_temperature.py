import numpy as np
import cv2
import time

import yaml
import base64
with open("configuration.yaml") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

TRANSFORM_MATRIX = cfg['transMatrix']

#setup offset temperature
NUMBER_MAX_THERMAL_POINTS = cfg['measureTemperature']['numberMaxThermalPoints']
OFFSET_TEMPERATURE_DIST_COEF = cfg['measureTemperature']['offsetDistCoeffecient']
OFFSET_TEMPERATURE_DIST_INT = cfg['measureTemperature']['offsetDistIntercept']
# ROTATION_VECTOR = 

def measureTemperature(color,temp, objects, object_measurement, user_offset, scale):
    for (objectID, obj) in list(objects.items()):
        try:
            if (obj.temporary_dissapear):
                continue
            coordinates = object_measurement[objectID].coor
            thermal_start_x, thermal_start_y = convertRGBToThermalCoor(coordinates[0], coordinates[1])
            thermal_end_x, thermal_end_y = convertRGBToThermalCoor(coordinates[2], coordinates[3])
            
            cv2.rectangle(color, (thermal_start_x, thermal_start_y), (thermal_end_x, thermal_end_y), (0, 0, 0), 4)
            
            measured_temp = measureTemperatureFromCoor(temp, (thermal_start_x, thermal_start_y), (thermal_end_x, thermal_end_y) )
            
            face_area = (coordinates[2]-coordinates[0])*(coordinates[3]-coordinates[1])*(scale*2)
            offset_temp = user_offset +  measureOffsetTempOfDistance(face_area)
            
            temperature = (measured_temp/100.0) - 273.15 + offset_temp
            objects[objectID].updateTemperature(temperature)
        except Exception as identifier:
            print(identifier)


def convertRGBToThermalCoor(x, y):
    start = time.time()
    MAX_WIDTH = 640
    MAX_HEIGHT = 480
#     # Homography 
#     # H = np.linalg.inv(H_raw)
#     # convert_x = int((H[0][0] * x + H[0][1] * y + H[0][2]) / (H[2][0] * x + H[2][1] * y + H[2][2]))
#     # convert_y = int((H[1][0] * x + H[1][1] * y + H[1][2]) / (H[2][0] * x + H[2][1] * y + H[2][2]))
#     # Affine convert
#     H = H_raw 
#     convert_x = int(H[0][0] * x + H[0][1] * y + H[0][2])
#     convert_y = int(H[1][0] * x + H[1][1] * y + H[1][2])
#     # 3D convert
    rvecs = np.asmatrix(np.asarray([[-0.155208039313718210161496813270787242799997329711914062500000],[-0.131953500947026264311645604720979463309049606323242187500000],[0.019602272475897668940758578060012951027601957321166992187500]]), dtype=np.float32)
    tvecs = np.asmatrix(np.asarray([[-365.079587118443782856047619134187698364257812500000000000000000],[-176.352320461007423091359669342637062072753906250000000000000000],[934.825330462552301469258964061737060546875000000000000000000000]]
), dtype=np.float32)
    mtx = np.asmatrix(np.asarray([[640.000000000000000000000000000000000000000000000000000000000000,0.000000000000000000000000000000000000000000000000000000000000,320.000000000000000000000000000000000000000000000000000000000000],[0.000000000000000000000000000000000000000000000000000000000000,640.000000000000000000000000000000000000000000000000000000000000,240.000000000000000000000000000000000000000000000000000000000000],[0.000000000000000000000000000000000000000000000000000000000000,0.000000000000000000000000000000000000000000000000000000000000,1.000000000000000000000000000000000000000000000000000000000000]]
), dtype=np.float32)
    dist = np.asmatrix(np.asarray([[0.000000000000000000000000000000000000000000000000000000000000],[0.000000000000000000000000000000000000000000000000000000000000],[0.000000000000000000000000000000000000000000000000000000000000],[0.000000000000000000000000000000000000000000000000000000000000]]
), dtype=np.float32)
    test= []
    test.append([[x, y, 1]])
    threed_point = np.asarray(test, dtype=np.float32)
    imgpoints2, _ = cv2.projectPoints(threed_point, rvecs, tvecs, mtx, dist)
    convert_x = imgpoints2[0][0][0]
    convert_y = imgpoints2[0][0][1]
    if(convert_x > MAX_WIDTH):
        convert_x = MAX_WIDTH - 1
    if(convert_y > MAX_HEIGHT):
        convert_y = MAX_HEIGHT - 1
    # print( "{:.5f}" .format(time.time() - start))
    return convert_x, convert_y  

def measureOffsetTempOfDistance(face_area):
    return (face_area*OFFSET_TEMPERATURE_DIST_COEF + OFFSET_TEMPERATURE_DIST_INT)

def measureTemperatureFromCoor(temp_img, coor_start, coor_end):
    x_start = int(coor_start[0]/8)
    x_end = int(coor_end[0]/8)
    y_start = int(coor_start[1]/8)
    y_end = int(coor_end[1]/8)

    if (x_start == x_end):
        x_end += 1
    if (y_start == y_end):
        y_end += 1

    thermal_matrix = temp_img[y_start:y_end, x_start:x_end]

    if ((x_end - x_start)*(y_end - y_start) > NUMBER_MAX_THERMAL_POINTS):
        top_max_indices = (-np.array(thermal_matrix)).argpartition(NUMBER_MAX_THERMAL_POINTS, axis=None)[:NUMBER_MAX_THERMAL_POINTS]
        # measured_temp = np.max(thermal_matrix)
        measured_temp = np.average(thermal_matrix[np.unravel_index(top_max_indices, thermal_matrix.shape)])
    else:
        measured_temp = np.average(thermal_matrix)

    return measured_temp



