# This Python file uses the following encoding: utf-8
import sys
import os
import cv2
import time
import numpy as np
from threading import Thread

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
from device_app_function import DeviceAppFunctions
import qimage2ndarray


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, deviceFuntion):
        super(MainWindow, self).__init__()

        uic.loadUi("./guiModules/form.ui", self)

        self.deviceFuntion = deviceFuntion

        self.timerRGB = QtCore.QTimer()
        self.timerRGB.timeout.connect(self.display_main_frame)
        self.timerRGB.start(0)

        self.timerThermal = QtCore.QTimer()
        self.timerThermal.timeout.connect(self.display_thermal_frame)
        self.timerThermal.start(1000)

    def display_main_frame(self):
        start_a = time.time()
        frame = self.deviceFuntion.process()
        end_a = time.time()
        frame = cv2.resize(frame, (self.label.width(), self.label.height()))
        # frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        image = qimage2ndarray.array2qimage(frame)  #SOLUTION FOR MEMORY LEAK
        end_a = time.time()
        print ('time {:.2f}' .format(end_a - start_a))
        self.label.setPixmap(QtGui.QPixmap.fromImage(image))

    def display_thermal_frame(self):
        frame = self.deviceFuntion.get_thermal_frame()
        frame = cv2.resize(frame, (self.label_2.width(), self.label_2.height()))
        frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        image = qimage2ndarray.array2qimage(frame)  #SOLUTION FOR MEMORY LEAK
        self.label_2.setPixmap(QtGui.QPixmap.fromImage(image))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    deviceFunction = DeviceAppFunctions()
    # print('start')
    window = MainWindow(deviceFunction)
    window.showFullScreen()

    sys.exit(app.exec_())