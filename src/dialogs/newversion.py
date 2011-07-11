"""
Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from ui.ui_newversion import Ui_NewVersionDialog
from settings import getSettings

class NewVersionDialog(QDialog, Ui_NewVersionDialog):

    def __init__(self, info, parent=None):
        super(NewVersionDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self.setMinimumSize(QSize(500, 500))
        self.messageLabel.setText('Version ' + info['version'] + ' is now available')
        self.textBrowser.setHtml(info['changes'])
        self.info = info

    def skipVersion(self):
        getSettings()['skipVersion'] = self.info['version']
        self.hide()

    def visitDownloadPage(self):
        QDesktopServices.openUrl(QUrl(self.info['url']))
        getSettings()['skipVersion'] = self.info['version']
        self.hide()

    def reject(self):
       self.hide()