# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'choosecover.ui'
#
# Created: Fri Sep  3 23:10:27 2010
#      by: PyQt4 UI code generator snapshot-4.7.5-7088e9094087
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_ChooseCoverDialog(object):
    def setupUi(self, ChooseCoverDialog):
        ChooseCoverDialog.setObjectName(_fromUtf8("ChooseCoverDialog"))
        ChooseCoverDialog.resize(323, 137)
        self.gridLayout = QtGui.QGridLayout(ChooseCoverDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        spacerItem = QtGui.QSpacerItem(128, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.imageLabel = QtGui.QLabel(ChooseCoverDialog)
        self.imageLabel.setText(_fromUtf8(""))
        self.imageLabel.setObjectName(_fromUtf8("imageLabel"))
        self.horizontalLayout_2.addWidget(self.imageLabel)
        spacerItem1 = QtGui.QSpacerItem(148, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 0, 1, 3)
        self.chooseCoverComboBox = QtGui.QComboBox(ChooseCoverDialog)
        self.chooseCoverComboBox.setObjectName(_fromUtf8("chooseCoverComboBox"))
        self.gridLayout.addWidget(self.chooseCoverComboBox, 1, 0, 1, 3)
        spacerItem2 = QtGui.QSpacerItem(103, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem2, 2, 0, 1, 1)
        self.pushButton = QtGui.QPushButton(ChooseCoverDialog)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.gridLayout.addWidget(self.pushButton, 2, 1, 1, 1)
        spacerItem3 = QtGui.QSpacerItem(105, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem3, 2, 2, 1, 1)

        self.retranslateUi(ChooseCoverDialog)
        QtCore.QObject.connect(self.chooseCoverComboBox, QtCore.SIGNAL(_fromUtf8("currentIndexChanged(int)")), ChooseCoverDialog.chooseCover)
        QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL(_fromUtf8("clicked()")), ChooseCoverDialog.accept)
        QtCore.QMetaObject.connectSlotsByName(ChooseCoverDialog)

    def retranslateUi(self, ChooseCoverDialog):
        ChooseCoverDialog.setWindowTitle(QtGui.QApplication.translate("ChooseCoverDialog", "Choose Cover Image", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.setText(QtGui.QApplication.translate("ChooseCoverDialog", "Add", None, QtGui.QApplication.UnicodeUTF8))

