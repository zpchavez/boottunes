"""
The main dialog of the main window.

Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""
import re
import os
import codecs
import chardet
import platform
import sys
import audiotools
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui.ui_queuedialog import Ui_QueueDialog
from settings import getSettings
from dialogs.settingsdialog import SettingsDialog
from dialogs.confirmmetadata import ConfirmMetadataDialog
from dialogs.messagebox import MessageBox
from dialogs.threads.queuedialog import *
from dialogs.exceptions import \
    QueueDialogError, \
    LoadCanceledError, \
    TracklintFixableError
import data


class QueueDialog(QDialog, Ui_QueueDialog):
    """
    The main dialog of the app, showing the queue of selected shows
    to import.

    """

    def __init__(self):
        super(QueueDialog, self).__init__()
        self.setupUi(self)
        self.queueItemData = {}
        """holds dicts with keys 'item' containing the queueListWidgetItem,
           'metadata' containing the metadata dict, and 'valid', containing
           true if there is no missing metadata necessary to go ahead with
           the conversion.  Keys are the full path to the recording.
        """
        self.queueListWidget.setAcceptDrops(True)
        self.setAcceptDrops(True)
        self.queueListWidget.setIconSize(QSize(32, 32))

        def dragEnterEvent(self, event):
            if event.mimeData().urls():
                event.accept()
            else:
                event.ignore()
        
        def dropEvent(self, event):
            if event.mimeData().urls():
                regex = QRegExp('file://(/\w:)?')                
                dirList = [
                    url.toString().replace(regex, '') \
                    for url in event.mimeData().urls()
                ]
                if len(dirList) == 0:
                    event.ignore()
                else:
                    event.accept()
                    dirParam = dirList if len(dirList) > 1 else dirList[0]
                    self.parentWidget().loadDirContents(dirParam)
        setattr(
            self.queueListWidget.__class__,
            'dragMoveEvent',
            dragEnterEvent
        )
        setattr(
            self.queueListWidget.__class__,
            'dragEnterEvent',
            dragEnterEvent
        )
        setattr(self.queueListWidget.__class__, 'dropEvent', dropEvent)

    def convertAgainPrompt(self, name):
        """
        Display a message saying that the recording has already been
        converted and does the user wish to convert it again.  Return
        the response as a bool.

        @type name: unicode
        @param name: An identifier for the show (e.g. the directory name).

        @rtype: bool

        """
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle('BootTunes')
        msgBox.setText('%s has already been converted.' % name)
        msgBox.setInformativeText('Do you want to convert it again?')
        msgBox.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        msgBox.setDefaultButton(QMessageBox.Yes)
        choice = msgBox.exec_()
        return choice == QMessageBox.Yes

    def openFileDialog(self):
        """
        Open file dialog and handle the directory selected.

        """
        dirName = QFileDialog.getExistingDirectory(
            self,
            'Locate Directory',
            getSettings()['defaultFolder']
        )
        if dirName:
            # Set the directory above the chosen one as the new default
            qDir = QDir(dirName)
            qDir.cdUp()
            getSettings()['defaultFolder'] = qDir.absolutePath()

            self.loadDirContents(dirName)

    def loadDirContents(self, dirOrDirs):
        """
        Parse dirOrDirs for recordings.  If a single recording is found, open
        it in the confirm metadata dialog.  If multiple recordings are found,
        add them to the queue.  Display a message dialog if none could be
        added.

        @type dirName: QString or list of QStrings if multiple dirs are dragged
        and dropped

        """
        self.progressDialog = progressDialog = QProgressDialog(
            "Loading",
            "Cancel",
            1,
            2,
            self
        )
        self.connect(
            self.progressDialog,
            SIGNAL("canceled()"),
            self.cancelLoading
        )
        progressDialog.setWindowTitle('BootTunes')
        progressDialog.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        progressDialog.setWindowModality(Qt.WindowModal)
        progressDialog.setMinimumSize(QSize(300, 150))
        self.progressBarLabel = progressBarLabel = QLabel()
        progressBarLabel.setText('Loading Shows')
        progressDialog.setLabel(progressBarLabel)
        progressDialog.setValue(1)

        self.lock = QReadWriteLock()
        self.loadShowsThread = LoadShowsThread(self.lock, self, dirOrDirs)
        self.connect(
            self.loadShowsThread,
            SIGNAL("progress(int, QString)"),
            self.updateProgress
        )
        self.connect(
            self.loadShowsThread,
            SIGNAL("success()"),
            self.loadingComplete
        )
        self.connect(
            self.loadShowsThread,
            SIGNAL("error(QString)"),
            self.errorInThread
        )
        self.loadShowsThread.start()        

    def openConfirmMetadata(self, item):
        """
        Open ConfirmMetadataDialog for the specified item

        @type  item: QListWidgetItem
        @param item: The item whose metadata will be passed to the dialog

        """
        # 32 is the start of user-space
        indexOfSavedData = item.data(32).toString() 
        data = self.queueItemData[indexOfSavedData]['metadata']
        ConfirmMetadataDialog(data, self).exec_()
        self.queueListWidget.sortItems()

    def openSettingsDialog(self):
        """
        Open the settings dialog.

        """
        SettingsDialog(self).exec_()

    def loadingComplete(self):
        """
        Called when the LoadShowsThread has completed.
        If a single show is loaded, will bring up the confirm metadata
        dialog.  If multiple shows loaded, will add them to the queue.

        """
        # Single show
        if hasattr(self, 'metadata') and self.metadata:            
            isCompleted = getSettings().isCompleted(self.metadata['hash'])            
            if isCompleted:
                basename = os.path.basename(
                    unicode(self.metadata['dir'].absolutePath())
                )
                if self.convertAgainPrompt(basename):
                    getSettings().removeCompleted(self.metadata['hash'])
                else:
                    return
            ConfirmMetadataDialog(self.metadata, self).exec_()
        # Multiple shows
        elif hasattr(self, 'metadataList') and self.metadataList:
            for metadata in self.metadataList:                
                isCompleted = getSettings().isCompleted(metadata['hash'])
                if isCompleted:
                    basename = os.path.basename(
                        unicode(metadata['dir'].absolutePath())
                    )
                    if self.convertAgainPrompt(basename):
                        getSettings().removeCompleted(metadata['hash'])
                    else:
                        continue
                self.addToQueue(metadata)

    def _openFileOfUnknownEncoding(self, filePath):
        """
        Open a file whose encoding is unknown, assuming UTF-8 at first
        and attempting to detect the encoding if that fails.  Return
        the file handle.

        @type filePath: unicode
        @param filePath: The path to the text file.

        @rtype: file
        @return: The file handle.

        """
        # Open file with open, detect the encoding, close it and open
        # again with codec.open
        fileHandle = open(filePath, 'r')
        encoding = chardet.detect(fileHandle.read())['encoding']
        fileHandle.close()
        # Try UTF-8 first. If there's an error, try the chardet
        # detected encoding. This seems to give the best results.
        fileHandle = codecs.open(filePath, 'r', 'utf-8')
        try:
            fileHandle.read()
            fileHandle.seek(0)
        except UnicodeDecodeError:
            fileHandle = codecs.open(filePath, 'r', encoding)
        return fileHandle

    def _getFilePaths(self, qDir):
        """
        Get a list of QStrings for every audio file in the specified folder.
        If the audio files are split up between folders, e.g. CD1 and CD2,
        get files from the subdirectories as well.

        @type qDir: QDir

        """        
        filePaths = []
        for file in qDir.entryList():
            filePaths.append(qDir.filePath(file))
        
        if len(filePaths) == 0:
            validExtensions = qDir.nameFilters()
            qDir.setNameFilters('*')
            qDir.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
            for subdirStr in qDir.entryList():
                qSubdir = QDir(qDir.filePath(subdirStr))
                qSubdir.setNameFilters(validExtensions)
                for file in qSubdir.entryList():
                    filePaths.append(
                        qSubdir.filePath(file)
                    )
        return filePaths

    def _getSortedFiles(self, filePaths):
        """
        Sort files in the correct order.

        If the single digits tracks are numbered like 1, 2, 3
        instead of 01, 02, 03, make sure they are sorted correctly,
        so that track 10 does not follow track 1, etc.

        @type filesPaths: list
        @param filesPaths: A list of QStrings

        @rtype:  list
        @return: the sorted list

        """
        sortedFilePaths = []
        sortDict = {} # Will be sorted by the keys
        for index, file in enumerate(filePaths):
            base = os.path.basename(unicode(file))
            path = os.path.dirname(unicode(file))
            if re.match('\d{1}\D', base):
                sortDict[unicode(path + '/0' + base)] = file
            else:
                sortDict[unicode(file)] = file        
        for key in sorted(sortDict.iterkeys()):
            sortedFilePaths.append(sortDict[key])
        return sortedFilePaths

    def removeSelectedItem(self):
        """
        Remove the item or items currently highlighted in the queue list widget.

        """
        for item in self.queueListWidget.selectedItems():
            self.queueListWidget.takeItem(self.queueListWidget.row(item))
            del self.queueItemData[item.data(32).toString()]

    def refreshQueue(self):
        """
        Reload all items in the queue using the current settings

        """
        for dir, itemData in self.queueItemData.iteritems():
            self.addToQueue(itemData['metadata'])

    def addToQueue(self, metadata):
        """
        Add item to the queue if it is new, otherwise update it.

        @type  dir: QDir
        @param dir: The directory with the audio files and txt file

        @type  metadata: dict
        @param metadata: The metadata for the recording

        @type  imagePath: string
        @param imagePath: the full path to the cover art image

        """
        detectedArtist = metadata['artist']

        defaults = getSettings().getArtistDefaults(detectedArtist)        
        if defaults:
            metadata['defaults'] = defaults

        path = metadata['dir'].absolutePath()

        artistName = metadata['defaults']['preferred_name'] \
            if 'defaults' in metadata \
            else metadata['artist']
        if isinstance(artistName, str):
            artistName = artistName.decode('utf=8')

        if path in self.queueItemData:
            listItem = self.queueItemData[path]['item']
        else:
            listItem = QListWidgetItem()
            self.queueListWidget.addItem(listItem)
        if metadata['cover'] == 'No Cover Art':
            noCoverArt = QPixmap(
                data.path + '/' + 'media' + '/' + 'no-cover.png'
            )
            icon = QIcon(noCoverArt)
        else:
            icon = QIcon(QPixmap(metadata['cover']))
        listItem.setIcon(icon)
        self.queueItemData[path] = {
            'item': listItem,
            'metadata': metadata,
            'valid': True
        }
        listItem.setData(32, path)
        
        # If title is set, use that, otherwise follow the albumTitleFormat
        # in settings
        if 'title' in metadata and metadata['title'] != '':
            albumTitle = metadata['title']
        else:
            # If any parts of the title are blank, add a note and display
            # the item in red
            albumTitle = getSettings()['albumTitleFormat']
            for placeHolder in ['artist', 'venue', 'location', 'date']:
                match = re.search('\[' + placeHolder + '\]', albumTitle)
                if not match:
                    continue
                if placeHolder == 'date' and metadata['date'] != None:
                    replacement = metadata[placeHolder].strftime(
                        getSettings()['dateFormat']
                    )
                else:
                    placeHolder = "preferredArtist" \
                        if placeHolder == 'artist' \
                        else placeHolder
                    replacement = metadata[placeHolder]

                if replacement == '' or replacement == None:
                    self.queueItemData[path]['valid'] = False
                    albumTitle = albumTitle.replace(
                        '[' + placeHolder + ']',
                        '[missing ' + placeHolder + ']'
                    )
                else:
                    albumTitle = albumTitle.replace(
                        '[' + placeHolder + ']',
                        replacement
                    )

        if not artistName:
            artistName = '[missing artist]'
            self.queueItemData[path]['valid'] = False

        displayedTitle = albumTitle
        if self.queueItemData[path]['valid'] == False:
            listItem.setBackground(QBrush(QColor(255, 0, 0)))
            listItem.setForeground(QBrush(QColor(255, 255, 255)))
        else:            
            listItem.setForeground(QBrush(QColor(0, 0, 0)))
            if '' in set(metadata['tracklist']):
                displayedTitle += ' [contains untitled tracks]'
                listItem.setBackground(QBrush(QColor(255, 255, 0)))
            elif metadata['md5_mismatches'] != []:
                displayedTitle += (
                    ' [MD5 mismatch.  May contain corrupted files.]'
                )
                listItem.setBackground(QBrush(QColor(255, 255, 0)))
            else:                
                listItem.setBackground(QBrush(QColor(255, 255, 255)))

        listItem.setText(artistName + ' - ' + displayedTitle)        
        metadata['albumTitle'] = albumTitle

    def addToITunes(self):
        """
        Begin the conversion process of all the valid items in the queue.

        """
        self.validRecordings = []
        """A list containing the values from self.queueItemData, but only for
           recordings with all the required metadata"""
        self.currentRecording = 0
        """The index of self.validRecordings that is currently being converted
           and copied to iTunes"""
        self.currentTrack = 0
        """The track from the current recording currently being processed"""

        if not hasattr(self, 'antiCrashBin'):
            self.antiCrashBin = []
            """For reasons unknown, Windows 7 crashes when PCMReader objects
               go out of scope. My inelegant solution is to keep those objects
               in this antiCrashBin so that if the user converts multiple
               batches in one session the program won't crash.
            """        

        # Count all tracks for the progress bar and load recording
        # data into self.validRecordings in the order that the items
        # appear in the queue.        
        self.trackCount = 0
        [
            self.validRecordings.append(None)
            for x in range(len(self.queueItemData))
        ]
        for dir, data in self.queueItemData.iteritems():
            if data['valid'] == True:
                rowForItemInQueue = self.queueListWidget.row(data['item'])
                self.validRecordings[rowForItemInQueue] = data.copy()
                self.trackCount += len(data['metadata']['tracklist'])
        [
            self.validRecordings.remove(None)
            for x in range(self.validRecordings.count(None))
        ]
        
        self.failedTracks = []

        if len(self.validRecordings) == 0:
            MessageBox.warning(self, 'Notice', 'Nothing to add')
            return

        # Prepare a list of PcmReader objects
        for validRecording in self.validRecordings:
            validRecording['pcmReaders'] = []            
            audioFiles = validRecording['metadata']['audioFiles']            
            for index, audioFile in enumerate(audioFiles):
                try:
                    encoding = sys.getfilesystemencoding()
                    audiofileObj = audiotools.open(audioFile.encode(encoding))
                except audiotools.UnsupportedFile:
                    MessageBox.critical(
                        self,
                        'Error opening file',
                        '%s is an unsupported type' % \
                        os.path.basename(audioFile)
                    )
                    return
                except IOError as e:
                    MessageBox.critical(
                        self,
                        'Error opening file',
                        'Could not open file %s <br /><br /> %s ' % \
                        (os.path.basename(audioFile), e.args[1])
                    )
                    return
                except UnicodeDecodeError as e:
                    MessageBox.critical(
                        self,
                        'Error opening file',
                        'Unicode decode error <br /><br /> %s' % e.args[1]
                    )
                    return

                # If ALAC already, set the reader to None.
                if isinstance(audiofileObj, audiotools.ALACAudio):
                    validRecording['pcmReaders'].append(None)
                else:
                    try:
                        pcmReader = audiofileObj.to_pcm()
                    except Exception as e:
                        MessageBox.critical(
                            self,
                            'Error reading file',
                            'Could not read file: %s <br /><br /> %s' % \
                                (audioFile, str(e))
                        )
                        return
                    
                    if isinstance(pcmReader, audiotools.PCMReaderError):
                        MessageBox.critical(
                            self,
                            'Error reading file',
                            'Could not read file ' + os.path.basename(audioFile)
                            + "<br /><br />" + pcmReader.error_message
                        )
                        return
                    validRecording['pcmReaders'].append(pcmReader)
                    self.antiCrashBin.append(pcmReader)

        self.progressBarLabel = progressBarLabel = QLabel()
        self.progressDialog = progressDialog = QProgressDialog(
            "Loading",
            "Cancel",
            1,
            self.trackCount + 1,
            self
        )
        self.connect(
            self.progressDialog,
            SIGNAL("canceled()"),
            self.cancelProcess
        )
        progressDialog.setWindowTitle('BootTunes')
        progressDialog.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        progressDialog.setWindowModality(Qt.WindowModal)
        progressDialog.setLabel(progressBarLabel)
        progressBarLabel.setText(
            'Converting "%s"' % \
            self.validRecordings[0]['metadata']['tracklist'][0]
        )
        progressDialog.setValue(1)


        self.lock = QReadWriteLock()
        self.processThread = ConvertFilesThread(self.lock, self)
        self.connect(
            self.processThread,
            SIGNAL("progress(int, QString)"),
            self.updateProgress
        )
        self.connect(
            self.processThread,
            SIGNAL("success()"),
            self.conversionComplete
        )
        self.connect(
            self.processThread,
            SIGNAL("error(QString)"),
            self.errorInThread
        )
        self.processThread.start()

    def errorInThread(self, string):
        """
        Signaled if an exception is raised in a thread.
        
        """
        self.progressDialog.cancel()        
        MessageBox.critical(
            self,
            'Error',
            'Error encountered <br /><br />' + string
        )

    def updateProgress(self, value, text):
        """
        Updates the progress bar.  Slot for
        ProcessThread.SIGNAL(progress(int)).
        
        """
        if self.progressDialog.wasCanceled():
            return
        with ReadLocker(self.lock):            
            if value <= self.progressDialog.maximum():
                self.progressDialog.setValue(value)
                self.progressBarLabel.setText(
                    text
                )

    def conversionComplete(self):
        """
        Called on completion of ConvertFilesThread.
        
        """        
        if self.processThread.completed:
            soundPath = data.path + '/' + 'media' + '/' + 'complete.wav'
            QSound.play(soundPath)
            tracksCompleted = self.trackCount - len(self.failedTracks)
            recordingsCount = len(self.validRecordings)
            # Make the plurality of the words match the counts
            # in the conversion summary message.
            trackStr = 'track' if tracksCompleted == 1 else 'tracks'
            recordingStr = 'recording' \
                if len(self.validRecordings) == 1 \
                else 'recordings'
            message = (
                'Conversion complete\n\nConverted %d %s from %d %s.' %
                (tracksCompleted, trackStr, recordingsCount, recordingStr)
            )            
            if self.failedTracks:
                message += (
                    '\n\nThe following tracks could not be converted:\n\n %s' %
                    '\n'.join(self.failedTracks)
                )
            MessageBox.information(
                self,
                'Complete',
                message
            )
            self.removeCompletedRecordings()

    def removeCompletedRecordings(self):
        """
        Remove items that have been set as completed from the queue.

        """
        for recording in self.validRecordings:
            if getSettings().isCompleted(recording['metadata']['hash']):
                self.queueListWidget.takeItem(
                    self.queueListWidget.row(recording['item'])
                )
                key = recording['metadata']['dir'].absolutePath()
                del self.queueItemData[key]

    def cancelProcess(self):
        """
        Cancel the conversion process.  Called when "Cancel" is pressed
        in the progress bar dialog.
        
        """        
        self.processThread.stop()        
        if platform.system() != 'Darwin':
            self.processThread.terminate()
        if (hasattr(self, 'validRecordings')):
            self.removeCompletedRecordings()

    def cancelLoading(self):
        """
        Cancel the loading process.  Called when "Cancel" is pressed
        in the progress bar dialog.

        """                
        self.loadShowsThread.stop()
        if platform.system() != 'Darwin':
            self.loadShowsThread.terminate()        

    def event(self, event):
        """
        Map enter key to self.addToITunes()
        Other keys are mapped in MainWindow.event()
        """
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Enter, Qt.Key_Return):
                self.addToITunes()
            else:
                return QDialog.event(self, event)
            event.accept()
            return True
        return QDialog.event(self, event)