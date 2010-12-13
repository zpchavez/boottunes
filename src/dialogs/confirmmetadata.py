"""
Dialog displaying the information gleaned from the txt file.

Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""
import datetime
import difflib
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from settings import getSettings
from ui.ui_confirmmetadata import Ui_ConfirmMetadataDialog
from dialogs.choosecover import ChooseCoverDialog


class ConfirmMetadataDialog(QDialog, Ui_ConfirmMetadataDialog):

    def __init__(self, metadata, parent=None):
        """
        @type  metadata: dict
        @param metadata: The dict returned by parsetxt.TxtParser.parseTxt()

        @type  dir: QDir
        @param dir: The path to the selected directory
        """
        super(ConfirmMetadataDialog, self).__init__(parent)
        self.metadata = metadata
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)

        artistDefaults = getSettings().getArtistDefaults(metadata['artist'])
        if artistDefaults:            
            self.artistLineEdit.setText(artistDefaults['preferred_name'].decode('utf_8'))            
        else:
            self.artistLineEdit.setText(metadata['artist'])

        pyDate = metadata['date']
        if pyDate == None:
            pyDate = datetime.date.today()
        self.dateEdit.setDate(QDate(pyDate.year, pyDate.month, pyDate.day))
        self.locationLineEdit.setText(metadata['location'])
        self.venueLineEdit.setText(metadata['venue'])
        if artistDefaults and 'genre' in artistDefaults:
            self.genreLineEdit.setText(artistDefaults['genre'])

        self.tracklistTableWidget.setRowCount(len(metadata['tracklist']))
        self.tracklistTableWidget.setColumnCount(1)
        self.tracklistTableWidget.setColumnWidth(0, 2000)
        self.tracklistTableWidget.setHorizontalHeaderLabels(['']) # Don't label the column header
        for track, title in enumerate(metadata['tracklist']):
            self.tracklistTableWidget.setItem(track, 0, QTableWidgetItem(title))
        self.commentsTextEdit.setText(metadata['comments'])

    def accept(self):                
        suggestedArtist = unicode(self.metadata['artist'])
        submittedArtist = unicode(self.artistLineEdit.text()).strip()        

        defaults = {
            'preferred_name': submittedArtist,
            'genre'         : unicode(self.genreLineEdit.text()).strip()
        }

        # If the entered name has little similarity to the original, assume the detected artist was
        # completely wrong and is not synonymous with the submitted artist name.
        diff = difflib.SequenceMatcher(None, suggestedArtist.lower(), submittedArtist.lower())

        getSettings().setArtistDefaults(
            suggestedArtist if suggestedArtist and diff.ratio() > 0.5 else submittedArtist,
            defaults
        )

        if submittedArtist:
            self.metadata['artist'] = submittedArtist
        else:
            self.metadata['artist'] = ''

        self.metadata['defaults'] = defaults        

        qDate = self.dateEdit.date()
        self.metadata['date'] = datetime.date(qDate.year(), qDate.month(), qDate.day())
        self.metadata['location'] = unicode(self.locationLineEdit.text())
        self.metadata['venue'] = unicode(self.venueLineEdit.text())

        self.metadata['tracklist'] = [
            unicode(self.tracklistTableWidget.item(1, i).text())
            for i in range(-1, self.tracklistTableWidget.rowCount() - 1)
        ]

        self.metadata['title'] = unicode(self.titleLineEdit.text())
        self.close()        
        ChooseCoverDialog(self.metadata, parent=self.parentWidget()).exec_()