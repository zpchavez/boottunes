"""
Thread for loading shows from a directory or list of directories.

Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from dialogs.exceptions import QueueDialogError
from settings import getSettings
from parsetxt import TxtParser
from coverart import CoverArtRetriever
import re
import os
import hashlib
import platform
import audiotools
import tracklint
from multiprocessing import Process

class LoadShowsThread(QThread):
    """
    Load shows.

    """

    def __init__(self, lock, parent, dirOrDirs):
        super(LoadShowsThread, self).__init__(parent)
        self.lock = lock
        self.stopped = False
        self.mutex = QMutex()
        self.completed = False
        self.dirOrDirs = dirOrDirs

    def run(self):        
        dirOrDirs = self.dirOrDirs
        parent = self.parent()

        if isinstance(dirOrDirs, list):
            dirs = dirOrDirs
        else:        
            try:                
                self.basename = os.path.basename(unicode(dirOrDirs))
                self.updateProgress('Loading %s' % self.basename, 1)
                metadata = self.getMetadataFromDir(dirOrDirs)
                self.updateProgress('Loading %s' % self.basename, 2)
                parent.metadata = metadata
                self.complete()
                return
            except QueueDialogError as e:
                qDir = QDir(dirOrDirs)
                qDir.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
                dirs = [
                    QDir(qDir.absoluteFilePath(dir)).absolutePath()
                    for dir in qDir.entryList()
                ]
                if not dirs:
                    self.fail(str(e))
                    return

        if hasattr(parent, 'progressDialog'):
            parent.progressDialog.setMaximum(len(dirs))

        errorCount   = 0
        metadataList = []
        for index, dir in enumerate(dirs):            
            self.basename = os.path.basename(unicode(dir))
            self.updateProgress('Loading %s' % self.basename, index)
            try:
                metadataList.append(self.getMetadataFromDir(dir))
            except QueueDialogError as e:
                errorCount += 1
                errorMsg = str(e)
            if self.stopped:
                return
            self.updateProgress('Loading %s' % self.basename, index + 1)

        # If only one error, show that error.
        if len(metadataList) == 0 and errorCount == 1:
            self.fail(errorMsg)
        # Use generic message for multiple errors.
        elif len(metadataList) == 0 and errorCount > 1:
            self.fail("No valid recordings found")

        parent.metadata     = None
        if self.stopped:
            parent.metadataList = None
        else:
            parent.metadataList = metadataList
        self.complete()

    def complete(self):
        """
        Stop process and sent a success signal.

        """        
        self.completed = True        
        self.emit(SIGNAL("success()"))        
        self.stop()        

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
        parent = self.parent()
        qDir = QDir(dirName)

        if getSettings()['verifyMd5Hashes']:
            md5s = self.getMd5s(qDir)
        else:
            md5s = []

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
                fileHandle = parent.openFileOfUnknownEncoding(textFilePath)

                txt      = fileHandle.read()
                metadata = TxtParser(txt).parseTxt()

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

                filePaths = parent.getFilePaths(qDir)
                filePaths = parent.getSortedFiles(filePaths)
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

                # Check for MD5 mismatches
                nonParsedMetadata['md5_mismatches'] = []
                tempDir = unicode(nonParsedMetadata['tempDir'].absolutePath())
                if md5s:
                    nonParsedMetadata['md5_mismatches'] = self.checkMd5s(
                        md5s,
                        filePaths
                    )

                try:
                    audioFile = audiotools.open(filePaths[0])
                    isBroken = isinstance(
                        audioFile,
                        tracklint.BrokenFlacAudio
                    )
                    if isBroken:
                        metadata.update(nonParsedMetadata)
                        self.fixBadFlacFiles(metadata)                        
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
                    .getCoverImageChoices(nonParsedMetadata, True)[0]

                metadata.update(nonParsedMetadata)

                if self.stopped:
                    return None
                else:
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

    def fixBadFlacFiles(self, metadata):
        """
        Fix FLAC files that are malformed because they contain ID3 tags.
        Replace the audioFile paths the metadata dict with the paths to
        temporary fixed versions.

        """
        parent = self.parent()        
        for index, audioFile in enumerate(metadata['audioFiles']):
            if self.stopped:
                return
            self.updateProgress(
                'Loading %s\n\nFixing malformed FLACs (%d\%d)'
                % (self.basename, index+1, len(metadata['audioFiles'])),
            )
            audioObj = audiotools.open(audioFile)            
            if isinstance(audioObj, tracklint.BrokenFlacAudio):
                tempFilePath = unicode(
                    metadata['tempDir'].absolutePath()
                ) + u'/%d.flac' % index
                if platform.system() == 'Darwin':                    
                    self.process = Process(
                        target=self.fixFlacProcess,
                        args=(tempFilePath, audioObj)
                    )
                    self.process.start()
                    while self.process.is_alive():
                        pass                    
                else:
                    self.fixFlacProcess(tempFilePath, audioObj)
                metadata['audioFiles'][index] = (tempFilePath)

    def fixFlacProcess(self, tempFilePath, audioObj):
        """
        Fix a malformed FLAC.

        """
        audioObj.fix_id3_preserve_originals(tempFilePath)

    def getMd5s(self, qDir):
        """
        Look for a .md5 file in qDir and if find return a list of the sums
        within.  Otherwise, return an empty list.

        @type qDir: QDir
        @param qDir: The directory containing the show.

        @rtype: list
        @returnL A list of MD5 sums.

        """
        parent = self.parent()
        qDir.setNameFilters(['*.md5'])
        if qDir.entryList():
            filePath = qDir.absolutePath() + '/' + qDir.entryList()[0]
            try:
                fileHandle = parent.openFileOfUnknownEncoding(filePath)
                txt = fileHandle.read()
                md5s = self.parseForMd5s(txt)
            except UnicodeDecodeError as e:
                # Getting hashes isn't essential, so just carry on.
                md5s = []
            finally:
                if 'fileHandle' in locals():
                    fileHandle.close()
        else:
            md5s = []
        return [md5.lower() for md5 in md5s]

    def checkMd5s(self, md5s, filePaths):
        """
        Check MD5s and return a list of file paths for the files whose hashes
        don't match.

        @type md5s: list
        @param md5s: A list of unicode objects.

        @type filePaths: list
        @param filePaths: A list of QStrings.

        """
        mismatches = []
        for index, expected in enumerate(md5s):            
            if self.stopped:
                return
            self.updateProgress(
                'Loading %s\n\nChecking MD5 hashes (%d\%d)'
                % (self.basename, index+1, len(md5s)),
            )
            if len(filePaths) < (index + 1):
                break
            audioFileAtIndex = filePaths[index]
            handle = open(
                audioFileAtIndex,
                'rb'
            )
            fileContent = handle.read()
            handle.close
            actual = hashlib.md5(fileContent).hexdigest()
            if expected.lower() != actual.lower():
                mismatches.append(audioFileAtIndex)
        return mismatches

    def parseForMd5s(self, txt):
        """
        Return a list of all the MD5 hashes found in the specified file.

        @type txt: unicode
        @param txt: The text to parse for MD5s

        """
        matches = re.findall(
            '^.*([0-9a-f]{32}).+\.(flac.*|shn.*)$',
            txt,
            re.IGNORECASE | re.MULTILINE
        )
        return [group[0] for group in matches]

    def stop(self):
        """
        Stop the thread from executing, as if it had been canceled.

        """        
        with QMutexLocker(self.mutex):
            self.stopped = True
        if platform.system() == 'Darwin' \
                and hasattr(self, 'process') \
                and self.process.is_alive():            
            self.process.terminate()            

    def fail(self, errorMsg):
        """
        Stop process and send back an error message.

        @type errorMsg: unicode

        """
        self.failed = True
        self.emit(
            SIGNAL("error(QString)"),
            str(errorMsg)
        )

    def updateProgress(self, text, value=None):
        """
        Update the text and optionally the value of the progress bar.

        @type text: unicode

        @type value: int

        """
        if not hasattr(self.parent(), 'progressDialog'):
            return
        if value is None:
            value = self.parent().progressDialog.value()
        self.emit(
            SIGNAL("progress(int, QString)"),
            value,
            text
        )