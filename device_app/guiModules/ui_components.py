from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic

class InputDlg(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("./device_app/guiModules/inputNameDialog.ui", self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

class FaderWidget(QtWidgets.QWidget):

    def __init__(self, old_widget, new_widget):
    
        QtWidgets.QWidget.__init__(self, new_widget)
        
        self.old_pixmap = QtGui.QPixmap(new_widget.size())
        old_widget.render(self.old_pixmap)
        self.pixmap_opacity = 1.0
        
        self.timeline = QtCore.QTimeLine()
        self.timeline.valueChanged.connect(self.animate)
        self.timeline.finished.connect(self.close)
        self.timeline.setDuration(333)
        self.timeline.start()
        
        self.resize(new_widget.size())
        self.show()
    
    def paintEvent(self, event):
    
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setOpacity(self.pixmap_opacity)
        painter.drawPixmap(0, 0, self.old_pixmap)
        painter.end()
    
    def animate(self, value):
    
        self.pixmap_opacity = 1.0 - value
        self.repaint()
