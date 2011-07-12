"""
Thread for converting files to Apple Lossless.

Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import re
import os
import audiotools
import platform
import shutil
from multiprocessing import Process
from dialogs.threads import ReadLocker, WriteLocker
from settings import getSettings

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
                    progressCounter + 1,
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
                progressCounter + 1,
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
