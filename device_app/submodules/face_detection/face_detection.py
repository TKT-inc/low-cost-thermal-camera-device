import cv2
import numpy as np

CAFFEMODEL = "/models/res10_300x300_ssd_iter_140000.caffemodel"
PROTOTEXTPATH = "/models/deploy.prototxt.txt"

class FaceDetection:
    def __init__(self, model = CAFFEMODEL, proto = PROTOTEXTPATH):
        self.rects = []
        self.net = cv2.dnn.readNetFromCaffe(proto, model)
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
    def detectFaces(self, frame):
        (h, w) = frame.shape[:2]
        # blobImage convert RGB (104.0, 177.0, 123.0)
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0,
                                    (300, 300), (104.0, 177.0, 123.0))
        # passing blob through the network to detect and pridiction
        self.net.setInput(blob) 
        detections = self.net.forward()
        # loop over the detections
        self.rects = []
        for i in range(0, detections.shape[2]):
            # extract the confidence and prediction
            confidence = detections[0, 0, i, 2]
            # filter detections by confidence greater than the minimum confidence
            if confidence < 0.8 :
                continue
            # Determine the (x, y)-coordinates of the bounding box for the

            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")
            self.rects.append((startX, startY, endX, endY))
            cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 0, 255), 2)
        return self.rects
