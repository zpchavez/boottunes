import os.path
import unittest
import os
import sys
import datetime
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from dialogs.queuedialog import *
from settings import *

class QueueDialogTestCase(unittest.TestCase):

    testPath = unicode(QDir.fromNativeSeparators(os.path.dirname(__file__)))
    showPath = testPath + '/' + 'test-shows'

    def setUp(self):
        self.settings = Settings('test')
        self.settings.settings.clear()
        self.settings.artistDefaults.clear()
        self.settings.artistNames.clear()
        self.settings.completed.clear()

        self.queuedialog = QueueDialog()

    def tearDown(self):
        settings.clearTempFiles()

    def testGetMetadataFromDirGetsMetadataFromTheSpecifiedDirectory(self):
        showPath = self.showPath + '/' + 'show1'
        metadata = self.queuedialog.getMetadataFromDir(showPath)        

        self.assertEquals('576ef998d942f9ce90395321d5ae01a5', metadata['hash'])
        expectedAudioFiles = [
            showPath + '/' + '1.flac',
            showPath + '/' + '2.flac',
            showPath + '/' + '3.flac'
        ]
        expectedTempPath = settings.settingsDir + '/' + metadata['hash']
        self.assertEquals(expectedAudioFiles, metadata['audioFiles'])
        self.assertEquals('The Foo Bars', metadata['artist'])
        self.assertEquals(expectedTempPath + '/' + 'visicon.png', metadata['cover'])
        self.assertEquals('Venue', metadata['venue'])
        self.assertEquals(datetime.date(1970, 7, 7), metadata['date'])
        self.assertEquals(
            'The Foo Bars\n1970-07-07\nThe Venue\nLondon\n\nDisc 1\n\n01 Track 1\n02 Track 2\n03 Track 3',
            metadata['comments']
        )
        self.assertEquals('London, UK', metadata['location'])
        self.assertEquals(expectedTempPath, metadata['tempDir'].absolutePath())
        self.assertEquals(['Track 1', 'Track 2', 'Track 3'], metadata['tracklist'])
        self.assertEquals(showPath, metadata['dir'].absolutePath())

    def testGetMetadataFromDirWorksWhenAudioFilesAreSplitUpInSeparateSubFolders(self):
        showPath = self.showPath + '/' + 'show2'
        metadata = self.queuedialog.getMetadataFromDir(showPath)        

        self.assertEquals('78a7e838cef92aec7c4cf189864c58c6', metadata['hash'])
        expectedAudioFiles = [
            showPath + '/' + 'CD1' + '/' + '1.shn',
            showPath + '/' + 'CD1' + '/' + '2.shn',
            showPath + '/' + 'CD2' + '/' + '1.shn',
            showPath + '/' + 'CD2' + '/' + '2.shn'
        ]
        expectedTempPath = settings.settingsDir + '/' + metadata['hash']
        self.assertEquals(expectedAudioFiles, metadata['audioFiles'])
        self.assertEquals('The Foo Bars', metadata['artist'])
        self.assertEquals(expectedTempPath + '/' + 'visicon.png', metadata['cover'])
        self.assertEquals('Venue', metadata['venue'])
        self.assertEquals(datetime.date(1970, 7, 8), metadata['date'])
        self.assertEquals(
            'The Foo Bars\n1970-07-08\nThe Venue\nLondon\n\nDisc 1\n\n'
            + '01 Track 1\n02 Track 2\n\nDisc 2\n\n01 Track 3\n02 Track 4',
            metadata['comments']
        )
        self.assertEquals('London, UK', metadata['location'])
        self.assertEquals(expectedTempPath, metadata['tempDir'].absolutePath())
        self.assertEquals(['Track 1', 'Track 2', 'Track 3', 'Track 4'], metadata['tracklist'])
        self.assertEquals(showPath, metadata['dir'].absolutePath())

    def testIfMoreTracksCountedInTextFileThanThereAreAudioFilesIgnoreTheApparentExtraTracks(self):
        # The extra tracks are probably something else being listed in the text file
        showPath = self.showPath + '/' + 'show3'
        metadata = self.queuedialog.getMetadataFromDir(showPath)

        self.assertEquals('082225a633ead0ce383409370ba1fec3', metadata['hash'])
        expectedAudioFiles = [
            showPath + '/' + '1.flac',
            showPath + '/' + '2.flac',
            showPath + '/' + '3.flac'
        ]
        expectedTempPath = settings.settingsDir + '/' + metadata['hash']
        self.assertEquals(expectedAudioFiles, metadata['audioFiles'])
        self.assertEquals('The Foo Bars', metadata['artist'])
        self.assertEquals(expectedTempPath + '/' + 'visicon.png', metadata['cover'])
        self.assertEquals('Venue', metadata['venue'])
        self.assertEquals(datetime.date(1970, 7, 7), metadata['date'])

        self.assertEquals('London, UK', metadata['location'])
        self.assertEquals(expectedTempPath, metadata['tempDir'].absolutePath())
        self.assertEquals(['Track 1', 'Track 2', 'Track 3'], metadata['tracklist'])
        self.assertEquals(showPath, metadata['dir'].absolutePath())
        
    def testIfThereAreMoreAudioFilesThanThereAreTracksInTheTextFileRaiseQueueDialogError(self):
        showPath = self.showPath + '/' + 'show4'
        self.assertRaises(QueueDialogError, self.queuedialog.getMetadataFromDir, showPath)
        # Make sure the exception has the correct message
        try:
            self.queuedialog.getMetadataFromDir(showPath)
        except QueueDialogError as e:
            self.assertEquals(e[0], "Number of audio files does not match tracklist")

    def testGetMetadataFromDirAndSubDirsGetsMetadataForAllValidShowsInSubDirectoriesWithinTheTargetDir(self):
        metadataTuple = self.queuedialog.getMetadataFromDirAndSubDirs(self.showPath)        
        self.assertTrue(isinstance(metadataTuple, tuple))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    unittest.main()
else:
    app = QApplication(sys.argv)