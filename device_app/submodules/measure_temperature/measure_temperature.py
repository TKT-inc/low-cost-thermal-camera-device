import numpy as np
import cv2
import time
import math
import yaml
import base64
import csv
with open("configuration.yaml") as ymlfile:
    cfg = yaml.safe_load(ymlfile)


"""
Prams for transform from RGB coors into Thermal coors
"""
# Homography
TRANSFORM_MATRIX = cfg['transMatrix']

# PnP
PNP_ROTATION_VEC = cfg['transMatrixPnP']['rotationVector']
PNP_TRANSLATION_VEC = cfg['transMatrixPnP']['translationVector']
PNP_THERMAL_CAM_MATRIX = cfg['transMatrixPnP']['thermalCameraMatrix']
PNP_DIST_COEFF = cfg['transMatrixPnP']['distortionCoefficients']

"""
setup offset temperature
"""
NUMBER_MAX_THERMAL_POINTS = cfg['measureTemperature']['numberMaxThermalPoints']
OFFSET_TEMPERATURE_DIST_COEF = cfg['measureTemperature']['offsetDistCoeffecient']
OFFSET_TEMPERATURE_DIST_INT = cfg['measureTemperature']['offsetDistIntercept']
PERCENTAGE_THERMAL_POINTS = cfg['measureTemperature']['percentageThermalPoints']
TEMPERATURE_MEASURE_METHOD = cfg['measureTemperature']['temperatureMeasureMethod']
TEMPERATURE_STANDARD_DEVIATION_THRESHOLD = cfg['measureTemperature']['temperatureStandardDeviationThreshold']

"""
get thermal camera size
"""
THERMAL_CAM_SCALED_WIDTH = cfg['camera']['thermal']['scaleWidth']
THERMAL_CAM_SCALED_HEIGHT = cfg['camera']['thermal']['scaleHeight']
THERMAL_CAM_WIDTH = cfg['camera']['thermal']['originalWidth']
THERMAL_CAM_HEIGHT = cfg['camera']['thermal']['originalHeight']


def measureTemperature(color,temp, objects, object_measurement, user_offset, scale, csvActivate=False):
    # with open('./device_app/submodules/measure_temperature/temp.csv', 'a') as f_object:
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
            # raw = measured_temp/100.0 - 273.15
            # if (csvActivate):
            #     writer_object = csv.writer(f_object)
            #     writer_object.writerow([face_area, raw])
            # f_object.close()
            # print(f'Log: {measureOffsetTempOfDistance(face_area)}')
            # print(f'Area: {str(face_area)}')
            # print(f'Temp: {str((measured_temp/100.0) - 273.15)}')
            objects[objectID].updateTemperature(temperature)
        except Exception as identifier:
            print('Cant measure the temperature')
            print(identifier)


def convertRGBToThermalCoor(x, y):
    start = time.time()
#     # Homography 
#     # H = np.linalg.inv(H_raw)
#     # convert_x = int((H[0][0] * x + H[0][1] * y + H[0][2]) / (H[2][0] * x + H[2][1] * y + H[2][2]))
#     # convert_y = int((H[1][0] * x + H[1][1] * y + H[1][2]) / (H[2][0] * x + H[2][1] * y + H[2][2]))
#     # Affine convert
#     H = H_raw 
#     convert_x = int(H[0][0] * x + H[0][1] * y + H[0][2])
#     convert_y = int(H[1][0] * x + H[1][1] * y + H[1][2])
#     # 3D convert
    rvecs = np.asmatrix(np.asarray(PNP_ROTATION_VEC), dtype=np.float32)
    tvecs = np.asmatrix(np.asarray(PNP_TRANSLATION_VEC), dtype=np.float32)
    mtx = np.asmatrix(np.asarray(PNP_THERMAL_CAM_MATRIX), dtype=np.float32)
    dist = np.asmatrix(np.asarray(PNP_DIST_COEFF), dtype=np.float32)
    coors= [[[x, y, 1]]]
    threed_point = np.asarray(coors, dtype=np.float32)
    imgpoints2, _ = cv2.projectPoints(threed_point, rvecs, tvecs, mtx, dist)
    convert_x = imgpoints2[0][0][0]
    convert_y = imgpoints2[0][0][1]

    def handleMaxMinSize(value, MAX, MIN = 0):
        if (value >= MAX):
            return MAX - 1
        elif (value < MIN):
            return MIN
        return value
    
    convert_x = handleMaxMinSize(convert_x, THERMAL_CAM_SCALED_WIDTH)
    convert_y = handleMaxMinSize(convert_y, THERMAL_CAM_SCALED_HEIGHT)

    return convert_x, convert_y  

def measureOffsetTempOfDistance(face_area):
    return (math.log(face_area)*OFFSET_TEMPERATURE_DIST_COEF + OFFSET_TEMPERATURE_DIST_INT)

def measureTemperatureFromCoor(temp_img, coor_start, coor_end):
    x_start = int(coor_start[0]/8)
    x_end = int(coor_end[0]/8)
    y_start = int(coor_start[1]/8)
    y_end = int(coor_end[1]/8)

    def translateCoorToThermal(start, end, MAX):
        if (start == end):
            if (end + 1 < MAX):
                return start, (end + 1)
            else: 
                return (start - 1), end
        return start, end

    x_start, x_end = translateCoorToThermal(x_start, x_end, THERMAL_CAM_WIDTH)
    y_start, y_end = translateCoorToThermal(y_start, y_end, THERMAL_CAM_HEIGHT)

    thermal_matrix = temp_img[y_start:y_end, x_start:x_end]

    def calculateLocalPixels():
        def calculateAverageTemp(y, x):
            selected_range = thermal_matrix[max(y - 1, 0) : min(y + 2, y_end-y_start + 1), max(x - 1, 0) : min(x + 2, x_end - x_start + 1)]
            # thermal_reshape = thermal_matrix.reshape((thermal_matrix.shape[0], thermal_matrix.shape[1]))
            # np.savetxt('thermal_matrix.csv', thermal_reshape, delimiter=',')
            # print(f'Mat: {selected_range}')
            average_temp = np.average(selected_range)
            standard_dev = np.std(selected_range)
            return average_temp, standard_dev

        if ((x_end - x_start)*(y_end - y_start) > NUMBER_MAX_THERMAL_POINTS):
            average_temp_arr = []
            top_max_indices = (-np.array(thermal_matrix)).argpartition(NUMBER_MAX_THERMAL_POINTS, axis=None)[:NUMBER_MAX_THERMAL_POINTS]
            for i in range(NUMBER_MAX_THERMAL_POINTS):
                idx = np.unravel_index(top_max_indices[i], thermal_matrix.shape)
                # print(f'index: {idx}')
                average_temp, standard_dev = calculateAverageTemp(idx[0], idx[1])
                print(f'kth-largest: {idx} STD: {standard_dev}')
                average_temp_arr.append(average_temp)
            return max(average_temp_arr)
        return np.amax(thermal_matrix)

    def calculatePercentagePoints():
        num_of_points = math.ceil(PERCENTAGE_THERMAL_POINTS * (x_end - x_start) * (y_end - y_start))
        print(f'Point: {num_of_points}')
        if (num_of_points > 1):
            top_max_indices = (-np.array(thermal_matrix)).argpartition(num_of_points, axis=None)[:num_of_points]
            return np.average(thermal_matrix[np.unravel_index(top_max_indices, thermal_matrix.shape)])
        return np.amax(thermal_matrix)

    if TEMPERATURE_MEASURE_METHOD == 1 :
        return calculateLocalPixels()
    elif TEMPERATURE_MEASURE_METHOD == 2:
        return calculatePercentagePoints()
