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
import urllib
import chardet
import platform
import audiotools
from multiprocessing import Process
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui.ui_queuedialog import Ui_QueueDialog
from settings import settings
from parsetxt import TxtParser
from coverart import CoverArtRetriever
from dialogs.settingsdialog import SettingsDialog
from dialogs.confirmmetadata import ConfirmMetadataDialog
from dialogs.messagebox import MessageBox
import data

class QueueDialogError(Exception): pass
class LoadCanceledException(Exception): pass

class QueueDialog(QDialog, Ui_QueueDialog):
    def __init__(self):
        super(QueueDialog, self).__init__()
        self.setupUi(self)
        self.queueItemData = {}
        """holds dicts with keys 'item' containing the queueListWidgetItem, 'metadata' containing the
           metadata dict, and 'valid', containing true if there is no missing metadata necessary to
           go ahead with the conversion.  Keys are the full path to the recording.
        """
        self.queueListWidget.setAcceptDrops(True)        
        self.setAcceptDrops(True)

        def dragEnterEvent(self, event):
            if event.mimeData().urls():
                event.accept()
            else:
                event.ignore()

        def dropEvent(self, event):            
            if event.mimeData().urls():                
                urlsString = '\n'.join([unicode(url.toString()) for url in event.mimeData().urls()])
                urlsString = re.sub('file://(/\w:)?', '', urlsString)
                dirList = urlsString.split('\n')
                # Remove trailing slashes from directories and non-directories from the list
                for i in range(len(dirList)):
                    if i >= len(dirList): break # Necessary because items may be removed
                    if not os.path.isdir(urllib.url2pathname(dirList[i])):
                        dirList.remove(dirList[i])
                    else:
                        dirList[i] = dirList[i].rstrip('/\\')
                if len(dirList) == 0:
                    event.ignore()
                else:
                    event.accept()
                    dirParam = dirList if len(dirList) > 1 else dirList[0]
                    self.parentWidget().loadDirContents(dirParam)
        setattr(self.queueListWidget.__class__, 'dragMoveEvent', dragEnterEvent)
        setattr(self.queueListWidget.__class__, 'dragEnterEvent', dragEnterEvent)
        setattr(self.queueListWidget.__class__, 'dropEvent', dropEvent)

    def openFileDialog(self):
        """
        Open file dialog and handle the directory selected.
        """        
        dirName = QFileDialog.getExistingDirectory(self, 'Locate Directory', settings['defaultFolder'])
        if dirName:
            # Set the directory above the chosen one as the new default
            qDir = QDir(dirName)
            qDir.cdUp()
            settings['defaultFolder'] = qDir.absolutePath()
            self.loadDirContents(dirName)

    def loadDirContents(self, dirOrDirs):
        """
        Parse dirOrDirs for recordings.  If a single recording is found, open it in the confirm metadata dialog.
        If multiple recordings are found, add them to the queue.
        Display a message dialog if none could be added.

        @type dirName: string or list of strings if multiple dirs are dragged and dropped
        """
        try:
            if isinstance(dirOrDirs, list):                
                metadata = []
                for dir in dirOrDirs:
                    try:
                        ret = self.getMetadataFromDirAndSubDirs(QDir(dir))
                    except:
                        continue
                    if isinstance(ret, dict):
                        metadata.append(ret)
                    else:
                        metadata += ret
                if len(metadata) == 1:
                    metadata = metadata[0]
                else:
                    metadata = tuple(metadata)
            else:
                dir = dirOrDirs
                metadata = self.getMetadataFromDirAndSubDirs(QDir(dir));
            if isinstance(metadata, tuple):
                for metadatum in metadata:
                    if not settings.isCompleted(metadatum['hash']):
                        self.addToQueue(metadatum)
                self.queueListWidget.sortItems()
            else:
                if settings.isCompleted(metadata['hash']):
                    msgBox = QMessageBox(self)
                    msgBox.setText('This recording has already been converted.')
                    msgBox.setInformativeText('Do you want to convert it again?')
                    msgBox.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
                    msgBox.setDefaultButton(QMessageBox.Yes)
                    choice = msgBox.exec_()
                    if choice == QMessageBox.Yes:
                        settings.removeCompleted(metadata['hash'])
                    else:
                        return
                ConfirmMetadataDialog(metadata, self).exec_()
        except QueueDialogError as e:
            MessageBox.critical(
                self,
                "Add To Queue Error",
                e.args[0]
            )
        except LoadCanceledException:
            pass
        

    def openConfirmMetadata(self, item):
        """
        Open ConfirmMetadataDialog for the specified item

        @type  item: QListWidgetItem
        @param item: The item whose metadata will be passed to the dialog
        """
        indexOfSavedData = item.data(32).toString() # 32 is the start of user-space
        data = self.queueItemData[unicode(indexOfSavedData)]['metadata']
        ConfirmMetadataDialog(data, self).exec_()

    def openSettingsDialog(self):
        SettingsDialog(self).exec_()

    def getMetadataFromDirAndSubDirs(self, dirName):
        """
        Search dirName and the first level of subdirectories for valid recordings.

        @type  dirName: string
        @param dirName: Full path of the directory

        @rtype:  tuple or dict
        @return: A tuple of metadata dicts that may be passed to self.addToQueue(), or a single such dict.
        @raise QueueDialogError: Containing detailed error message if the dir contained a
               single recording.  A more general message for multiple subdirectories, which
               may all be invalid for different reasons.
        """
        try:
            return self.getMetadataFromDir(dirName)
        except QueueDialogError as e: # If dir itself contained no recordings, check its subdirs
            qDir = QDir(dirName)
            qDir.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
            metadataList = []
            errorCount = 1

            if qDir.entryList():
                # Display progress bar
                progress = QProgressDialog("Loading", "Cancel", 1, len(qDir.entryList()), self)
                progress.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
                progress.setWindowModality(Qt.WindowModal)

                for index, dir in enumerate(qDir.entryList()):
                    if progress.wasCanceled():
                        raise LoadCanceledException
                    try:
                        metadataList.append(self.getMetadataFromDir(qDir.absolutePath() + '/' + dir))
                    except QueueDialogError as e:
                        errorCount += 1
                    progress.setValue(index + 1)
            
            # If any valid recordings were found, simply ignore those that weren't valid.
            # Otherwise, display an error dialog.
            if len(metadataList) == 0 and errorCount == 1: # If only one error, show that error.
                raise e
            elif len(metadataList) == 0 and errorCount > 1: # Use generic message for multiple errors.
                raise QueueDialogError("No valid recordings found")
            return tuple(metadataList)
    
    def getMetadataFromDir(self, dirName):
        """
        Search dirName for a txt file and supported audio files.  If found, return a tuple of
        parameters to be passed to self.addToQueue().  If not found, raises QueueDialogError.

        @type  dirName: string
        @param dirName: Full path of the directory

        @rtype:  dict
        @return: Metadata suitable as a parameter for self.addToQueue()
        @raise QueueDialogError: For various errors.  Error message contained in first argument.
        """
        qDir = QDir(dirName)        
        qDir.setNameFilters(['*.txt'])
        if not qDir.entryList():
            raise QueueDialogError("No txt file found in the specified directory")                

        # If at least three fields not found (not counting comments, which is set to the full contents
        # of the file), and there are more txt files, keep trying.
        for index, txtFile in enumerate(qDir.entryList()):
            theFinalTxt = (index == len(qDir.entryList()) - 1)
            textFilePath = unicode(qDir.filePath(txtFile))
            try:
                # Open file with open, detect the encoding, close it and open again with codec.open
                fileHandle = open(textFilePath, 'r')                
                encoding = chardet.detect(fileHandle.read())['encoding']                                
                fileHandle.close()
                # Try UTF-8 first.  If there's an error, try the chardet detected encoding.
                # This seems to give the best results.
                fileHandle = codecs.open(textFilePath, 'r', 'utf_8')
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
                if foundCount < 4 and not theFinalTxt:
                    continue

                if metadata['tracklist'] == None:
                    raise QueueDialogError("Could not find a tracklist in " + txtFile)

                validExtensions = ['*.flac', '*.shn', '*.m4a']

                # Must contain valid audio files
                qDir.setNameFilters(validExtensions)
                filePaths = []
                for file in qDir.entryList():
                    fileNameEncoding = 'utf_8' if platform.system() == 'Darwin' else encoding
                    filePath = unicode(qDir.absolutePath() + '/' + file).encode(fileNameEncoding)                    
                    filePaths.append(filePath)
                # The show could be split up between folders, e.g. CD1 and CD2
                if len(filePaths) == 0:
                    qDir.setNameFilters('*')
                    qDir.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
                    for subdirStr in qDir.entryList():
                        qSubdir = QDir(qDir.absolutePath() + '/' + subdirStr)
                        qSubdir.setNameFilters(validExtensions)
                        for file in qSubdir.entryList():
                            filePaths.append(unicode(qSubdir.absolutePath()) + '/' + unicode(file))

                if len(filePaths) == 0:
                    raise QueueDialogError("Directory does not contain any supported audio files (FLAC, SHN, ALAC)");
                elif len(metadata['tracklist']) < len(filePaths):
                    raise QueueDialogError("Number of audio files does not match tracklist")

                # If more tracks detected than files exist, assume the extra tracks are an error
                del metadata['tracklist'][len(filePaths):]                

                metadata['audioFiles'] = filePaths

                try:
                    # Assume that an artist name found in the actual file metadata is more accurate
                    audioFile = audiotools.open(filePaths[0])                    
                    audioFileMetadata = audioFile.get_metadata()                    
                    if audioFileMetadata and audioFileMetadata.artist_name:
                        metadata['artist'] = audioFileMetadata.artist_name
                except audiotools.UnsupportedFile as e:
                    raise QueueDialogError(os.path.basename(filepaths[0]) + " is an unsupported file: ")

                metadata['dir'] = qDir
                # Hash used for identicons and temp directory names
                metadata['hash'] = hashlib.md5(metadata['comments'].encode('utf_8')).hexdigest()
                # The dir where all temporary files for this recording will be stored
                metadata['tempDir'] = QDir(settings.settingsDir + '/' + metadata['hash'])
                if not metadata['tempDir'].exists():
                    metadata['tempDir'].mkpath(metadata['tempDir'].absolutePath())
                metadata['cover'] = CoverArtRetriever.getCoverImageChoices(metadata)[0][0]                
                return metadata

            except IOError as e:
                raise QueueDialogError("Could not read file: " + txtFile + "<br /><br />" + e.args[1])
            except UnicodeDecodeError as e:
                raise QueueDialogError("Could not read file: " + txtFile + "<br /><br />" + e.args[4])

    def removeSelectedItem(self):
        """
        Remove the item or items currently highlighted in the queue list widget.
        """
        for item in self.queueListWidget.selectedItems():            
            self.queueListWidget.takeItem(self.queueListWidget.row(item))
            del self.queueItemData[unicode(item.data(32).toString())]

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

        defaults = settings.getArtistDefaults(detectedArtist)
        if defaults:
            metadata['defaults'] = defaults        

        path = unicode(metadata['dir'].absolutePath())

        artistName = metadata['defaults']['preferred_name'] if 'defaults' in metadata else metadata['artist']
        if isinstance(artistName, str):
            artistName = artistName.decode('utf-8')

        if path in self.queueItemData:
            listItem = self.queueItemData[path]['item']
        else:
            listItem = QListWidgetItem()
            self.queueListWidget.addItem(listItem)        
        icon = QIcon(CoverArtRetriever.imagePathToPixmap(metadata['cover']))        
        listItem.setIcon(icon)
        self.queueItemData[path] = {'item': listItem, 'metadata':metadata, 'valid':True}
        listItem.setData(32, path)        

        # If title is set, use that, otherwise follow the albumTitleFormat in settings
        if 'title' in metadata and metadata['title'] != '':
            albumTitle = metadata['title']
        else:
            # If any parts of the title are blank, add a note and display the item in red
            albumTitle = settings['albumTitleFormat']
            for placeHolder in ['artist', 'venue', 'location', 'date']:
                match = re.search('\[' + placeHolder + '\]', albumTitle)
                if match:
                    if placeHolder == 'date' and metadata['date'] != None:
                        replacement = metadata[placeHolder].strftime(settings['dateFormat'])
                    else:
                        placeHolder = "preferredArtist" if placeHolder == 'artist' else placeHolder
                        replacement = metadata[placeHolder]

                    if replacement == '' or replacement == None:
                        self.queueItemData[path]['valid'] = False
                        albumTitle = albumTitle.replace('[' + placeHolder + ']', '[missing ' + placeHolder + ']')
                    else:
                        albumTitle = albumTitle.replace('[' + placeHolder + ']', replacement)

        if not artistName:
            artistName = '[missing artist]'
            self.queueItemData[path]['valid'] = False

        listItem.setText(artistName + ' - ' + albumTitle)
        if self.queueItemData[path]['valid'] == False:
            listItem.setBackground(QBrush(QColor(255, 0, 0)))
        else:
            listItem.setBackground(QBrush(QColor(255, 255, 255)))
        metadata['albumTitle'] = albumTitle

    def addToITunes(self):
        """
        Begin the conversion process of all the valid items in the queue.
        """
        self.validRecordings = []
        """A list containing the values from self.queueItemData, but only for recordings with all the
           required metadata
        """
        self.currentRecording = 0
        """The index of self.validRecordings that is currently being converted and copied to iTunes"""
        self.currentTrack = 0
        """The track from the current recording currently being processed"""

        if not hasattr(self, 'antiCrashBin'):
            self.antiCrashBin = []
            """For reasons unknown, Windows 7 crashes when PCMReader objects go out of scope.
               My inelegant solution is to keep those objects in this antiCrashBin so that
               if the user converts multiple batches in one session the program won't crash.
            """

        # Count all tracks for the progress bar and load recording data into self.validRecordings
        # in the order that the items appear in the queue.
        trackCount = 0
        [self.validRecordings.append(None) for x in range(len(self.queueItemData))]
        for dir, data in self.queueItemData.iteritems():
            if data['valid'] == True:
                rowForItemInQueue = self.queueListWidget.row(data['item'])                
                self.validRecordings[rowForItemInQueue] = data.copy()
                trackCount += len(data['metadata']['tracklist'])
                self.trackCount = trackCount        
        [self.validRecordings.remove(None) for x in range(self.validRecordings.count(None))]

        if len(self.validRecordings) == 0:
            MessageBox.warning(self, 'Notice', 'Nothing to add')
            return        

        # Prepare a list of PcmReader objects
        for validRecording in self.validRecordings:
            validRecording['pcmReaders'] = []
            for audioFile in validRecording['metadata']['audioFiles']:
                try:
                    audiofileObj = audiotools.open(audioFile)
                except audiotools.UnsupportedFile:
                    MessageBox.critical(
                        self,
                        'Error opening file',
                        os.path.basename(audioFile) + ' is an unsupported type'
                    )
                    return
                except IOError as e:                    
                    MessageBox.critical(
                        self,
                        'Error opening file',
                        'Could not open file ' + os.path.basename(audioFile) + "<br /><br />" + e[1]
                    )
                    return
                # If ALAC already, set the reader to None.
                if isinstance(audiofileObj, audiotools.ALACAudio):                    
                    validRecording['pcmReaders'].append(None)
                else:
                    pcmReader = audiofileObj.to_pcm()
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
        self.progressDialog = progressDialog = QProgressDialog("Loading", "Cancel", 1, trackCount + 1, self)
        self.connect(self.progressDialog, SIGNAL("canceled()"), self.cancelProcess)
        progressDialog.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        progressDialog.setWindowModality(Qt.WindowModal)
        progressDialog.setLabel(progressBarLabel)
        progressBarLabel.setText('Converting "' + self.validRecordings[0]['metadata']['tracklist'][0] + '"')
        progressDialog.setValue(1)        


        self.lock = QReadWriteLock()
        self.processThread = ProcessThread(self.lock, self)
        self.connect(self.processThread, SIGNAL("progress(int)"), self.updateProgress)        
        self.connect(self.processThread, SIGNAL("finished()"), self.conversionComplete)
        self.processThread.start()

    def updateProgress(self, value):
        """
        Updates the progress bar.  Slot for ProcessThread.SIGNAL(progress(int)).
        """
        with ReadLocker(self.lock):            
            self.progressDialog.setValue(value + 1)
            if value < self.progressDialog.maximum():                
                self.progressBarLabel.setText(
                    'Converting "' + self.currentTrackName + '"'
                )

    def conversionComplete(self):
        """
        Called on completion of ProcessThread.
        """
        if self.processThread.completed:
            soundPath = data.path + '/' + 'media' + '/' + 'complete.wav'
            QSound.play(soundPath)
            # Make the plurality of the words match the counts in the conversion summary message
            trackStr = ' track' if self.trackCount == 1 else ' tracks'
            recordingStr = ' recording' if len(self.validRecordings) == 1 else ' recordings'
            MessageBox.information(
                self,
                'Complete',
                'Conversion complete\n\nConverted ' + str(self.trackCount) + trackStr + ' from ' \
                + str(len(self.validRecordings)) + recordingStr
            )
            self.removeCompletedRecordings()

    def removeCompletedRecordings(self):
        """
        Remove items that have been set as completed from the queue.
        """
        for recording in self.validRecordings:
            if settings.isCompleted(recording['metadata']['hash']):
                self.queueListWidget.takeItem(self.queueListWidget.row(recording['item']))
                key = unicode(recording['metadata']['dir'].absolutePath())
                del self.queueItemData[key]

    def cancelProcess(self):
        """
        Cancel the conversion process.  Called when "Cancel" is pressed in the progress bar dialog.
        """
        self.processThread.stop()
        if platform.system() != 'Darwin':
            self.processThread.terminate()
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

class ProcessThread(QThread):
    """
    Convert all of the valid recordings in the queue to lossless m4a files and place
    them in the "Automatically Add To iTunes" directory.    
    """
    def __init__(self, lock, parent):
        super(ProcessThread, self).__init__(parent)
        self.lock = lock
        self.stopped = False
        self.mutex = QMutex()
        self.completed = False

    def run(self):
        parent = self.parent()
        progressCounter = 0
        while progressCounter < parent.trackCount and not self.isStopped():
            currentRecording = parent.validRecordings[parent.currentRecording]
            metadata = currentRecording['metadata']

            if 'imageData' not in currentRecording:
                imageFile = open(metadata['cover'], 'rb')
                currentRecording['imageData'] = imageFile.read()
                imageFile.close()

            tempDirPath = metadata['tempDir'].absolutePath()

            filePath = metadata['audioFiles'][parent.currentTrack]
            self.currentFile = filePath

            extensionMatches = re.findall('\.([^.]+)$', filePath)
            self.extension = extensionMatches[0] if extensionMatches else ''

            if 'defaults' in metadata:
                artistName = metadata['defaults']['preferred_name'].decode('utf_8')
            else:
                artistName = metadata['artist']

            parent.currentTrackName = metadata['tracklist'][parent.currentTrack]

            alacMetadata = audiotools.MetaData(
                track_name   = parent.currentTrackName,
                track_number = parent.currentTrack + 1,
                track_total  = len(metadata['tracklist']),
                album_name   = metadata['albumTitle'],
                artist_name  = artistName,
                year         = unicode(metadata['date'].year),
                date         = unicode(metadata['date'].isoformat()),
                comment      = metadata['comments']
            )
            self.emit(SIGNAL("progress(int)"), progressCounter)

            alacMetadata.add_image(audiotools.Image.new(currentRecording['imageData'], 'cover', 0))            
            sourcePcm = currentRecording['pcmReaders'][parent.currentTrack]
            targetFile = tempDirPath + '/' + unicode(parent.currentTrack) + u'.m4a'

            # If on Mac, run as a separate process
            if platform.system() == 'Darwin':
                self.process = Process(target=self.encodeProcess, args=(targetFile, sourcePcm, alacMetadata))                
                self.process.start()                
                while self.process.is_alive() and not self.isStopped():
                    pass                
            else:
                self.encodeProcess(targetFile, sourcePcm, alacMetadata)
                
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
                QDir(settings['addToITunesPath']).mkdir(metadata['hash'])
                for audioFile in metadata['tempDir'].entryList():
                    metadata['tempDir'].rename(
                        audioFile,
                        settings['addToITunesPath'] + '/' + metadata['hash'] + '/' + audioFile
                    )
                if not settings.isCompleted(metadata['hash']):
                    settings.addCompleted(metadata['hash'])
                with WriteLocker(self.lock):
                    parent.currentRecording += 1
            else:
                parent.currentTrack += 1

        self.emit(SIGNAL("progress(int)"), progressCounter)
        self.completed = True
        self.emit(SIGNAL('finished'))
        self.stop()

    def encodeProcess(self, targetFile, sourcePcm, alacMetadata):
        """
        The actual m4a encoding process.

        @type targetFile: unicode
        @type sourcePcm: audiotool.PCMReader
        @type alacMetadata: audiotools.MetaData
        """
        if re.match('^m4a$', self.extension, re.IGNORECASE):
            shutil.copyfile(self.currentFile, targetFile)
            alacFile = audiotools.open(targetFile)            
        else:
            alacFile = audiotools.ALACAudio.from_pcm(targetFile, sourcePcm)
        alacFile.set_metadata(alacMetadata)
        # Set the "part of a compilation" flag to false
        metadata = alacFile.get_metadata()
        metadata['cpil'] = metadata.text_atom('data', '\x00\x00\x00\x15\x00\x00\x00\x00\x00')
        alacFile.set_metadata(metadata)

    def stop(self):        
        with QMutexLocker(self.mutex):
            self.stopped = True        
        if platform.system() == 'Darwin' and self.process.is_alive():
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