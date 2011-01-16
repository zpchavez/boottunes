"""
Dialog displaying the information gleaned from the txt file.

Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""
import datetime
import difflib
import audiotools
import pyaudio.pyaudio as pyaudio
import data
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
        self.playing = False # The track currently playing (0-indexed)

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
        self.connect(
            self.tracklistTableWidget.verticalHeader(), SIGNAL('sectionPressed(int)'), self.playOrStopSelected)

        self.playButtonIcon = QIcon(QPixmap(data.path + '/' + 'media' + '/' + 'play.png'))
        self.stopButtonIcon = QIcon(QPixmap(data.path + '/' + 'media' + '/' + 'stop.png'))

        for track, title in enumerate(metadata['tracklist']):
            item = QTableWidgetItem(str(track + 1))
            item.setIcon(self.playButtonIcon)
            self.tracklistTableWidget.setVerticalHeaderItem(track, item)
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

    def playOrStopSelected(self, rowClicked):
        """
        Play the selected track's file using the default application for that file type.
        """
        rowStopped = self.stopAudio()        
        if rowStopped is rowClicked:
            return
        
        item = QTableWidgetItem(str(rowClicked + 1))
        item.setIcon(self.stopButtonIcon)
        self.tracklistTableWidget.setVerticalHeaderItem(rowClicked, item)

        audiofileObj = audiotools.open(self.metadata['audioFiles'][rowClicked])

        self.pyaudioObj = pyaudio.PyAudio()

        self.stream = self.pyaudioObj.open(
            format = pyaudio.paInt16,
            channels = audiofileObj.channels(),
            rate = audiofileObj.sample_rate(),
            output = True
        )

        self.playing = rowClicked
        self.playAudioThread = PlayAudioThread(self, audiofileObj, self.stream)
        self.connect(self.playAudioThread, SIGNAL('done()'), self.stopAudio)
        self.playAudioThread.start()

    def refreshTracks(self):
        """
        Reload the tracklist from the current contents of the "comments" field.
        """
        import parsetxt
        tracklist = parsetxt.TxtParser(unicode(self.commentsTextEdit.toPlainText()))._findTracklist()        
        
        for i in range(0, self.tracklistTableWidget.rowCount()):            
            if i < len(tracklist):
                self.tracklistTableWidget.setItem(i, 0, QTableWidgetItem(tracklist[i]))
            else:
                tracklist.append(' ')
                self.tracklistTableWidget.setItem(i, 0, QTableWidgetItem(u' '))

        self.metadata['tracklist'] = tracklist

    def stopAudio(self):
        """
        Stop currently playing audio, and set row icon back to the play button

        @return: The row stopped
        """
        rowStopped = False
        if hasattr(self, 'playAudioThread') and not self.playAudioThread.isStopped():                        
            self.playAudioThread.terminate()
        if self.playing is not False:
            rowStopped = self.playing
            item = QTableWidgetItem(str(self.playing + 1))
            item.setIcon(self.playButtonIcon)
            self.tracklistTableWidget.setVerticalHeaderItem(self.playing, item)
            self.playing = False
        return rowStopped

    def closeEvent(self, event):
        self.stopAudio()
        
class PlayAudioThread(QThread):
    def __init__(self, parent, audiofileObj, stream):
        self.parent = parent
        self.audiofileObj = audiofileObj
        self.stream = stream
        self.mutex = QMutex()
        self.stopped = False
        super(PlayAudioThread, self).__init__(parent)

    def run(self):
        self.audiofileObj.play_wave(self.stream)        
        self.stop()
        self.emit(SIGNAL('done()'))

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

    def isStopped(self):
        with QMutexLocker(self.mutex):
            return self.stopped