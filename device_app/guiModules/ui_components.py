from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic

class InputNameDlg(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("./device_app/guiModules/ui_files/inputNameDialog.ui", self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

class InputTempDlg(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("./device_app/guiModules/ui_files/inputCalibrateTemp.ui", self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

class NotificationDlg(QtWidgets.QDialog):
    def __init__(self, noti="GOT ERROR DURING OPERATING" ,parent=None, timeout=None):
        super().__init__(parent)
        uic.loadUi("./device_app/guiModules/ui_files/notificationDialog.ui", self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.notification.setText(noti)
        self.show()
        if (timeout is not None):
            self.time_to_wait = timeout
            self.timeout_noti.setText("Closing automatically in {0} secondes.".format(self.time_to_wait))
            self.timer = QtCore.QTimer(self)
            self.timer.setInterval(1000)
            self.timer.timeout.connect(self.changeContent)
            self.timer.start()

    def changeContent(self):
        self.time_to_wait -= 1
        self.timeout_noti.setText("Closing automatically in {0} secondes.".format(self.time_to_wait))
        if self.time_to_wait <= 0:
            self.close()

    def closeEvent(self, event):
        print('close Dlg Noti')
        self.timer.stop()
        event.accept()
    
    def accept(self):
        print('OK Dlg Noti')
        try:
            self.timer.stop()
        except:
            pass
        super().accept()

class LoadingDlg(QtWidgets.QDialog):
    def __init__(self, parent=None, opacity='0.4'):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.resize(parent.size().width(), parent.size().height())
        self.loading_label = QtWidgets.QLabel(self)
        self.loading_label.resize(227,227)
        self.loading_label.move(self.rect().center()- self.loading_label.rect().center())
        self.setStyleSheet("background-color:rgba(0,0,0,"+ opacity +");")
        self.loading_label.setStyleSheet("background-color: transparent;")
        self.movie = QtGui.QMovie('./device_app/guiModules/images/loading.gif')
        self.loading_label.setMovie(self.movie)
        self.movie.start()
        self.close()
    
    def display(self, opacity='0.4'):
        self.setStyleSheet("background-color:rgba(0,0,0,"+ opacity +");")
        self.show()
    
def clickableWidget(widget):
    class Filter(QtCore.QObject):

        clicked = QtCore.pyqtSignal()
        
        def eventFilter(self, obj, event):
            if obj == widget:
                if event.type() == QtCore.QEvent.MouseButtonRelease:
                    if obj.rect().contains(event.pos()):
                        self.clicked.emit()
                        return True
            return False
    
    filter = Filter(widget)
    widget.installEventFilter(filter)
    return filter.clicked