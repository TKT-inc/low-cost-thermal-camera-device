# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_mainUi(object):
    def setupUi(self, mainUi):
        if not mainUi.objectName():
            mainUi.setObjectName(u"mainUi")
        mainUi.resize(1920, 1080)
        mainUi.setMinimumSize(QSize(1920, 1080))
        mainUi.setMaximumSize(QSize(1920, 1080))
        mainUi.setAutoFillBackground(False)
        mainUi.setStyleSheet(u"")
        self.centralwidget = QWidget(mainUi)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 60, 1481, 981))
        self.label.setStyleSheet(u"\n"
"background-color: rgb(34, 34, 34);")
        self.pushButton_2 = QPushButton(self.frame)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setGeometry(QRect(40, 0, 141, 51))
        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(1510, 10, 381, 361))
        self.label_2.setStyleSheet(u"background-color: rgb(27, 27, 27);")
        self.tableView = QTableView(self.frame)
        self.tableView.setObjectName(u"tableView")
        self.tableView.setGeometry(QRect(1510, 390, 381, 651))
        self.pushButton_3 = QPushButton(self.frame)
        self.pushButton_3.setObjectName(u"pushButton_3")
        self.pushButton_3.setGeometry(QRect(220, 0, 141, 51))

        self.verticalLayout.addWidget(self.frame)

        mainUi.setCentralWidget(self.centralwidget)

        self.retranslateUi(mainUi)

        QMetaObject.connectSlotsByName(mainUi)
    # setupUi

    def retranslateUi(self, mainUi):
        mainUi.setWindowTitle(QCoreApplication.translate("mainUi", u"mainUi", None))
        self.label.setText("")
        self.pushButton_2.setText(QCoreApplication.translate("mainUi", u"PushButton", None))
        self.label_2.setText(QCoreApplication.translate("mainUi", u"TextLabel", None))
        self.pushButton_3.setText(QCoreApplication.translate("mainUi", u"PushButton", None))
    # retranslateUi

