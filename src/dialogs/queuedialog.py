"""
The main dialog of the main window.

Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""
import re
import os
import shutil
import codecs
import hashlib
import chardet
import platform
import sys
import audiotools
import tracklint
from multiprocessing import Process
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui.ui_queuedialog import Ui_QueueDialog
from settings import getSettings
from parsetxt import TxtParser
from coverart import CoverArtRetriever
from dialogs.settingsdialog import SettingsDialog
from dialogs.confirmmetadata import ConfirmMetadataDialog
from dialogs.messagebox import MessageBox
import data

class QueueDialogError(Exception): pass
class LoadCanceledException(Exception): pass
class TracklintFixableError(Exception): pass

class QueueDialog(QDialog, Ui_QueueDialog):
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

    def convertAgainPrompt(self):
        """
        Display a message saying that the recording has already been
        converted and does the user wish to convert it again.  Return
        the response as a bool.

        @rtype: bool

        """
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle('BootTunes')
        msgBox.setText('This recording has already been converted.')
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
        self.loadingMultipleShows = False
        try:
            if isinstance(dirOrDirs, list):
                metadata = []
                self.loadingMultipleShows = True
                for dirName in dirOrDirs:
                    if dirName in self.queueItemData:
                        metadata = [
                            self.queueItemData[dirName]['metadata']
                        ]
                    else:
                        try:
                            ret = self.getMetadataFromDirAndSubDirs(dirName)
                        except:
                            continue
                        if isinstance(ret, dict):
                            metadata.append(ret)
                        else: # It's not a dict, so it must be a tuple
                            metadata += ret
                if len(metadata) == 1:
                    metadata = metadata[0]
                else:
                    metadata = tuple(metadata)
            else:
                dirName = dirOrDirs
                if dirName in self.queueItemData:
                    metadata = self.queueItemData[dirName]['metadata']
                else:
                    metadata = self.getMetadataFromDirAndSubDirs(dirName);
        except QueueDialogError as e:
            MessageBox.critical(
                self,
                "Add To Queue Error",
                e.args[0]
            )
        except LoadCanceledException:
            pass

        if isinstance(metadata, tuple):
            for metadatum in metadata:
                if not getSettings().isCompleted(metadatum['hash']):
                    self.addToQueue(metadatum)
            self.queueListWidget.sortItems()
        else:
            id3RepairInProgress = (
                hasattr(self, 'processThread')
                and not self.processThread.isStopped()
            )

            if id3RepairInProgress:
                return

            isCompleted = getSettings().isCompleted(metadata['hash'])
            
            if isCompleted:
                if self.convertAgainPrompt():
                    getSettings().removeCompleted(metadata['hash'])
                else:
                    return

            ConfirmMetadataDialog(metadata, self).exec_()

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
        SettingsDialog(self).exec_()

    def getMetadataFromDirAndSubDirs(self, dirName):
        """
        Search dirName and the first level of subdirectories for valid
        recordings.

        @type  dirName: QString
        @param dirName: Full path of the directory

        @rtype:  tuple or dict
        @return: A tuple of metadata dicts that may be passed to
        self.addToQueue(), or a single such dict.

        @raise QueueDialogError: Containing detailed error message if
        the dir contained a single recording.  A more general message
        for multiple subdirectories, which may all be invalid for
        different reasons.

        """
        try:
            return self.getMetadataFromDir(dirName)
        # If dir itself contained no recordings, check its subdirs
        except QueueDialogError as e: 
            qDir = QDir(dirName)
            qDir.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
            metadataList = []
            errorCount = 1            
            if qDir.entryList():
                # Display progress bar
                self.loadingMultipleShows = True
                progress = QProgressDialog(
                    "Loading",
                    "Cancel",
                    1,
                    len(qDir.entryList()), self
                )
                progress.setWindowTitle('BootTunes')
                progress.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
                progress.setWindowModality(Qt.WindowModal)

                for index, dir in enumerate(qDir.entryList()):                    
                    if progress.wasCanceled():
                        raise LoadCanceledException
                    absoluteDirPath = qDir.filePath(dir)
                    if absoluteDirPath in self.queueItemData:
                        metadataList.append(
                            self.queueItemData[absoluteDirPath]['metadata']
                        )
                    else:
                        try:
                            metadataList.append(
                                self.getMetadataFromDir(absoluteDirPath)
                            )
                        except QueueDialogError as e:
                            errorCount += 1
                    progress.setValue(index + 1)

            # If any valid recordings were found, simply ignore those
            # that weren't valid. Otherwise, display an error dialog.

            # If only one error, show that error.
            if len(metadataList) == 0 and errorCount == 1:
                raise e
            # Use generic message for multiple errors.
            elif len(metadataList) == 0 and errorCount > 1: 
                raise QueueDialogError("No valid recordings found")
            return tuple(metadataList)

    def getMetadataFromDir(self, dirName):
        """
        Search dirName for a txt file and supported audio files.  If found,
        return a tuple of parameters to be passed to self.addToQueue().  If
        not found, raises QueueDialogError.

        @type  dirName: QString
        @param dirName: Full path of the directory

        @rtype:  dict
        @return: Metadata suitable as a parameter for self.addToQueue()
        @raise QueueDialogError: For various errors.  Error message contained
        in first argument.

        """
        qDir = QDir(dirName)
        qDir.setNameFilters(['*.txt'])
        if not qDir.entryList():
            raise QueueDialogError(
                "No txt file found in the specified directory"
            )

        # If at least three fields not found (not counting comments, which
        # is set to the full contents of the file), and there are more txt
        # files, keep trying.
        for index, txtFile in enumerate(qDir.entryList()):
            isTheFinalTxt = (index == len(qDir.entryList()) - 1)            
            textFilePath = unicode(qDir.filePath(txtFile))
            try:                
                # Open file with open, detect the encoding, close it and open
                # again with codec.open
                fileHandle = open(textFilePath, 'r')                
                encoding = chardet.detect(fileHandle.read())['encoding']
                fileHandle.close()                
                # Try UTF-8 first. If there's an error, try the chardet
                # detected encoding. This seems to give the best results.
                fileHandle = codecs.open(textFilePath, 'r', 'utf-8')
                try:
                    fileHandle.read()
                    fileHandle.seek(0)
                except UnicodeDecodeError:
                    fileHandle = codecs.open(textFilePath, 'r', encoding)

                metadata = TxtParser(fileHandle.read()).parseTxt()                

                fileHandle.close()

                foundCount = 0
                for k, v in metadata.iteritems():
                    if v:
                        foundCount += 1
                if foundCount < 4 and not isTheFinalTxt:
                    continue

                # Must contain valid audio files
                validExtensions = ['*.flac', '*.shn', '*.m4a']                
                qDir.setNameFilters(validExtensions)
                
                filePaths = self._getFilePaths(qDir)
                filePaths = self._getSortedFiles(filePaths)
                filePaths = [
                    unicode(filePath) for filePath in filePaths
                ]
                
                if len(filePaths) == 0:
                    raise QueueDialogError(
                        "Directory does not contain any supported audio " +
                        "files (FLAC, SHN, ALAC)"
                    );

                if metadata['tracklist'] == None:
                    metadata['tracklist'] = ['' for x in filePaths]

                # Otherwise, leave titles for remaining files blank
                if (len(filePaths) > len(metadata['tracklist'])):
                    numOfBlankTracks = (
                        len(filePaths) - len(metadata['tracklist'])
                    )
                    for i in range(0, numOfBlankTracks):
                        metadata['tracklist'].append('')

                # If more tracks detected than files exist,
                # assume the extra tracks are an error
                del metadata['tracklist'][len(filePaths):]
                
                nonParsedMetadata = {}                
                
                nonParsedMetadata['audioFiles'] = filePaths                
                nonParsedMetadata['dir'] = qDir
                # Hash used for identicons and temp directory names
                nonParsedMetadata['hash'] = hashlib.md5(metadata['comments'] \
                    .encode('utf-8')).hexdigest()
                # The dir where all temp files for this show will be stored
                nonParsedMetadata['tempDir'] = QDir(
                    getSettings().settingsDir + '/' + nonParsedMetadata['hash']
                )
                if not nonParsedMetadata['tempDir'].exists():
                    nonParsedMetadata['tempDir'].mkpath(
                        nonParsedMetadata['tempDir'].absolutePath()
                    )
                
                try:
                    audioFile = audiotools.open(filePaths[0])
                    isBroken = isinstance(
                        audioFile,
                        tracklint.BrokenFlacAudio
                    )
                    if isBroken:
                        if self.loadingMultipleShows:
                            raise QueueDialogError(
                                'Malformed FLAC files.  ' +
                                'Load this show alone to fix.'
                            )
                        else:
                            metadata.update(nonParsedMetadata)
                            isCompleted = getSettings().isCompleted(metadata['hash'])
                            if isCompleted and not self.convertAgainPrompt():
                                return
                            self.fixBadFlacFiles(metadata)
                            if self.processThread.failed:
                                raise QueueDialogError(
                                    'Could not fix malformed FLAC files.'
                                )
                    else:
                        # Assume that an artist name found in the actual file
                        # metadata is more accurate unless that title is
                        # "Unknown Artist"
                        audioFileMetadata = audioFile.get_metadata()
                        artistFoundInFileMetadata = (
                            audioFileMetadata
                            and audioFileMetadata.artist_name
                            and audioFileMetadata.artist_name != \
                            'Unknown Artist'
                        )
                        if artistFoundInFileMetadata:
                            txtParser = TxtParser(metadata['comments'])
                            txtParser.artist = audioFileMetadata.artist_name
                            # Don't lose values added to tracklist
                            # since last parsing it
                            tracklist = metadata['tracklist']
                            metadata = txtParser.parseTxt()
                            metadata['tracklist'] = tracklist
                except audiotools.UnsupportedFile as e:
                    raise QueueDialogError(
                        os.path.basename(filePaths[0]) +
                        " is an unsupported file: "
                    )
                                
                nonParsedMetadata['cover'] = CoverArtRetriever \
                    .getCoverImageChoices(nonParsedMetadata)[0][0]

                metadata.update(nonParsedMetadata)                
                
                return metadata

            except IOError as e:                
                raise QueueDialogError(
                    "Could not read file: %s<br /><br />%s" % \
                    (txtFile, e.args[1])
                )
            except UnicodeDecodeError as e:
                raise QueueDialogError(
                    "Could not read file: %s<br /><br />%s" % \
                    (txtFile, e.args[4])
                )

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
        sortedFiles = []
        [sortedFiles.append('') for x in range(len(filePaths))]
        foundTrackNumbers = []
        for index, file in enumerate(filePaths):
            base = os.path.basename(unicode(file))
            path = os.path.dirname(unicode(file))
            match = re.search(
                '^(\d{1,2})([^\d].*)?$',
                base,
                re.IGNORECASE
            )
            if not match or match.group(1) in foundTrackNumbers:
                sortedFiles = filePaths
                break
            trackNum = int(match.group(1)) - 1
            if trackNum < len(sortedFiles):
                sortedFiles[int(match.group(1)) - 1] = QString(file)
                foundTrackNumbers.append(match.group(1))
        return sortedFiles

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
        with ReadLocker(self.lock):
            self.progressDialog.setValue(value + 1)
            if value < self.progressDialog.maximum():
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
            # in the conversion summary message
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
                    '\n\nThe followed tracks could not be converted:\n\n %s' %
                    '\n'.join(self.failedTracks)
                )
            MessageBox.information(
                self,
                'Complete',
                message
            )
            self.removeCompletedRecordings()

    def badFlacFixingComplete(self):
        """
        Called on completion of FixBadFlacsThread.
        
        """        
        ConfirmMetadataDialog(self.metadata, self).exec_()

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

    def fixBadFlacFiles(self, metadata):
        self.progressBarLabel = progressBarLabel = QLabel()
        self.progressDialog = progressDialog = QProgressDialog(
            "Loading",
            "Cancel",
            1,
            len(metadata['audioFiles']),
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
        progressBarLabel.setText('Temporarily removing ID3 tags')
        progressDialog.setValue(1)

        self.lock = QReadWriteLock()
        self.processThread = FixBadFlacsThread(self.lock, metadata, self)
        self.connect(
            self.processThread,
            SIGNAL("progress(int, QString)"),
            self.updateProgress
        )
        self.connect(
            self.processThread,
            SIGNAL("success()"),
            self.badFlacFixingComplete
        )
        self.connect(
            self.processThread,
            SIGNAL("error(QString)"),
            self.errorInThread
        )
        self.processThread.start()

class FixBadFlacsThread(QThread):
    """
    Fix invalid FLAC files.
    """
    def __init__(self, lock, metadata, parent):        
        super(FixBadFlacsThread, self).__init__(parent)
        parent.metadata = None
        self.lock = lock
        self.metadata = metadata
        self.failed = False
        self.stopped = False        
        self.completed = False

    def run(self):
        try:
            for index, audioFile in enumerate(self.metadata['audioFiles']):                
                audioObj = audiotools.open(audioFile)                
                if isinstance(audioObj, tracklint.BrokenFlacAudio):
                    tempFilePath = unicode(
                        self.metadata['tempDir'].absolutePath()
                    ) + u'/%d.flac' % index
                    if platform.system() == 'Darwin':
                        self.process = Process(
                            target=self.fixProcess,
                            args=(tempFilePath, audioObj)
                        )                        
                        self.process.start()                        
                        while self.process.is_alive() and not self.isStopped():
                            pass                        
                    else:
                        self.fixProcess(tempFilePath, audioObj)
                    self.metadata['audioFiles'][index] = (tempFilePath)
                if self.isStopped():
                    return
                self.emit(
                    SIGNAL("progress(int, QString)"),
                    index,
                    'Temporarily removing ID3 tags'
                )
            self.parent().metadata = self.metadata
            self.emit(SIGNAL("success()"))
        except Exception as e:            
            raise
        finally:
            self.completed = True
            self.stop()

    def fixProcess(self, tempFilePath, audioObj):
        audioObj.fix_id3_preserve_originals(tempFilePath)
        
    def stop(self):
        self.stopped = True
        if platform.system() == 'Darwin' \
                and hasattr(self, 'process') \
                and self.process.is_alive():
            self.process.terminate()

    def isStopped(self):
        return self.stopped

class ConvertFilesThread(QThread):
    """
    Convert all of the valid recordings in the queue to lossless
    m4a files and place them in the "Automatically Add To iTunes"
    directory.

    """
    def __init__(self, lock, parent):
        super(ConvertFilesThread, self).__init__(parent)
        self.lock = lock
        self.stopped = False
        self.mutex = QMutex()
        self.completed = False        

    def run(self):
        try:
            failed = []
            parent = self.parent()
            progressCounter = 0
            while progressCounter < parent.trackCount and not self.isStopped():
                currentRecording = parent.validRecordings[parent.currentRecording]
                metadata = currentRecording['metadata']

                if 'imageData' not in currentRecording:
                    if metadata['cover'] == 'No Cover Art':
                        currentRecording['imageData'] = None
                    else:
                        imageFile = open(metadata['cover'], 'rb')
                        currentRecording['imageData'] = imageFile.read()
                        imageFile.close()

                tempDirPath = metadata['tempDir'].absolutePath()

                filePath = metadata['audioFiles'][parent.currentTrack]
                self.currentFile = filePath

                extensionMatches = re.findall('\.([^.]+)$', filePath)
                self.extension = extensionMatches[0] \
                    if extensionMatches \
                    else ''

                if 'defaults' in metadata:
                    artistName = metadata['defaults']['preferred_name'] \
                        .decode('utf-8')
                    genre = metadata['defaults']['genre']
                else:
                    artistName = metadata['artist']
                    genre = ''

                parent.currentTrackName = metadata['tracklist'][parent.currentTrack]

                alacMetadata = audiotools.MetaData(
                    # if track name is empty iTunes will use the filename,
                    # which we don't want, so replace with a space
                    track_name   = parent.currentTrackName \
                        if parent.currentTrackName != '' \
                        else ' ',
                    track_number = parent.currentTrack + 1,
                    track_total  = len(metadata['tracklist']),
                    album_name   = metadata['albumTitle'],
                    artist_name  = artistName,
                    year         = unicode(metadata['date'].year),
                    date         = unicode(metadata['date'].isoformat()),
                    comment      = metadata['comments']
                )
                self.emit(
                    SIGNAL("progress(int, QString)"),
                    progressCounter,
                    'Converting "' + parent.currentTrackName + '"'
                )

                imageData = currentRecording['imageData']
                sourcePcm = currentRecording['pcmReaders'][parent.currentTrack]
                targetFile = tempDirPath + '/' \
                    + unicode(parent.currentTrack) + u'.m4a'
                
                args = [
                    targetFile,
                    sourcePcm,
                    alacMetadata,
                    genre,
                    imageData,                    
                ]
                # If on Mac, run as a separate process            
                if platform.system() == 'Darwin':
                    self.process = Process(
                        target=self.encodeProcess,
                        args=(args)
                    )
                    self.process.start()
                    while self.process.is_alive() and not self.isStopped():
                        pass                    
                else:
                    self.encodeProcess(*args)                
                if not os.path.exists(targetFile):                    
                    parent.failedTracks.append(self.currentFile)

                if self.isStopped():
                    return

                progressCounter += 1

                with ReadLocker(self.lock):
                    currentTrack = parent.currentTrack
                if (currentTrack + 1) > (len(metadata['tracklist']) - 1):
                    with WriteLocker(self.lock):
                        parent.currentTrack = 0
                    # Move files to addToITunesPath
                    metadata['tempDir'].setNameFilters(['*.m4a'])
                    QDir(
                        getSettings()['addToITunesPath']) \
                        .mkdir(metadata['hash']
                    )
                    for audioFile in metadata['tempDir'].entryList():
                        metadata['tempDir'].rename(
                            audioFile,
                            getSettings()['addToITunesPath'] + '/' \
                            + metadata['hash'] + '/' + audioFile
                        )
                    if not getSettings().isCompleted(metadata['hash']):
                        getSettings().addCompleted(metadata['hash'])
                    with WriteLocker(self.lock):
                        parent.currentRecording += 1
                else:
                    parent.currentTrack += 1

            self.emit(
                SIGNAL("progress(int, QString)"),
                progressCounter,
                'Finishing'
            )
        except Exception as e:
            self.failed = True
            self.emit(
                SIGNAL("error(QString)"),
                str(e)
            )                        
            raise # Re-raise so that it gets logged
        finally:
            self.completed = True
            self.emit(SIGNAL("success()"))
            self.stop()

    def encodeProcess(self, targetFile, sourcePcm,
                      alacMetadata, genre, imageData):
        """
        The actual m4a encoding process.

        @type targetFile: unicode
        @type sourcePcm: audiotool.PCMReader
        @type alacMetadata: audiotools.MetaData
        @type genre: unicode
        @type imageData: str        
        
        """
        try:
            if re.match('^m4a$', self.extension, re.IGNORECASE):
                shutil.copyfile(self.currentFile, targetFile)
                alacFile = audiotools.open(targetFile)
            else:
                alacFile = audiotools.ALACAudio.from_pcm(targetFile, sourcePcm)
        except:
            pass
        else:
            alacFile.set_metadata(alacMetadata)
            metadata = alacFile.get_metadata()
            # Set the "part of a compilation" flag to false
            metadata['cpil'] = metadata.text_atom(
                'data',
                '\x00\x00\x00\x15\x00\x00\x00\x00\x00'
            )
            metadata['\xa9gen'] = metadata.text_atom('\xa9gen', genre)
            alacFile.set_metadata(metadata)
            # Separately attempt to set the cover art,
            # since a MemoryError may occur in large files
            try:
                if imageData is not None:
                    metadata.add_image(
                        audiotools.Image.new(imageData, 'cover', 0)
                    )
                alacFile.set_metadata(metadata)
            except MemoryError:
                pass

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True
        if platform.system() == 'Darwin' \
                and hasattr(self, 'process') \
                and self.process.is_alive():
            self.process.terminate()

    def isStopped(self):
        with QMutexLocker(self.mutex):
            return self.stopped

class ReadLocker:
    """Context manager for QReadWriteLock::lockForRead()"""
    def __init__(self, lock):
        self.lock = lock
    def __enter__(self):
        self.lock.lockForRead()
    def __exit__(self, type, value, tb):
        self.lock.unlock()

class WriteLocker:
    """Context manager for QReadWriteLock::lockForWrite()"""
    def __init__(self, lock):
        self.lock = lock
    def __enter__(self):
        self.lock.lockForWrite()
    def __exit__(self, type, value, tb):
        self.lock.unlock()