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

def measureOffsetTempOfDistance(face_area, coefficient, intercept):
    return (face_area*coefficient + intercept)

def measureTemperature(color,temp, objects, object_measurement, H_matrix, offset_temp, number_max, coefficient, intercept, scale):
    H = H_matrix
    for (objectID, obj) in objects.items():
        try:
            coordinates = object_measurement[objectID].coor
            thermal_start_x, thermal_start_y = convertRGBToThermalCoor(coordinates[0], coordinates[1], H)
            thermal_end_x, thermal_end_y = convertRGBToThermalCoor(coordinates[2], coordinates[3], H)
            
            cv2.rectangle(color, (thermal_start_x, thermal_start_y), (thermal_end_x, thermal_end_y), (0, 0, 0), 4)
            x_start = int(thermal_start_x/8)
            x_end = int(thermal_end_x/8)
            y_start = int(thermal_start_y/8)
            y_end = int(thermal_end_y/8)

            if (x_start == x_end):
                x_end += 1
            if (y_start == y_end):
                y_end += 1

            thermal_matrix = temp[y_start:y_end, x_start:x_end]
            # print(thermal_matrix)
            # print((x_end - x_start)*(y_end - y_start))
            if ((x_end - x_start)*(y_end - y_start) > number_max):
                top_max_indices = (-np.array(thermal_matrix)).argpartition(number_max, axis=None)[:number_max]
                # measured_temp = np.max(thermal_matrix)
                measured_temp = np.average(thermal_matrix[np.unravel_index(top_max_indices, thermal_matrix.shape)])
            else:
                measured_temp = np.average(thermal_matrix)
            
            face_area = (coordinates[2]-coordinates[0])*(coordinates[3]-coordinates[1])*(scale*2)
            offset_temp += measureOffsetTempOfDistance(face_area, coefficient, intercept)

            # print(thermal_matrix[np.unravel_index(top_max_indices, thermal_matrix.shape)])
            temperature = (measured_temp/100.0) - 273.15 + offset_temp
            objects[objectID].updateTemperature(temperature)
        except Exception as identifier:
            print(identifier)
            pass
    return

