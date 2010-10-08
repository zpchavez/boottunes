"""
Customized QMessageBox that uses the BootTunes logo.

Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""
import os
import data
from PyQt4.QtGui import *

class MessageBox(QMessageBox):
    @staticmethod
    def warning(*args):
        MessageBox.general(*args)

    @staticmethod
    def critical(*args):
        MessageBox.general(*args)

    @staticmethod
    def information(*args):
        MessageBox.general(*args)

    @staticmethod
    def general(*args):
        Box = QMessageBox(0, args[1], args[2], QMessageBox.Ok, args[0])
        pixmap = QPixmap(data.path + os.sep + 'media' + os.sep + 'logo.png')
        pixmap = pixmap.scaledToHeight(64)
        Box.setIconPixmap(pixmap)
        Box.exec_()