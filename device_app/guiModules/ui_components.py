from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic

class InputNameDlg(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("./device_app/guiModules/inputNameDialog.ui", self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

class InputTempDlg(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("./device_app/guiModules/inputCalibrateTemp.ui", self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

class NotificationDlg(QtWidgets.QDialog):
    def __init__(self, noti="GOT ERROR DURING OPERATING" ,parent=None):
        super().__init__(parent)
        uic.loadUi("./device_app/guiModules/notificationDialog.ui", self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.notification.setText(noti)
        self.exec()

class LoadingDlg(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        uic.loadUi("./device_app/guiModules/loading.ui", self)

        self.resize(parent.size().width(), parent.size().height())
        self.loading_label.resize(227,227)
        self.loading_label.move(self.rect().center()- self.loading_label.rect().center())
        self.setStyleSheet("background-color:rgba(0,0,0, 0.4);")
        self.loading_label.setStyleSheet("background-color: transparent;")
        self.movie = QtGui.QMovie('./device_app/guiModules/images/loading.gif')
        self.loading_label.setMovie(self.movie)
        self.movie.start()
        self.close()