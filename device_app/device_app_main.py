# This Python file uses the following encoding: utf-8
import sys
import cv2
import time
from threading import Thread

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
from device_app_function import DeviceAppFunctions


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, deviceFunction):
        super(MainWindow, self).__init__()
        # start_a = time.time()
        uic.loadUi("./guiModules/form.ui", self)

        self.deviceFuntion = deviceFunction

        self.timerRGB = QtCore.QTimer()
        self.timerRGB.setTimerType(QtCore.Qt.PreciseTimer)
        self.timerRGB.timeout.connect(self.display_main_frame)
        self.timerRGB.start(1)

        self.timerThermal = QtCore.QTimer()
        self.timerThermal.setTimerType(QtCore.Qt.PreciseTimer)
        self.timerThermal.timeout.connect(self.display_thermal_frame)
        self.timerThermal.start(1000)


    def display_main_frame(self):
        start_a = time.time()
        frame = self.deviceFuntion.process()
        end_a = time.time()

        height, width, _ = frame.shape
        qimg = QtGui.QImage(frame.data, width, height, 3*width, QtGui.QImage.Format_RGB888).rgbSwapped()
        print('time: {:.5f} ----- {:.5f}' .format(time.time() - start_a, end_a - start_a))
        
        self.rgb_frame.setPixmap(QtGui.QPixmap(qimg))

    def display_thermal_frame(self):
        frame = self.deviceFuntion.get_thermal_frame()

        frame = cv2.resize(frame, (self.label_2.width(), self.label_2.height()))
        height, width, _ = frame.shape
        qimg = thremal_frame.QImage(frame.data, width, height, 3*width, QtGui.QImage.Format_RGB888).rgbSwapped()
        self.label_2.setPixmap(QtGui.QPixmap(qimg))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    deviceFunction = DeviceAppFunctions()
    window = MainWindow(deviceFunction)

    window.showFullScreen()
    sys.exit(app.exec_())

