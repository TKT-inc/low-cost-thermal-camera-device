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
        self.shortcut_quit = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+Q'), self)
        self.shortcut_quit.activated.connect(self.closeApp)

        self.timerRGB = QtCore.QTimer()
        self.timerRGB.setTimerType(QtCore.Qt.PreciseTimer)
        self.timerRGB.timeout.connect(self.display_main_frame)
        self.timerRGB.start(1)

        self.timerThermal = QtCore.QTimer()
        self.timerThermal.setTimerType(QtCore.Qt.PreciseTimer)
        self.timerThermal.timeout.connect(self.display_thermal_frame)
        self.timerThermal.start(1000)

        self.btn_home.clicked.connect(self.Button)
        self.btn_new_user.clicked.connect(self.Button)
        self.btn_info.clicked.connect(self.Button)
        self.register_button.clicked.connect(self.Button)

    def closeApp(self):
        self.deviceFuntion.stop()
        app.quit()

    def display_main_frame(self):
        # start_a = time.time()
        frame = self.deviceFuntion.process()
        # end_a = time.time()

        height, width, _ = frame.shape
        qimg = QtGui.QImage(frame.data, width, height, 3*width, QtGui.QImage.Format_RGB888).rgbSwapped()
        # print('time: {:.5f} ----- {:.5f}' .format(time.time() - start_a, end_a - start_a))
        
        self.rgb_frame.setPixmap(QtGui.QPixmap(qimg))

    def display_thermal_frame(self):
        frame = self.deviceFuntion.get_thermal_frame()

        frame = cv2.resize(frame, (self.thremal_frame.width(), self.thremal_frame.height()))
        height, width, _ = frame.shape
        # print(frame)
        qimg = QtGui.QImage(frame.data, width, height, 3*width, QtGui.QImage.Format_RGB888).rgbSwapped()
        self.thremal_frame.setPixmap(QtGui.QPixmap(qimg))

    def Button(self):
        # GET BT CLICKED
        btnWidget = self.sender()

        # PAGE HOME
        if btnWidget.objectName() == "btn_home":
            self.stackedWidget.setCurrentWidget(self.home_page)
            self.resetStyle("btn_home")
            btnWidget.setStyleSheet(self.selectMenu(btnWidget.styleSheet()))

        # PAGE NEW USER
        if btnWidget.objectName() == "btn_new_user":
            self.stackedWidget.setCurrentWidget(self.new_user)
            self.resetStyle("btn_new_user")
            btnWidget.setStyleSheet(self.selectMenu(btnWidget.styleSheet()))

        # PAGE WIDGETS
        if btnWidget.objectName() == "btn_info" or btnWidget.objectName == "register_button":
            self.stackedWidget.setCurrentWidget(self.page)
            self.resetStyle("btn_widgets")
            btnWidget.setStyleSheet(self.selectMenu(btnWidget.styleSheet()))

    def selectMenu(self, getStyle):
        select = getStyle + ("QPushButton { border-right: 8px solid rgb(44, 49, 60); }")
        return select

    ## ==> DESELECT
    def deselectMenu(self, getStyle):
        deselect = getStyle.replace("QPushButton { border-right: 8px solid rgb(44, 49, 60); }", "")
        return deselect

    ## ==> START SELECTION
    def selectStandardMenu(self, widget):
        for w in self.ui.menu.findChildren(QtWidgets.QPushButton):
            if w.objectName() == widget:
                w.setStyleSheet(self.selectMenu(w.styleSheet()))

    ## ==> RESET SELECTION
    def resetStyle(self, widget):
        for w in self.menu.findChildren(QtWidgets.QPushButton):
            if w.objectName() != widget:
                w.setStyleSheet(self.deselectMenu(w.styleSheet()))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    deviceFunction = DeviceAppFunctions()
    window = MainWindow(deviceFunction)

    window.showFullScreen()
    print('end')
    del deviceFunction
    sys.exit(app.exec_())
    