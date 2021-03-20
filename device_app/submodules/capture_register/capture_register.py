import numpy as np
import math
import cv2
import collections


class CaptureRegisterFace:
    def __init__ (self,front_pics=2, left_pics=2, right_pics=2, left=-25, right=16, middle_range=35, stack_number=8, frame_distance_capture=3):
        self.left = left
        self.right = right
        self.mid = middle_range
        self.front_pics = front_pics
        self.left_pics = left_pics
        self.right_pics = right_pics
        self.left_stack = 0
        self.right_stack = 0
        self.front_stack = 0
        self.stack_number = stack_number
        self.frame_distance_capture = frame_distance_capture
        self.state = "FRONT"
        self.imgs = []
    
    def update(self, frame, image_points, ori, rects, scale):
        rotation_angle = self.detectHeadpose(frame, image_points)[1]
        # print(rotation_angle)
        if self.state == "FRONT":
            if (rotation_angle <= self.mid/2 and rotation_angle >= - self.mid/2):
                self.front_stack = self.front_stack + 1
            else:
                self.front_stack = 0
            if (self.front_stack > self.stack_number):
                self.imgs.append(self.getFace(ori, rects,scale))
                self.front_stack -= self.frame_distance_capture
            if (len(self.imgs) == self.front_pics):
                self.state = "LEFT"
                print ("***FRONT")
        elif self.state == "LEFT":
            if (rotation_angle < self.left):
                self.left_stack += 1
            else:
                self.left_stack = 0
            if self.left_stack > self.stack_number:
                self.imgs.append(self.getFace(ori, rects,scale))
                self.left_stack -= self.frame_distance_capture
            if (len(self.imgs) == self.front_pics + self.left_pics):
                self.state = "RIGHT"
                print("***LEFT")
        elif self.state == "RIGHT":
            if (rotation_angle > self.right):
                self.right_stack += 1
            else:
                self.right_stack = 0
            if (self.right_stack > self.stack_number):
                self.imgs.append(self.getFace(ori, rects,scale))
                self.right_stack -= self.frame_distance_capture
            if (len(self.imgs) == self.front_pics + self.left_pics + self.right_pics):
                print("***RIGHT")
                return self.imgs
        return None

    def getFace(self, ori, rects, RGB_SCALE):
        savePic = ori[int(rects[0][1]*RGB_SCALE):int(rects[0][3]*RGB_SCALE), int(rects[0][0]*RGB_SCALE):int(rects[0][2]*RGB_SCALE)]
        return savePic

    def detectHeadpose(self, frame, image_points):
        size = frame.shape

        model_points = np.array([
                                    (0.0, 0.0, 0.0),             # Nose tip
                                    (0.0, -330.0, -65.0),        # Chin
                                    (-225.0, 170.0, -135.0),     # Left eye left corner
                                    (225.0, 170.0, -135.0),      # Right eye right corne
                                    (-150.0, -150.0, -125.0),    # Left Mouth corner
                                    (150.0, -150.0, -125.0)      # Right mouth corner
                                
                                ])

        focal_length = size[1]
        center = (size[1]/2, size[0]/2)
        camera_matrix = np.array(
                                [[focal_length, 0, center[0]],
                                [0, focal_length, center[1]],
                                [0, 0, 1]], dtype = "double"
                                )

        dist_coeffs = np.zeros((4,1)) # Assuming no lens distortion
        (success, rotation_vector, translation_vector) = cv2.solvePnP(model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)

        angles = 180*self.yawpitchrolldecomposition(cv2.Rodrigues(rotation_vector)[0])/math.pi
        (nose_end_point2D, jacobian) = cv2.projectPoints(np.array([(0.0, 0.0, 1000.0)]), rotation_vector, translation_vector, camera_matrix, dist_coeffs)

        p1 = ( int(image_points[0][0]), int(image_points[0][1]))
        p2 = ( int(nose_end_point2D[0][0][0]), int(nose_end_point2D[0][0][1]))

        cv2.line(frame, p1, p2, (255,0,0), 2)

        return angles

    def isRotationMatrix(self, R) :
        Rt = np.transpose(R)
        shouldBeIdentity = np.dot(Rt, R)
        I = np.identity(3, dtype = R.dtype)
        n = np.linalg.norm(I - shouldBeIdentity)
        return n < 1e-6

    def yawpitchrolldecomposition(self, R):

        assert(self.isRotationMatrix(R))

        sy = math.sqrt(R[0,0] * R[0,0] +  R[1,0] * R[1,0])
        
        singular = sy < 1e-6
    
        if  not singular :
            x = math.atan2(R[2,1] , R[2,2])
            y = math.atan2(-R[2,0], sy)
            z = math.atan2(R[1,0], R[0,0])
        else :
            x = math.atan2(-R[1,2], R[1,1])
            y = math.atan2(-R[2,0], sy)
            z = 0
    
        return np.array([x, y, z])