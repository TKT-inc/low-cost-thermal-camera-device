# This Python file uses the following encoding: utf-8
import sys
import cv2
import time
import os
import dbus
from threading import Thread

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
from datetime import datetime
from device_app_function import DeviceAppFunctions

bus = dbus.SessionBus()
proxy = bus.get_object("org.onboard.Onboard", "/org/onboard/Onboard/Keyboard")
keyboard = dbus.Interface(proxy, "org.onboard.Onboard.Keyboard")

FONT_OF_TABLE = QtGui.QFont()
FONT_OF_TABLE.setPointSize(16)
FONT_OF_TABLE.setBold(True)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, devviceFunction):
        super(MainWindow, self).__init__()

        uic.loadUi("./guiModules/form.ui", self)

        # QtWidgets.QApplication.instance().focusChanged.connect(self.handle_focuschanged)

        self.main_display_monitor = self.rgb_frame

        self.deviceFuntion = deviceFunction
        self.shortcut_quit = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+Q'), self)
        self.shortcut_quit.activated.connect(self.closeApp)

        self.history_record.setColumnWidth(0, 130)
        self.history_record.setColumnWidth(1, 175)
        self.history_record.setColumnWidth(2, 75)
        # self.history_record.verticalHeader().setDefaultSectionSize(10)

        self.timerWorking = QtCore.QTimer()
        self.timerWorking.setTimerType(QtCore.Qt.PreciseTimer)
        self.timerWorking.timeout.connect(self.working)
        self.timerWorking.start(0)

        self.timeHandleStatus = QtCore.QTimer()
        self.timeHandleStatus.setTimerType(QtCore.Qt.PreciseTimer)
        self.timeHandleStatus.timeout.connect(self.handleRecordsAndNotis)
        self.timeHandleStatus.start(20)

        self.timerRGB = QtCore.QTimer()
        self.timerRGB.setTimerType(QtCore.Qt.PreciseTimer)
        self.timerRGB.timeout.connect(self.display_main_frame)
        self.timerRGB.start(20)

        self.timerThermal = QtCore.QTimer()
        self.timerThermal.setTimerType(QtCore.Qt.PreciseTimer)
        self.timerThermal.timeout.connect(self.display_thermal_frame)
        self.timerThermal.start(1000)

        self.btn_home.clicked.connect(self.Button)
        self.btn_new_user.clicked.connect(self.Button)
        self.btn_info.clicked.connect(self.Button)
        self.register_button.clicked.connect(self.Button)

    """
    Main processing of the application
    """

    #PROCESSING OF THE MAIN SYSTEM
    def working(self):
        status = self.deviceFuntion.process()
        if (status == "REGISTER_SUCCESS"):
            self.finishedFaceRegistrationStyle(self.face_right)
            self.create_input_name_dialog()
        elif (status == "REGISTER_DONE_LEFT"):
            self.finishedFaceRegistrationStyle(self.face_left)
        elif (status == "REGISTER_DONE_FRONT"):
            self.finishedFaceRegistrationStyle(self.face_front)

    #Handle status of working process
    def handleRecordsAndNotis(self):
        records = self.deviceFuntion.get_records()
        for (objectID, obj) in records.items():
            self.addRecords(str(objectID) + '-' + obj.name, obj.temperature)
            if (~obj.have_mask):
                self.addNotiNoMask(obj.name)


    #Close the application
    def closeApp(self):
        self.deviceFuntion.stop()
        app.quit()

    #Display main frame into rgb frame in homepage and register page
    def display_main_frame(self):
        frame = self.deviceFuntion.get_rgb_frame()
        height, width, _ = frame.shape
        qimg = QtGui.QImage(frame.data, width, height, 3*width, QtGui.QImage.Format_RGB888).rgbSwapped()
        self.main_display_monitor.setPixmap(QtGui.QPixmap(qimg))

    #Display thermal frame in homepage
    def display_thermal_frame(self):
        frame = self.deviceFuntion.get_thermal_frame()
        frame = cv2.resize(frame, (self.thremal_frame.width(),self.thremal_frame.height()))
        height, width, _ = frame.shape
        qimg = QtGui.QImage(frame.data, width, height, 3*width, QtGui.QImage.Format_RGB888).rgbSwapped()
        self.thremal_frame.setPixmap(QtGui.QPixmap(qimg))

    #Create an input dialog to input person's info when finish face register
    def create_input_name_dialog(self):
        keyboard.Show()
        self.dlg = InputDlg(self)
        self.dlg.accepted.connect(self.accept_input_register_name)
        self.dlg.rejected.connect(self.cancel_input_register_name)
        self.dlg.exec()
    
    def accept_input_register_name(self):
        keyboard.Hide()
        self.deviceFuntion.send_registered_info_to_server(self.dlg.name_edit.text())
        self.selectNormalMode()

    def cancel_input_register_name(self):
        keyboard.Hide()
        self.selectRegisterMode()

    def finishedFaceRegistrationStyle(self, label_of_face):
        label_of_face.setStyleSheet(label_of_face.styleSheet() + ("background-color: rgb(147, 255, 165);"))

    def selectNormalMode(self):
        self.deviceFuntion.select_normal_mode()
        self.main_display_monitor = self.rgb_frame
        self.stackedWidget.setCurrentWidget(self.home_page)
        self.resetStyleBtn("btn_home")
        self.btn_home.setStyleSheet(self.selectMenu(self.btn_home.styleSheet()))

    def selectRegisterMode(self):
        self.deviceFuntion.select_register_mode()
        self.main_display_monitor = self.register_screen
        self.face_left.setStyleSheet(self.face_left.styleSheet().replace("background-color: rgb(147, 255, 165);", ""))
        self.face_right.setStyleSheet(self.face_right.styleSheet().replace("background-color: rgb(147, 255, 165);", ""))
        self.face_front.setStyleSheet(self.face_front.styleSheet().replace("background-color: rgb(147, 255, 165);", ""))
        self.stackedWidget.setCurrentWidget(self.new_user)
        self.resetStyleBtn("btn_new_user")
        self.btn_new_user.setStyleSheet(self.selectMenu(self.btn_new_user.styleSheet()))


    """
    Handle inputs and signals of the application
    """
    def addNotiNoMask(self, name):
        self.notifications.insertRow(self.notifications.rowCount())
        noti = name + " does not have MASK!"
        self.notifications.setItem(self.notifications.rowCount()-1, 0, QtWidgets.QTableWidgetItem(noti))

    def addNotiFever(self, name, temp):
        self.notifications.insertRow(self.notifications.rowCount())
        noti = name + " got sick with " + temp
        self.notifications.setItem(self.notifications.rowCount()-1, 0, QtWidgets.QTableWidgetItem(noti))

    def addRecords(self, name, temperature):
        vbar = self.history_record.verticalScrollBar()
        _scroll = vbar.value() == vbar.maximum()
        now = datetime.now()
        
        current_time = now.strftime("%d-%m|%H:%M:%S")
        self.history_record.insertRow(self.history_record.rowCount())

        self.history_record.setItem(self.history_record.rowCount()-1, 0, QtWidgets.QTableWidgetItem(current_time))
        self.history_record.item(self.history_record.rowCount()-1, 0).setFont(FONT_OF_TABLE)
        self.history_record.setItem(self.history_record.rowCount()-1, 1, QtWidgets.QTableWidgetItem(name))
        self.history_record.item(self.history_record.rowCount()-1, 1).setFont(FONT_OF_TABLE)
        self.history_record.setItem(self.history_record.rowCount()-1, 2, QtWidgets.QTableWidgetItem(temperature))
        self.history_record.item(self.history_record.rowCount()-1, 2).setFont(FONT_OF_TABLE)

        if(_scroll):
            self.history_record.scrollToBottom()

    #Handle all button of the application
    def Button(self):
        # GET BT CLICKED
        btnWidget = self.sender()

        # PAGE HOME
        if btnWidget.objectName() == "btn_home":
            self.selectNormalMode()

        # PAGE NEW USER
        if btnWidget.objectName() == "btn_new_user" or btnWidget.objectName() == "register_button":
            self.selectRegisterMode()

        # PAGE INFO
        if btnWidget.objectName() == "btn_info":
            self.stackedWidget.setCurrentWidget(self.page)
            self.resetStyleBtn("btn_widgets")
            btnWidget.setStyleSheet(self.selectMenu(btnWidget.styleSheet()))


    @QtCore.pyqtSlot("QWidget*", "QWidget*")
    def handle_focuschanged(self, old, now):
        if now.objectName() == "name_edit":
            keyboard.Show()
        # elif self.lineEdit == old:
        #     keyboard.Hide()

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
    def resetStyleBtn(self, widget):
        for w in self.menu.findChildren(QtWidgets.QPushButton):
            if w.objectName() != widget:
                w.setStyleSheet(self.deselectMenu(w.styleSheet()))


class InputDlg(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("./guiModules/dialog.ui", self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('TKT')

    deviceFunction = DeviceAppFunctions()
    window = MainWindow(deviceFunction)
    window.show()
    
    sys.exit(app.exec_())
    