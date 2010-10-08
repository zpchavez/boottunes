# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'newversion.ui'
#
# Created: Wed Oct  6 21:27:53 2010
#      by: PyQt4 UI code generator 4.7.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_NewVersionDialog(object):
    def setupUi(self, NewVersionDialog):
        NewVersionDialog.setObjectName(_fromUtf8("NewVersionDialog"))
        NewVersionDialog.resize(448, 287)
        self.gridLayout = QtGui.QGridLayout(NewVersionDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.messageLabel = QtGui.QLabel(NewVersionDialog)
        self.messageLabel.setText(_fromUtf8(""))
        self.messageLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.messageLabel.setObjectName(_fromUtf8("messageLabel"))
        self.verticalLayout.addWidget(self.messageLabel)
        self.textBrowser = QtGui.QTextBrowser(NewVersionDialog)
        self.textBrowser.setObjectName(_fromUtf8("textBrowser"))
        self.verticalLayout.addWidget(self.textBrowser)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.skipVersionButton = QtGui.QPushButton(NewVersionDialog)
        self.skipVersionButton.setAutoDefault(False)
        self.skipVersionButton.setObjectName(_fromUtf8("skipVersionButton"))
        self.horizontalLayout.addWidget(self.skipVersionButton)
        self.visitDownloadPageButton = QtGui.QPushButton(NewVersionDialog)
        self.visitDownloadPageButton.setAutoDefault(False)
        self.visitDownloadPageButton.setObjectName(_fromUtf8("visitDownloadPageButton"))
        self.horizontalLayout.addWidget(self.visitDownloadPageButton)
        self.dismissButton = QtGui.QPushButton(NewVersionDialog)
        self.dismissButton.setObjectName(_fromUtf8("dismissButton"))
        self.horizontalLayout.addWidget(self.dismissButton)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)

        self.retranslateUi(NewVersionDialog)
        QtCore.QObject.connect(self.skipVersionButton, QtCore.SIGNAL(_fromUtf8("clicked()")), NewVersionDialog.skipVersion)
        QtCore.QObject.connect(self.visitDownloadPageButton, QtCore.SIGNAL(_fromUtf8("clicked()")), NewVersionDialog.visitDownloadPage)
        QtCore.QObject.connect(self.dismissButton, QtCore.SIGNAL(_fromUtf8("clicked()")), NewVersionDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(NewVersionDialog)

    def retranslateUi(self, NewVersionDialog):
        NewVersionDialog.setWindowTitle(QtGui.QApplication.translate("NewVersionDialog", "New Version Available", None, QtGui.QApplication.UnicodeUTF8))
        self.skipVersionButton.setText(QtGui.QApplication.translate("NewVersionDialog", "Skip Version", None, QtGui.QApplication.UnicodeUTF8))
        self.visitDownloadPageButton.setText(QtGui.QApplication.translate("NewVersionDialog", "Visit Download Page", None, QtGui.QApplication.UnicodeUTF8))
        self.dismissButton.setText(QtGui.QApplication.translate("NewVersionDialog", "Dismiss", None, QtGui.QApplication.UnicodeUTF8))

