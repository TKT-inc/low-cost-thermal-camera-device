# This Python file uses the following encoding: utf-8
import sys
import cv2
import time
import dbus
import yaml

with open("user_settings.yaml") as settings:
    user_cfg = yaml.safe_load(settings)

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
from device_app_function import DeviceAppFunctions
from guiModules.ui_components import *
from guiModules.worker import *
from datetime import datetime
from submodules.common.log import Log

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
        worker.signals.finished.connect(self.checkActivatedStatusFromConfig)
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

    def checkActivatedStatusFromConfig(self):
        activateCode = self.deviceFuntion.isDeviceActivated()
        if not activateCode:
            keyboard.Show()
        else:
            self.startMainWindow()


    def initSystem(self):
        self.OfflineMode = False
        self.deviceFuntion =  DeviceAppFunctions(self.internetAvailable)
        self.internetAvailable.connect(self.getInternetStatus)
        return
    """
    Control windows
    """
    def startMainWindow(self):
        uic.loadUi("./device_app/guiModules/ui_files/mainWindow.ui", self)
        keyboard.Hide()
        self.main_display_monitor = self.rgb_frame   

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


        self.notis_slider.valueChanged.connect(self.notisSliderValueHandle)
        self.temp_slider.valueChanged.connect(self.tempSliderValueHandle)
        self.time_calib_slider.valueChanged.connect(self.timeSliderValueHandle)
        self.records_slider.valueChanged.connect(self.recordsSliderValueHandle)

    def startLoginWindow(self):

        uic.loadUi("./device_app/guiModules/ui_files/loginWindow.ui", self)
        self.active_device_btn.clicked.connect(self.button)

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
            self.noti = NotificationDlg('The PIN is not match. Please input again', self)

    @QtCore.pyqtSlot(bool)
    def getInternetStatus(self, internetStatus):
        if (self.deviceFuntion.isInternetAvailable() != internetStatus):
            self.deviceFuntion.setInternetStatus(internetStatus)

    #Close the application
    def closeApp(self):
        try:
            self.deviceFuntion.stop()
        except:
            pass
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
        time_calib, temp = self.deviceFuntion.getSettingsParam()
        self.time_calib_slider.setValue(time_calib)
        self.temp_slider.setValue(temp*100)
        self.records_slider.setValue(LIMIT_RECORDS)
        self.notis_slider.setValue(LIMIT_NOTIFICATIONS)
        self.stackedWidget.setCurrentWidget(self.setting)
        self.resetStyleBtn("settings")
        self.settings.setStyleSheet(self.selectMenu(self.settings.styleSheet()))

    def selectInfoPage(self):
        self.stackedWidget.setCurrentWidget(self.product_info)
        self.resetStyleBtn("btn_info")
        btnWidget.setStyleSheet(self.selectMenu(btnWidget.styleSheet()))
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
        self.deviceFuntion.updateSettingParams(time_calib=time, temp_fever=temp)
        self.selectNormalMode()
        
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
    
    #Ok button when input register name
    def acceptInputRegisterName(self):
        self.suspend = False
        keyboard.Hide()
        self.selectNormalMode()
        self.deviceFuntion.sendRegisteredInfoToServer(self.dlg.name_edit.text())

    #Cancel button when input register name
    def cancelInputRegisterName(self):
        self.suspend = False
        keyboard.Hide()
        self.selectRegisterMode()

    def acceptInputTempCalibrate(self):
        self.suspend = False
        keyboard.Hide()
        self.deviceFuntion.createUserTemperatureOffset(self.dlg.temperature_edit.text())
        self.selectNormalMode()
    
    def cancelInputTempCalibrate(self):
        self.suspend = False
        keyboard.Hide()
        self.selectCalibrateMode()

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


    # @QtCore.pyqtSlot("QWidget*", "QWidget*")
    # def handle_focuschanged(self, old, now):
    #     time.sleep(1)
        # if now.objectName() == "name_edit":
        #     keyboard.Show()
        # elif self.lineEdit == old:
        #     keyboard.Hide()

    ## ==> SELECT
    def selectMenu(self, getStyle):
        select = getStyle + ("QPushButton { background-color:#61668c; border-left: 28px solid #61668c; border-right: 11px solid rgb(44, 49, 60); }")
        return select

    ## ==> DESELECT
    def deselectMenu(self, getStyle):
        deselect = getStyle.replace("QPushButton { background-color:#61668c; border-left: 28px solid #61668c; border-right: 11px solid rgb(44, 49, 60); }", "")
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
    