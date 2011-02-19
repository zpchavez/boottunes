"""
Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""
import datetime
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from settings import getSettings
from ui.ui_settings import Ui_SettingsDialog

class SettingsDialog(QDialog, Ui_SettingsDialog):

    dateOptionsDisplay = [
        datetime.date.today().strftime('%Y-%m-%d (YYYY-MM-DD)'),
        datetime.date.today().strftime('%Y-%d-%m (YYYY-DD-MM)'),
        datetime.date.today().strftime('%y-%m-%d (YY-MM-DD)'),
        datetime.date.today().strftime('%y-%d-%m (YY-DD-MM)'),
        datetime.date.today().strftime('%B %d, %Y'),
        datetime.date.today().strftime('%d %B, %Y')
    ]
    """The displayed ComboBox values"""

    dateOptionsFormat = [
        '%Y-%m-%d',
        '%Y-%d-%m',
        '%y-%m-%d',
        '%y-%d-%m',
        '%B %d, %Y',
        '%d %B, %Y'
    ]
    """The actual values saved in settings"""
        
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        self.resize(0, 0) # fixes problem of the window being too big on Windows

        self.albumTitleFormatLineEdit.setText(getSettings()['albumTitleFormat'])

        self.defaultArtRadioButtons = {
            'Identicon'                 : self.defaultArtRadioButtonIdenticon,
            'Visicon'                   : self.defaultArtRadioButtonVisicon,
            'No Cover Art'              : self.defaultArtRadioButtonNoCoverArt,
            'Image File => Identicon'   : self.defaultArtRadioButtonImageFileIdenticon,
            'Image File => Visicon'     : self.defaultArtRadioButtonImageFileVisicon,
            'Image File => No Cover Art': self.defaultArtRadioButtonImageFileNoCoverArt
        }

        for value, button in self.defaultArtRadioButtons.iteritems():
            if getSettings()['defaultArt'] == value:
                button.setChecked(True)
                break

        if getSettings()['checkForUpdates']:
            self.checkForUpdatesCheckBox.setChecked(True)

        if getSettings()['sendErrorReports']:
            self.sendErrorReportsCheckBox.setChecked(True)

        self.addToITunesPathTextEdit.setText(getSettings()['addToITunesPath'])

        # Set the ComboBox values
        for index, display in enumerate(self.dateOptionsDisplay):
            self.dateFormatComboBox.addItem(display, self.dateOptionsFormat[index])

        # Select the value saved in settings
        self.dateFormatComboBox.setCurrentIndex(
            self.dateFormatComboBox.findData(getSettings()['dateFormat'])
        )

    def accept(self):
        getSettings()['albumTitleFormat'] = unicode(self.albumTitleFormatLineEdit.text())
        getSettings()['dateFormat'] = unicode(self.dateOptionsFormat[self.dateFormatComboBox.currentIndex()])

        for value, button in self.defaultArtRadioButtons.iteritems():
            if button.isChecked():
                getSettings()['defaultArt'] = value

        getSettings()['checkForUpdates'] = self.checkForUpdatesCheckBox.isChecked()
        
        getSettings()['sendErrorReports'] = self.sendErrorReportsCheckBox.isChecked()
        
        getSettings()['addToITunesPath'] = unicode(self.addToITunesPathTextEdit.toPlainText())

        self.parentWidget().refreshQueue()
        self.close()

    def restoreDefaults(self):
        self.albumTitleFormatLineEdit.setText(getSettings().defaults['albumTitleFormat'])
        
        if getSettings().defaults['defaultArt'] == 'Image File => Identicon':
            self.defaultArtRadioButtonImageFileIdenticon.setChecked(True)
        elif getSettings().defaults['defaultArt'] == 'Image File => Visicon':
            self.defaultArtRadioButtonImageFileVisicon.setChecked(True)
        elif getSettings().defaults['defaultArt'] == 'Visicon':
            self.defaultArtRadioButtonVisicon.setChecked(True)
        else:
            self.defaultArtRadioButtonIdenticon.setChecked(True)
    
        self.checkForUpdatesCheckBox.setChecked(getSettings().defaults['checkForUpdates'])
        self.sendErrorReportsCheckBox.setChecked(getSettings().defaults['sendErrorReports'])

        defaultAddToITunesPath = getSettings().getDetectedAddToITunesPath()
        if defaultAddToITunesPath:
            self.addToITunesPathTextEdit.setText(defaultAddToITunesPath)

        # Select the value saved in settings
        self.dateFormatComboBox.setCurrentIndex(
            self.dateFormatComboBox.findData(getSettings().defaults['dateFormat'])
        )
        
    def changeAddToITunesPath(self):
        dirName = QFileDialog.getExistingDirectory(self, 'Locate Directory', getSettings()['addToITunesPath'])
        if dirName:            
            self.addToITunesPathTextEdit.setText(dirName)