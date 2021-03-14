# This Python file uses the following encoding: utf-8
import sys
import os
import cv2
import numpy as np
from threading import Thread

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtUiTools import *
from PySide2.QtGui import QPixmap
from ui_form import Ui_mainUi
from device_app_function import DeviceAppFunctions
import qimage2ndarray


class MainWindow(QMainWindow):
    def __init__(self, deviceFuntion):
        super(MainWindow, self).__init__()
        self.ui = Ui_mainUi()
        self.ui.setupUi(self)

        self.deviceFuntion = deviceFuntion

        self.timerRGB = QTimer()
        self.timerRGB.timeout.connect(self.display_main_frame)
        self.timerRGB.start(30)

        self.timerThermal = QTimer()
        self.timerThermal.timeout.connect(self.timerThermal)
        self.timerThermal.start(1000)
        # self.ui.pushButton_2.clicked.connect(self.full())

    def display_main_frame(self):
        frame = self.deviceFuntion.get_main_frame()
        frame = cv2.resize(frame, (self.ui.label.width(), self.ui.label.height()))
        frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        frame = cv2.flip(frame, 1)
        image = qimage2ndarray.array2qimage(frame)  #SOLUTION FOR MEMORY LEAK
        self.ui.label.setPixmap(QPixmap.fromImage(image))

    def display_thermal_frame(self):
        frame = self.deviceFuntion.get_thermal_frame()
        frame = cv2.resize(frame, (self.ui.label_2.width(), self.ui.label_2.height()))
        frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        frame = cv2.flip(frame, 1)
        image = qimage2ndarray.array2qimage(frame)  #SOLUTION FOR MEMORY LEAK
        self.ui.label_2.setPixmap(QPixmap.fromImage(image))


if __name__ == "__main__":
    app = QApplication(sys.argv)

    deviceFunction = DeviceAppFunctions()
    window = MainWindow(deviceFunction)
    window.showFullScreen()

    sys.exit(app.exec_())