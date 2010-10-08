# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'queuedialog.ui'
#
# Created: Sun Sep 12 22:27:27 2010
#      by: PyQt4 UI code generator snapshot-4.7.5-7088e9094087
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_QueueDialog(object):
    def setupUi(self, QueueDialog):
        QueueDialog.setObjectName(_fromUtf8("QueueDialog"))
        QueueDialog.resize(524, 649)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(QueueDialog.sizePolicy().hasHeightForWidth())
        QueueDialog.setSizePolicy(sizePolicy)
        QueueDialog.setAutoFillBackground(False)
        QueueDialog.setSizeGripEnabled(False)
        self.verticalLayout = QtGui.QVBoxLayout(QueueDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        spacerItem = QtGui.QSpacerItem(88, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.settingsButton = QtGui.QPushButton(QueueDialog)
        self.settingsButton.setObjectName(_fromUtf8("settingsButton"))
        self.horizontalLayout_3.addWidget(self.settingsButton)
        spacerItem1 = QtGui.QSpacerItem(78, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.label_2 = QtGui.QLabel(QueueDialog)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.queueListWidget = QtGui.QListWidget(QueueDialog)
        self.queueListWidget.setMinimumSize(QtCore.QSize(500, 298))
        self.queueListWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.queueListWidget.setObjectName(_fromUtf8("queueListWidget"))
        self.verticalLayout.addWidget(self.queueListWidget)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem2 = QtGui.QSpacerItem(68, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.pushButton = QtGui.QPushButton(QueueDialog)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.horizontalLayout.addWidget(self.pushButton)
        self.pushButton_2 = QtGui.QPushButton(QueueDialog)
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.horizontalLayout.addWidget(self.pushButton_2)
        spacerItem3 = QtGui.QSpacerItem(68, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem3)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        spacerItem4 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem4)
        self.AddToITunesButton = QtGui.QPushButton(QueueDialog)
        self.AddToITunesButton.setObjectName(_fromUtf8("AddToITunesButton"))
        self.horizontalLayout_4.addWidget(self.AddToITunesButton)
        spacerItem5 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem5)
        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.retranslateUi(QueueDialog)
        QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL(_fromUtf8("clicked()")), QueueDialog.openFileDialog)
        QtCore.QObject.connect(self.settingsButton, QtCore.SIGNAL(_fromUtf8("clicked()")), QueueDialog.openSettingsDialog)
        QtCore.QObject.connect(self.pushButton_2, QtCore.SIGNAL(_fromUtf8("clicked()")), QueueDialog.removeSelectedItem)
        QtCore.QObject.connect(self.queueListWidget, QtCore.SIGNAL(_fromUtf8("itemDoubleClicked(QListWidgetItem*)")), QueueDialog.openConfirmMetadata)
        QtCore.QObject.connect(self.AddToITunesButton, QtCore.SIGNAL(_fromUtf8("clicked()")), QueueDialog.addToITunes)
        QtCore.QMetaObject.connectSlotsByName(QueueDialog)

    def retranslateUi(self, QueueDialog):
        QueueDialog.setWindowTitle(QtGui.QApplication.translate("QueueDialog", "BootTunes Queue", None, QtGui.QApplication.UnicodeUTF8))
        self.settingsButton.setText(QtGui.QApplication.translate("QueueDialog", "Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("QueueDialog", "Double-click entry to edit.", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.setText(QtGui.QApplication.translate("QueueDialog", "+", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_2.setText(QtGui.QApplication.translate("QueueDialog", "-", None, QtGui.QApplication.UnicodeUTF8))
        self.AddToITunesButton.setText(QtGui.QApplication.translate("QueueDialog", "Add To iTunes", None, QtGui.QApplication.UnicodeUTF8))

