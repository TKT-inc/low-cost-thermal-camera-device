import numpy as np
import cv2

def convertRGBToThermalCoor(x, y, H_raw):
    MAX_WIDTH = 640
    MAX_HEIGHT = 480
    H = np.linalg.inv(H_raw)
    convert_x = int((H[0][0] * x + H[0][1] * y + H[0][2]) / (H[2][0] * x + H[2][1] * y + H[2][2]))
    convert_y = int((H[1][0] * x + H[1][1] * y + H[1][2]) / (H[2][0] * x + H[2][1] * y + H[2][2]))
    if(convert_x > MAX_WIDTH):
        convert_x = MAX_WIDTH - 1
    if(convert_y > MAX_HEIGHT):
        convert_y = MAX_HEIGHT - 1
    return convert_x, convert_y 

def measureTemperature(frame,color,temp, objects,objectID, coordinates):
    H = [[ 9.65618052e-01,  1.64519945e-02, -2.23755740e+01],
    [-1.42094632e-02,  1.26760427e+00, -2.37487801e+01],
    [ 7.58731430e-05, -3.62088057e-05,  1.00000000e+00]]
    thermal_start_x, thermal_start_y = convertRGBToThermalCoor(coordinates[0], coordinates[1], H)
    thermal_end_x, thermal_end_y = convertRGBToThermalCoor(coordinates[2], coordinates[3], H)
    cv2.rectangle(color, (int(thermal_start_x), int(thermal_start_y)), (int(thermal_end_x), int(thermal_end_y)), (0, 0, 255), 2)
    max_temp = np.max(temp[int(thermal_start_y/8):int(thermal_end_y/8), int(thermal_start_x/8):int(thermal_end_x/8)], initial=15394)
    temperature = "{:.2f}".format(max_temp*36.5/30788) + " oC"
    objects[objectID].temperature = temperature
    return temperature