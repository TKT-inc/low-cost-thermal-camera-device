# This Python file uses the following encoding: utf-8
import sys
import cv2
import time
import dbus
import yaml
import os
from dbus.mainloop.glib import DBusGMainLoop
import NetworkManager

path = os.path.dirname(os.path.abspath(__file__))

with open("user_settings.yaml") as settings:
    user_cfg = yaml.safe_load(settings)

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
from device_app_function import DeviceAppFunctions
from guiModules.ui_components import *
from guiModules.worker import *
from submodules.wifi_connection.wifiManager import WifiManager
from datetime import datetime
from submodules.common.log import Log

DBusGMainLoop(set_as_default=True)

bus = dbus.SessionBus()
proxy = bus.get_object("org.onboard.Onboard", "/org/onboard/Onboard/Keyboard")
keyboard = dbus.Interface(proxy, "org.onboard.Onboard.Keyboard")

FONT_OF_TABLE = QtGui.QFont()
FONT_OF_TABLE.setPointSize(16)
FONT_OF_TABLE.setBold(True)

FONT_OF_TABLE_BIG= QtGui.QFont()
FONT_OF_TABLE_BIG.setPointSize(20)
FONT_OF_TABLE_BIG.setBold(True)

LIMIT_NOTIFICATIONS = user_cfg['limitNotifications']
LIMIT_RECORDS = user_cfg['limitRecords']

ON_SWITCH_ICON = os.path.join(path, 'guiModules/images/ON.png')
OFF_SWITCH_ICON = os.path.join(path, 'guiModules/images/OFF.png')

class MainWindow(QtWidgets.QMainWindow):

    internetAvailable = pyqtSignal(bool)

    def __init__(self):
        super(MainWindow, self).__init__()
        self.suspend = False
        # self.show()

        self.startLoginWindow()
        self.threadpool = QtCore.QThreadPool()
        self.loading = LoadingDlg(self)
        self.loading.display('1')
        worker = Worker(self.initSystem)
        worker.signals.finished.connect(self.loading.close)
        worker.signals.finished.connect(self.checkWifiStatus)
        self.threadpool.start(worker)

        # QtWidgets.QApplication.instance().focusChanged.connect(self.handle_focuschanged)
        
        self.shortcut_quit = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+Q'), self)
        self.shortcut_quit.activated.connect(self.closeApp)

    #     self.shortcut_on_csv = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+O'), self)
    #     self.shortcut_off_csv = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+C'), self)
    #     self.shortcut_on_csv.activated.connect(self.activeCSV)
    #     self.shortcut_off_csv.activated.connect(self.deactiveCSV)
    
    # def activeCSV(self):
    #     self.deviceFuntion.csvAva = True
    
    # def deactiveCSV(self):
    #     self.deviceFuntion.csvAva = False

    def checkWifiStatus(self):
        wifiConnected = self.wifi.wifiConnected()
        print(wifiConnected)
        if (not wifiConnected):
            self.startConnectWifiWindow()
        else:
            self.checkActivatedStatusFromConfig()

    def checkActivatedStatusFromConfig(self):
        activateCode = self.deviceFuntion.isDeviceActivated()
        if not activateCode:
            self.startLoginWindow()
            keyboard.Show()
        else:
            self.startMainWindow()


    def initSystem(self):
        self.OfflineMode = False
        self.deviceFuntion =  DeviceAppFunctions(self.internetAvailable)
        self.internetAvailable.connect(self.getInternetStatus)
        self.wifi = WifiManager()
        return
    """
    Control windows
    """
    def startMainWindow(self):
        uic.loadUi("./device_app/guiModules/ui_files/mainWindow.ui", self)
        keyboard.Hide()
        self.loading = LoadingDlg(self)
        self.main_display_monitor = self.rgb_frame   

        clickableWidget(self.rgb_frame).connect(self.selectZoomMode)
        clickableWidget(self.zoom_monitor).connect(self.selectNormalMode)
        clickableWidget(self.toggle_one_person).connect(self.toggleOnePersonMode)

        self.selectStandardMenu("btn_home")  
        self.stackedWidget.setCurrentWidget(self.home_page)

        self.history_record.setColumnWidth(0, 80)
        self.history_record.setColumnWidth(1, 230)
        self.history_record.setColumnWidth(2, 50)
        self.history_record.verticalHeader().setDefaultSectionSize(50)
        self.history_record.verticalHeader().sectionResizeMode(QtWidgets.QHeaderView.Fixed)

        self.notifications.setColumnWidth(0, 130)
        self.notifications.verticalHeader().setDefaultSectionSize(30)
        self.notifications.verticalHeader().sectionResizeMode(QtWidgets.QHeaderView.Fixed)

        self.timerWorking = QtCore.QTimer()
        self.timerWorking.setTimerType(QtCore.Qt.PreciseTimer)
        self.timerWorking.timeout.connect(self.working)
        self.timerWorking.start(0)

        # worker = Worker(self.working)
        # self.threadpool.start(worker)

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

        self.btn_home.clicked.connect(self.button)
        self.btn_new_user.clicked.connect(self.button)
        self.btn_info.clicked.connect(self.button)
        self.register_button.clicked.connect(self.button)
        self.btn_calib.clicked.connect(self.button)
        self.settings.clicked.connect(self.button)
        self.save.clicked.connect(self.button)
        self.btn_exit.clicked.connect(self.button)


        self.notis_slider.valueChanged.connect(self.notisSliderValueHandle)
        self.temp_slider.valueChanged.connect(self.tempSliderValueHandle)
        self.time_calib_slider.valueChanged.connect(self.timeSliderValueHandle)
        self.records_slider.valueChanged.connect(self.recordsSliderValueHandle)
        self.bright_slider.valueChanged.connect(self.brightSliderValueHandle)
        self.threshold_slider.valueChanged.connect(self.thresholdSliderValueHandle)

    def startLoginWindow(self):

        uic.loadUi("./device_app/guiModules/ui_files/loginWindow.ui", self)
        self.loading = LoadingDlg(self)
        self.active_device_btn.clicked.connect(self.button)

    def startConnectWifiWindow(self):
        uic.loadUi("./device_app/guiModules/ui_files/connectWifi.ui", self)
        self.loading = LoadingDlg(self)
        self.loading.display()
        worker = Worker(self.wifi.getAvailableWifis)
        worker.signals.finished.connect(self.loading.close)
        worker.signals.result.connect(self.addSsidsIntoSelectionBox)
        self.threadpool.start(worker)

        self.check_new_wifi.stateChanged.connect(lambda state: [self.password_wifi.setText(""),self.password_wifi.setEnabled(state!=QtCore.Qt.Unchecked)])
        self.connect_wifi.clicked.connect(self.connectWifi)
        self.refresh_wifi.clicked.connect(self.refreshWifiList)


    """
    Main processing of the application
    """
    #PROCESSING OF THE MAIN SYSTEM
    def working(self):
        # while self.deviceFuntion.getMode() != "OFF":
        try: 
            if (not self.suspend):
                status = self.deviceFuntion.process()
                if (status == "REGISTER_SUCCESS"):
                    self.finishedFaceRegistrationStyle(self.face_right)
                    self.createInputNameDialog()
                elif (status == "REGISTER_DONE_LEFT"):
                    self.finishedFaceRegistrationStyle(self.face_left)
                elif (status == "REGISTER_DONE_FRONT"):
                    self.finishedFaceRegistrationStyle(self.face_front)
                elif (status == "CALIBRATE_TOO_MUCH_PEOPLE"):
                    Log('PROCESS', 'calibrate_one person please')
                elif (status == "CALIBRATE_SUCCESS"):
                    self.createInputGroundTruthTemp()
        except Exception as e:
            print(e)
            pass

    #Handle status of working process
    def handleRecordsAndNotis(self):
        records = self.deviceFuntion.getRecordsInfo()
            
        for (objectID, obj) in list(records.items()):
            current_time = datetime.now()
            self.addRecords(current_time, str(objectID) + '-' + obj.name, obj.record_temperature, obj.face_rgb)
            if (obj.have_mask is False):
                self.addNoti(current_time, str(objectID) + '-' + obj.name)
            if (obj.got_fever is True):
                self.addNoti(current_time, str(objectID) + '-' + obj.name, obj.record_temperature)
            del records[objectID]

    """
    Active device functions
    """
    @QtCore.pyqtSlot(object)
    def activeDevice(self, activatedStatus):
        if (activatedStatus):
            self.startMainWindow()
        else:
            self.noti = NotificationDlg('The PIN is not match. Please input again', self, 5)

    @QtCore.pyqtSlot(bool)
    def getInternetStatus(self, internetStatus):
        if (self.deviceFuntion.isInternetAvailable() != internetStatus):
            self.deviceFuntion.setInternetStatus(internetStatus)

    @QtCore.pyqtSlot(object)
    def checkRegisterStatus(self, status):
        if (status == 'UPDATE_SUCCESS'):
            self.noti = NotificationDlg('Register data update successful!', self, 7)
        elif (status == 'ADD_SUCCESS'):
            self.noti = NotificationDlg('Register data add successful!', self, 7)
        else:
            self.noti = NotificationDlg('The register code is wrong or used. Please register again!', self, 7)
        self.selectNormalMode()

    @QtCore.pyqtSlot(object)
    def addSsidsIntoSelectionBox(self, ssids):
        self.ssids_selection.clear()
        for id in ssids:
            self.ssids_selection.addItem(id['ssid'])

    @QtCore.pyqtSlot(object)
    def handleConnectionStatus(self, status):
        if (status == 'SUCCESS'):
            self.checkActivatedStatusFromConfig()
        else:
            self.noti = NotificationDlg(status, self)


    #Close the application
    def closeApp(self):
        try:
            self.deviceFuntion.stop()
        except Exception as e:
            print(e)
        app.quit()

    #Display main frame into rgb frame in homepage and register page
    def displayMainFrame(self):
        try:
            frame = self.deviceFuntion.getRgbFrame()
            frame = cv2.resize(frame, (self.main_display_monitor.width(),self.main_display_monitor.height()))
            height, width, _ = frame.shape
            qimg = QtGui.QImage(frame.data, width, height, 3*width, QtGui.QImage.Format_RGB888).rgbSwapped()
            self.main_display_monitor.setPixmap(QtGui.QPixmap(qimg))
        except Exception as e:
            pass

    #Display thermal frame in homepage
    def displayThermalFrame(self):
        try:
            frame = self.deviceFuntion.getThermalFrame()
            frame = cv2.resize(frame, (self.thremal_frame.width(),self.thremal_frame.height()))
            height, width, _ = frame.shape
            qimg = QtGui.QImage(frame.data, width, height, 3*width, QtGui.QImage.Format_RGB888).rgbSwapped()
            self.thremal_frame.setPixmap(QtGui.QPixmap(qimg))
        except Exception as e:
            pass

    
    #Create an input dialog to input person's info when finish face register
    def createInputNameDialog(self):
        keyboard.Show()
        self.dlg = InputNameDlg(self)
        self.dlg.accepted.connect(self.acceptInputRegisterCode)
        self.dlg.rejected.connect(self.cancelInputRegisterCode)
        self.suspend = True
        self.dlg.show()

    # Create an input dialog to input the ground truth temperature
    def createInputGroundTruthTemp(self):
        keyboard.Show()
        self.dlg = InputTempDlg(self)
        self.dlg.accepted.connect(self.acceptInputTempCalibrate)
        self.dlg.rejected.connect(self.cancelInputTempCalibrate)
        self.suspend = True
        self.dlg.show()
    
    # Change color of the face register state
    def finishedFaceRegistrationStyle(self, label_of_face):
        label_of_face.setStyleSheet(label_of_face.styleSheet() + ("background-color: rgb(147, 255, 165);"))

    # change one person mode
    def toggleOnePersonMode(self):
        if (self.deviceFuntion.getEnableOnePersonModeFlag()):
            self.toggle_one_person.setPixmap(QtGui.QPixmap(OFF_SWITCH_ICON))
            self.deviceFuntion.setEnableOnePersonModeFlag(False)
        else:
            self.toggle_one_person.setPixmap(QtGui.QPixmap(ON_SWITCH_ICON))
            self.deviceFuntion.setEnableOnePersonModeFlag(True)

    #switch to normal mode (working mode)
    def selectNormalMode(self):
        self.main_display_monitor = self.rgb_frame
        self.stackedWidget.setCurrentWidget(self.home_page)
        self.resetStyleBtn("btn_home")
        self.btn_home.setStyleSheet(self.selectMenu(self.btn_home.styleSheet()))
        if (self.deviceFuntion.getMode() != 'NORMAL'):
            self.deviceFuntion.selectNormalMode() 

    #switch to zoom mode
    def selectZoomMode(self):
        self.main_display_monitor = self.zoom_monitor
        self.stackedWidget.setCurrentWidget(self.zoom)

    # Switch to register mode
    def selectRegisterMode(self):
        self.main_display_monitor = self.register_screen
        self.face_left.setStyleSheet(self.face_left.styleSheet().replace("background-color: rgb(147, 255, 165);", ""))
        self.face_right.setStyleSheet(self.face_right.styleSheet().replace("background-color: rgb(147, 255, 165);", ""))
        self.face_front.setStyleSheet(self.face_front.styleSheet().replace("background-color: rgb(147, 255, 165);", ""))
        self.stackedWidget.setCurrentWidget(self.new_user)
        self.resetStyleBtn("btn_new_user")
        self.btn_new_user.setStyleSheet(self.selectMenu(self.btn_new_user.styleSheet()))
        self.noti = NotificationDlg('Please rotate your face following the order: LEFT, FRONT, RIGHT', self)
        if (self.deviceFuntion.getMode() != 'REGISTER'):
            self.deviceFuntion.selectRegisterMode() 

    def selectCalibrateMode(self):
        self.main_display_monitor = self.calibrate_screen
        self.stackedWidget.setCurrentWidget(self.calibrate)
        self.resetStyleBtn("btn_calib")
        self.btn_calib.setStyleSheet(self.selectMenu(self.btn_calib.styleSheet()))
        if (self.deviceFuntion.getMode() != 'CALIBRATE'):
            self.deviceFuntion.selectCalibrateMode() 

    def selectSettingMode(self):
        if (self.deviceFuntion.getMode() != 'NORMAL'):
            self.deviceFuntion.selectNormalMode()
        time_calib, temp, bright, threshold = self.deviceFuntion.getSettingsParam()
        self.time_calib_slider.setValue(time_calib)
        self.temp_slider.setValue(temp*100)
        self.records_slider.setValue(LIMIT_RECORDS)
        self.notis_slider.setValue(LIMIT_NOTIFICATIONS)
        self.bright_slider.setValue(bright)
        self.threshold_slider.setValue(threshold*100)
        self.stackedWidget.setCurrentWidget(self.setting)
        self.resetStyleBtn("settings")
        self.settings.setStyleSheet(self.selectMenu(self.settings.styleSheet()))
        if (self.deviceFuntion.getEnableOnePersonModeFlag()):
            self.toggle_one_person.setPixmap(QtGui.QPixmap(ON_SWITCH_ICON))
        else:
            self.toggle_one_person.setPixmap(QtGui.QPixmap(OFF_SWITCH_ICON))

    def selectInfoPage(self):
        self.stackedWidget.setCurrentWidget(self.product_info)
        self.resetStyleBtn("btn_info")
        self.product_info.setStyleSheet(self.selectMenu(self.product_info.styleSheet()))
        if (self.deviceFuntion.getMode() != 'NORMAL'):
            self.deviceFuntion.selectNormalMode()

    def saveSettingParam(self):
        global LIMIT_RECORDS, LIMIT_NOTIFICATIONS, user_cfg
        LIMIT_RECORDS = self.records_slider.value()
        LIMIT_NOTIFICATIONS = self.notis_slider.value()
        user_cfg['limitNotifications'] = LIMIT_NOTIFICATIONS
        user_cfg['limitRecords'] = LIMIT_RECORDS
        with open("user_settings.yaml", "w") as f:
            yaml.dump(user_cfg, f)
        time = self.time_calib_slider.value()
        temp = float(self.temp_slider.value()/100)
        bright = self.bright_slider.value()
        threshold = float(self.threshold_slider.value()/100)
        self.deviceFuntion.updateSettingParams(time_calib=time, temp_fever=temp, bright_incre=bright,threshold=threshold )
        self.selectNormalMode()

    def logoutSystem(self):
        self.deviceFuntion.deactivateDevice()
        self.checkWifiStatus()

    # Add notification when someone got fever or does not wear mask
    def addNoti(self, current_time, name, temp=None):
        vbar = self.notifications.verticalScrollBar()
        _scroll = vbar.value() == vbar.maximum()

        if (self.notifications.rowCount() >= LIMIT_NOTIFICATIONS):
            self.notifications.removeRow(0)

        self.notifications.insertRow(self.notifications.rowCount())

        time = current_time.strftime("%d-%m|%H:%M:%S")
        self.notifications.setItem(self.notifications.rowCount()-1, 0, QtWidgets.QTableWidgetItem(time))
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
    def addRecords(self, current_time, name, temperature, face_rgb):
        vbar = self.history_record.verticalScrollBar()
        _scroll = vbar.value() == vbar.maximum()
        
        if (self.history_record.rowCount() >= LIMIT_RECORDS*2):
            self.history_record.removeRow(0)
            self.history_record.removeRow(0)

        count = self.history_record.rowCount()
        self.history_record.insertRow(count)
        self.history_record.insertRow(count + 1)

        self.history_record.setSpan(count, 0, 2, 1)
        self.history_record.setSpan(count, 1, 1, 2)

        try:
            face = cv2.resize(face_rgb, (70,85))
            height, width, _ = face.shape
            qimg = QtGui.QImage(face.data, width, height, 3*width, QtGui.QImage.Format_RGB888).rgbSwapped()
            qimg = QtGui.QPixmap(qimg)
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.DecorationRole, qimg)
            self.history_record.setItem(count, 0, item)
        except Exception as e:
            print (e)
            pass

        time = QtWidgets.QTableWidgetItem(current_time.strftime("%d-%m-%Y   %H:%M:%S"))
        time.setTextAlignment(QtCore.Qt.AlignCenter)
        self.history_record.setItem(count, 1, time)
        self.history_record.item(count, 1).setFont(FONT_OF_TABLE_BIG)
        self.history_record.setItem(count + 1, 1, QtWidgets.QTableWidgetItem(name))
        self.history_record.item(count + 1, 1).setFont(FONT_OF_TABLE)
        temperature = "{:.2f}".format(temperature) + " oC"
        self.history_record.setItem(count + 1, 2, QtWidgets.QTableWidgetItem(temperature))
        self.history_record.item(count + 1, 2).setFont(FONT_OF_TABLE)

        if(_scroll):
            self.history_record.scrollToBottom()


    """
    Handle inputs and signals of the application
    """
    #Refresh the available wifis
    def refreshWifiList(self):
        self.loading.display()
        worker = Worker(self.wifi.getAvailableWifis)
        worker.signals.finished.connect(self.loading.close)
        worker.signals.result.connect(self.addSsidsIntoSelectionBox)
        self.threadpool.start(worker)

    #Connect to wifi by ssid
    def connectWifi(self):
        self.loading.display()
        ssid = str(self.ssids_selection.currentText())
        password = str(self.password_wifi.text())
        worker = Worker(self.wifi.connectNewWifi, ssid, password, self.check_new_wifi.isChecked())
        worker.signals.result.connect(self.handleConnectionStatus)
        worker.signals.finished.connect(self.loading.close)
        self.threadpool.start(worker)
        # self.wifi.connectNewWifi(ssid,password)
    
    #Ok button when input register name
    def acceptInputRegisterCode(self):
        keyboard.Hide()
        if self.dlg.isVisible():
            self.dlg.setVisible(False)
        self.loading.display()
        worker = Worker(self.deviceFuntion.sendRegisteredInfoToServer, self.dlg.register_code_edit.text())
        worker.signals.result.connect(self.checkRegisterStatus)
        worker.signals.finished.connect(self.loading.close)

        self.threadpool.start(worker)
        self.suspend = False

        # self.deviceFuntion.sendRegisteredInfoToServer(self.dlg.register_code_edit.text())

    #Cancel button when input register name
    def cancelInputRegisterCode(self):
        self.suspend = False
        keyboard.Hide()
        self.selectRegisterMode()

    def acceptInputTempCalibrate(self):
        keyboard.Hide()
        self.deviceFuntion.createUserTemperatureOffset(self.dlg.temperature_edit.text())
        self.suspend = False
        self.selectNormalMode()
    
    def cancelInputTempCalibrate(self):
        self.suspend = False
        keyboard.Hide()
        self.selectNormalMode()

    #Handle limit of records slider
    def recordsSliderValueHandle(self):
        records_limit = self.records_slider.value()
        records_limit = str(records_limit) + " records"
        self.records_label.setText(records_limit)

    #Handle limit of notis slider
    def notisSliderValueHandle(self):
        notis_limit = self.notis_slider.value()
        notis_limit = str(notis_limit) + ' notis'
        self.notis_label.setText(notis_limit)

    #Handle all temp slider
    def tempSliderValueHandle(self):
        temp = self.temp_slider.value()
        temp = str(float(temp/100)) + 'oC'
        self.temp_label.setText(temp)

    #Handle time slider
    def timeSliderValueHandle(self):
        time = self.time_calib_slider.value()
        time = str(time) + ' seconds'
        self.time_calib_label.setText(time)

    #Handle Bright increment slider
    def brightSliderValueHandle(self):
        bright = self.bright_slider.value()
        bright = str(bright) + ' percent'
        self.bright_label.setText(bright)

    #Handle Face detection threshold slider
    def thresholdSliderValueHandle(self):
        threshold = self.threshold_slider.value()
        threshold = str(threshold) + ' percent'
        self.threshold_label.setText(threshold)

    #Handle all button of the application
    def button(self):
        # GET BT CLICKED
        btnWidget = self.sender()

        # PAGE HOME
        if btnWidget.objectName() == "btn_home":
            self.selectNormalMode()

        # PAGE NEW USER
        if btnWidget.objectName() == "btn_new_user" or btnWidget.objectName() == "register_button":
            self.selectRegisterMode()

        # PAGE FOR CALIBRATION
        if btnWidget.objectName() == "btn_calib":
            self.selectCalibrateMode()

        # PAGE INFO
        if btnWidget.objectName() == "btn_info":
            self.selectInfoPage()

        if btnWidget.objectName() == "settings":
            self.selectSettingMode()      

        if btnWidget.objectName() == "save":
            self.saveSettingParam()  

        if btnWidget.objectName() == "active_device_btn":
            self.loading.display()
            worker = Worker(self.deviceFuntion.activateDevice, self.pin_code.text())
            worker.signals.result.connect(self.activeDevice)
            worker.signals.finished.connect(self.loading.close)
            self.threadpool.start(worker)
        
        if btnWidget.objectName() == "btn_exit":
            self.logoutSystem()


    # @QtCore.pyqtSlot("QWidget*", "QWidget*")
    # def handle_focuschanged(self, old, now):
    #     time.sleep(1)
        # if now.objectName() == "name_edit":
        #     keyboard.Show()
        # elif self.lineEdit == old:
        #     keyboard.Hide()

    ## ==> SELECT
    def selectMenu(self, getStyle):
        select = getStyle + ("QPushButton { background-color:#61668c; border-left: 28px solid #61668c; border-right: 11px solid #61668c; }")
        return select

    ## ==> DESELECT
    def deselectMenu(self, getStyle):
        deselect = getStyle.replace("QPushButton { background-color:#61668c; border-left: 28px solid #61668c; border-right: 11px solid #61668c; }", "")
        return deselect

    ## ==> START SELECTION
    def selectStandardMenu(self, widget):
        for w in self.menu.findChildren(QtWidgets.QPushButton):
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
    