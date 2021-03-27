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

