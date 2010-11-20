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

    dateOptions = {datetime.date.today().strftime('%Y-%m-%d (YYYY-MM-DD)') : '%Y-%m-%d',
                   datetime.date.today().strftime('%Y-%d-%m (YYYY-DD-MM)') : '%Y-%d-%m',
                   datetime.date.today().strftime('%B %d, %Y'): '%B %d, %Y',
                   datetime.date.today().strftime('%d %B, %Y'): '%d %B, %Y'}
    """Map the ComboBox text values to the actual values saved"""

    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        self.resize(0, 0) # fixes problem of the window being too big on Windows

        self.albumTitleFormatLineEdit.setText(getSettings()['albumTitleFormat'])

        if getSettings()['defaultArt'] == 'Image File => Identicon':
            self.defaultArtRadioButtonImageFileIdenticon.setChecked(True)
        elif getSettings()['defaultArt'] == 'Image File => Visicon':
            self.defaultArtRadioButtonImageFileVisicon.setChecked(True)
        elif getSettings()['defaultArt'] == 'Visicon':
            self.defaultArtRadioButtonVisicon.setChecked(True)
        else:
            self.defaultArtRadioButtonIdenticon.setChecked(True)

        if getSettings()['checkForUpdates']:
            self.checkForUpdatesCheckBox.setChecked(True)

        self.addToITunesPathTextEdit.setText(getSettings()['addToITunesPath'])

        # Set the ComboBox values
        for k, v in self.dateOptions.iteritems():
            self.dateFormatComboBox.addItem(k, v)

        # Select the value saved in settings
        self.dateFormatComboBox.setCurrentIndex(
            self.dateFormatComboBox.findData(getSettings()['dateFormat'])
        )

    def accept(self):
        getSettings()['albumTitleFormat'] = unicode(self.albumTitleFormatLineEdit.text())
        getSettings()['dateFormat'] = unicode(self.dateOptions[str(self.dateFormatComboBox.currentText())])
        if self.defaultArtRadioButtonImageFileIdenticon.isChecked():
            getSettings()['defaultArt'] = u'Image File => Identicon'
        elif self.defaultArtRadioButtonImageFileVisicon.isChecked():
            getSettings()['defaultArt'] = u'Image File => Visicon'
        elif self.defaultArtRadioButtonVisicon.isChecked():
            getSettings()['defaultArt'] = u'Visicon'
        else:
            getSettings()['defaultArt'] = u'Identicon'

        getSettings()['checkForUpdates'] = self.checkForUpdatesCheckBox.isChecked()

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