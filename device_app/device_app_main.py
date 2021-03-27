# This Python file uses the following encoding: utf-8
import sys
import cv2
import time
import dbus
from threading import Thread

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
from datetime import datetime
from device_app_function import DeviceAppFunctions
from guiModules.ui_components import *

bus = dbus.SessionBus()
proxy = bus.get_object("org.onboard.Onboard", "/org/onboard/Onboard/Keyboard")
keyboard = dbus.Interface(proxy, "org.onboard.Onboard.Keyboard")

FONT_OF_TABLE = QtGui.QFont()
FONT_OF_TABLE.setPointSize(16)
FONT_OF_TABLE.setBold(True)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.deviceFuntion = DeviceAppFunctions()
        self.startMainWindow()
        # self.startLoginWindow()

        # QtWidgets.QApplication.instance().focusChanged.connect(self.handle_focuschanged)
        
        self.shortcut_quit = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+Q'), self)
        self.shortcut_quit.activated.connect(self.closeApp)

        # self.a = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+A'), self)
        # self.a.activated.connect(lambda: self.startMainWindow())

    """
    Controle windows
    """
    def startMainWindow(self):
        uic.loadUi("./device_app/guiModules/mainWindow.ui", self)

        self.main_display_monitor = self.rgb_frame        

        self.history_record.setColumnWidth(0, 130)
        self.history_record.setColumnWidth(1, 175)
        self.history_record.setColumnWidth(2, 75)

        self.notifications.setColumnWidth(0, 130)

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
        self.timerRGB.timeout.connect(self.displayMainFrame)
        self.timerRGB.start(20)

        self.timerThermal = QtCore.QTimer()
        self.timerThermal.setTimerType(QtCore.Qt.PreciseTimer)
        self.timerThermal.timeout.connect(self.displayThermalFrame)
        self.timerThermal.start(1000)

        self.btn_home.clicked.connect(self.Button)
        self.btn_new_user.clicked.connect(self.Button)
        self.btn_info.clicked.connect(self.Button)
        self.register_button.clicked.connect(self.Button)
        self.btn_calib.clicked.connect(self.Button)

    def startLoginWindow(self):

        uic.loadUi("./device_app/guiModules/loginWindow.ui", self)

    """
    Main processing of the application
    """
    #PROCESSING OF THE MAIN SYSTEM
    def working(self):
        status = self.deviceFuntion.process()
        if (status == "REGISTER_SUCCESS"):
            self.finishedFaceRegistrationStyle(self.face_right)
            self.createInputNameDialog()
        elif (status == "REGISTER_DONE_LEFT"):
            self.finishedFaceRegistrationStyle(self.face_left)
        elif (status == "REGISTER_DONE_FRONT"):
            self.finishedFaceRegistrationStyle(self.face_front)
        elif (status == "CALIBRATE_TOO_MUCH_PEOPLE"):
            print('one person please')
        elif (status == "CALIBRATE_SUCCESS"):
            self.createInputGroundTruthTemp()

    #Handle status of working process
    def handleRecordsAndNotis(self):
        records = self.deviceFuntion.getRecordsInfo()
        for (objectID, obj) in records.items():
            current_time = datetime.now().strftime("%d-%m|%H:%M:%S")
            self.addRecords(current_time, str(objectID) + '-' + obj.name, obj.record_temperature)
            if (obj.have_mask is False):
                self.addNoti(current_time, obj.name)
            if (obj.gotFever() is True):
                self.addNoti(current_time, obj.name, obj.record_temperature)


    #Close the application
    def closeApp(self):
        self.deviceFuntion.stop()
        app.quit()

    #Display main frame into rgb frame in homepage and register page
    def displayMainFrame(self):
        frame = self.deviceFuntion.getRgbFrame()
        frame = cv2.resize(frame, (self.main_display_monitor.width(),self.main_display_monitor.height()))
        height, width, _ = frame.shape
        qimg = QtGui.QImage(frame.data, width, height, 3*width, QtGui.QImage.Format_RGB888).rgbSwapped()
        self.main_display_monitor.setPixmap(QtGui.QPixmap(qimg))

    #Display thermal frame in homepage
    def displayThermalFrame(self):
        frame = self.deviceFuntion.getThermalFrame()
        frame = cv2.resize(frame, (self.thremal_frame.width(),self.thremal_frame.height()))
        height, width, _ = frame.shape
        qimg = QtGui.QImage(frame.data, width, height, 3*width, QtGui.QImage.Format_RGB888).rgbSwapped()
        self.thremal_frame.setPixmap(QtGui.QPixmap(qimg))

    #Create an input dialog to input person's info when finish face register
    def createInputNameDialog(self):
        keyboard.Show()
        self.dlg = InputNameDlg(self)
        self.dlg.accepted.connect(self.acceptInputRegisterName)
        self.dlg.rejected.connect(self.cancelInputRegisterName)
        self.dlg.exec()

    # Create an input dialog to input the ground truth temperature
    def createInputGroundTruthTemp(self):
        keyboard.Show()
        self.dlg = InputTempDlg(self)
        self.dlg.accepted.connect(self.acceptInputTempCalibrate)
        self.dlg.rejected.connect(self.cancelInputTempCalibrate)
        self.dlg.exec()
    
    # Change color of the face register state
    def finishedFaceRegistrationStyle(self, label_of_face):
        label_of_face.setStyleSheet(label_of_face.styleSheet() + ("background-color: rgb(147, 255, 165);"))

    #switch to normal mode (working mode)
    def selectNormalMode(self):       
        self.main_display_monitor = self.rgb_frame
        self.stackedWidget.setCurrentWidget(self.home_page)
        self.resetStyleBtn("btn_home")
        self.btn_home.setStyleSheet(self.selectMenu(self.btn_home.styleSheet()))
        if (self.deviceFuntion.getMode() != 'NORMAL'):
            self.deviceFuntion.selectNormalMode() 

    # Switch to register mode
    def selectRegisterMode(self):
        self.main_display_monitor = self.register_screen
        self.face_left.setStyleSheet(self.face_left.styleSheet().replace("background-color: rgb(147, 255, 165);", ""))
        self.face_right.setStyleSheet(self.face_right.styleSheet().replace("background-color: rgb(147, 255, 165);", ""))
        self.face_front.setStyleSheet(self.face_front.styleSheet().replace("background-color: rgb(147, 255, 165);", ""))
        self.stackedWidget.setCurrentWidget(self.new_user)
        self.resetStyleBtn("btn_new_user")
        self.btn_new_user.setStyleSheet(self.selectMenu(self.btn_new_user.styleSheet()))
        if (self.deviceFuntion.getMode() != 'REGISTER'):
            self.deviceFuntion.selectRegisterMode() 

    def selectCalibrateMode(self):
        self.main_display_monitor = self.calibrate_screen
        self.deviceFuntion.selectCalibrateMode()
        self.stackedWidget.setCurrentWidget(self.calibrate)
        self.resetStyleBtn("btn_calib")
        self.btn_calib.setStyleSheet(self.selectMenu(self.btn_new_user.styleSheet()))
        if (self.deviceFuntion.getMode() != 'CALIBRATE'):
            self.deviceFuntion.selectRegisterMode() 

        
    # Add notification when someone got fever or does not wear mask
    def addNoti(self, current_time, name, temp=None):
        vbar = self.notifications.verticalScrollBar()
        _scroll = vbar.value() == vbar.maximum()
        self.notifications.insertRow(self.notifications.rowCount())

        self.notifications.setItem(self.notifications.rowCount()-1, 0, QtWidgets.QTableWidgetItem(current_time))
        self.notifications.item(self.notifications.rowCount()-1, 0).setFont(FONT_OF_TABLE)

        if (temp is not None):
            noti = name + " got sick with " + "{:.2f}".format(temp) + " oC"
        else:
            noti = name + " plase wear MASK!"

        self.notifications.setItem(self.notifications.rowCount()-1, 1, QtWidgets.QTableWidgetItem(noti))
        self.notifications.item(self.notifications.rowCount()-1, 1).setFont(FONT_OF_TABLE)

        if(_scroll):
            self.notifications.scrollToBottom()

    # Add record info into the history record table
    def addRecords(self, current_time, name, temperature):
        vbar = self.history_record.verticalScrollBar()
        _scroll = vbar.value() == vbar.maximum()
        
        self.history_record.insertRow(self.history_record.rowCount())

        self.history_record.setItem(self.history_record.rowCount()-1, 0, QtWidgets.QTableWidgetItem(current_time))
        self.history_record.item(self.history_record.rowCount()-1, 0).setFont(FONT_OF_TABLE)
        self.history_record.setItem(self.history_record.rowCount()-1, 1, QtWidgets.QTableWidgetItem(name))
        self.history_record.item(self.history_record.rowCount()-1, 1).setFont(FONT_OF_TABLE)
        temperature = "{:.2f}".format(temperature) + " oC"
        self.history_record.setItem(self.history_record.rowCount()-1, 2, QtWidgets.QTableWidgetItem(temperature))
        self.history_record.item(self.history_record.rowCount()-1, 2).setFont(FONT_OF_TABLE)

        if(_scroll):
            self.history_record.scrollToBottom()



    """
    Handle inputs and signals of the application
    """
    
    #Ok button when input register name
    def acceptInputRegisterName(self):
        keyboard.Hide()
        self.selectNormalMode()
        self.deviceFuntion.sendRegisteredInfoToServer(self.dlg.name_edit.text())

    #Cancel button when input register name
    def cancelInputRegisterName(self):
        keyboard.Hide()
        self.selectRegisterMode()

    def acceptInputTempCalibrate(self):
        keyboard.Hide()
        self.selectNormalMode()
        status, temp = self.deviceFuntion.createUserTemperatureOffset(self.dlg.temperature_edit.text())
    
    def cancelInputTempCalibrate(self):
        keyboard.Hide()
        self.selectCalibrateMode()

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
            self.stackedWidget.setCurrentWidget(self.product_info)
            self.resetStyleBtn("btn_info")
            btnWidget.setStyleSheet(self.selectMenu(btnWidget.styleSheet()))

        if btnWidget.objectName() == "btn_calib":
            self.selectCalibrateMode()



    # @QtCore.pyqtSlot("QWidget*", "QWidget*")
    # def handle_focuschanged(self, old, now):
    #     time.sleep(1)
        # if now.objectName() == "name_edit":
        #     keyboard.Show()
        # elif self.lineEdit == old:
        #     keyboard.Hide()

    ## ==> SELECT
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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('TKT')

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())
    