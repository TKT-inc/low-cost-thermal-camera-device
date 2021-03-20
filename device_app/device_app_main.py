# This Python file uses the following encoding: utf-8
import sys
import cv2
import time
import os
import dbus
from threading import Thread

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
from device_app_function import DeviceAppFunctions
import subprocess

bus = dbus.SessionBus()
proxy = bus.get_object("org.onboard.Onboard", "/org/onboard/Onboard/Keyboard")
keyboard = dbus.Interface(proxy, "org.onboard.Onboard.Keyboard")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, devviceFunction):
        super(MainWindow, self).__init__()

        uic.loadUi("./guiModules/form.ui", self)

        QtWidgets.QApplication.instance().focusChanged.connect(self.handle_focuschanged)

        self.main_display_monitor = self.rgb_frame

        self.deviceFuntion = deviceFunction
        self.shortcut_quit = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+Q'), self)
        self.shortcut_quit.activated.connect(self.closeApp)

        self.timerWorking = QtCore.QTimer()
        self.timerWorking.setTimerType(QtCore.Qt.PreciseTimer)
        self.timerWorking.timeout.connect(self.working)
        self.timerWorking.start(0)

        self.timerRGB = QtCore.QTimer()
        self.timerRGB.setTimerType(QtCore.Qt.PreciseTimer)
        self.timerRGB.timeout.connect(self.display_main_frame)
        self.timerRGB.start(30)

        self.timerThermal = QtCore.QTimer()
        self.timerThermal.setTimerType(QtCore.Qt.PreciseTimer)
        self.timerThermal.timeout.connect(self.display_thermal_frame)
        self.timerThermal.start(1000)

        self.btn_home.clicked.connect(self.Button)
        self.btn_new_user.clicked.connect(self.Button)
        self.btn_info.clicked.connect(self.Button)
        self.register_button.clicked.connect(self.Button)

    def working(self):
        self.deviceFuntion.process()

    def closeApp(self):
        self.deviceFuntion.stop()
        app.quit()

    def display_main_frame(self):
        frame = self.deviceFuntion.get_rgb_frame()
        height, width, _ = frame.shape
        qimg = QtGui.QImage(frame.data, width, height, 3*width, QtGui.QImage.Format_RGB888).rgbSwapped()
        self.main_display_monitor.setPixmap(QtGui.QPixmap(qimg))

    def display_thermal_frame(self):
        frame = self.deviceFuntion.get_thermal_frame()
        height, width, _ = frame.shape
        qimg = QtGui.QImage(frame.data, width, height, 3*width, QtGui.QImage.Format_RGB888).rgbSwapped()
        self.thremal_frame.setPixmap(QtGui.QPixmap(qimg))

    def Button(self):
        # GET BT CLICKED
        btnWidget = self.sender()

        # PAGE HOME
        if btnWidget.objectName() == "btn_home":
            self.deviceFuntion.select_normal_mode()
            self.main_display_monitor = self.rgb_frame
            self.stackedWidget.setCurrentWidget(self.home_page)
            self.resetStyle("btn_home")
            btnWidget.setStyleSheet(self.selectMenu(btnWidget.styleSheet()))

        # PAGE NEW USER
        if btnWidget.objectName() == "btn_new_user" or btnWidget.objectName() == "register_button":
            self.deviceFuntion.select_register_mode()
            self.main_display_monitor = self.register_screen
            self.stackedWidget.setCurrentWidget(self.new_user)
            self.resetStyle("btn_new_user")
            btnWidget.setStyleSheet(self.selectMenu(btnWidget.styleSheet()))

        # PAGE WIDGETS
        if btnWidget.objectName() == "btn_info":
            self.stackedWidget.setCurrentWidget(self.page)
            self.resetStyle("btn_widgets")
            btnWidget.setStyleSheet(self.selectMenu(btnWidget.styleSheet()))

    @QtCore.pyqtSlot("QWidget*", "QWidget*")
    def handle_focuschanged(self, old, now):
        if self.lineEdit == now:
            keyboard.Show()
        elif self.lineEdit == old:
            keyboard.Hide()

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
    