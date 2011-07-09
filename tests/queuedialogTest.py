# coding=utf-8
import os.path
import unittest
import os
import sys
import datetime
import shutil
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from dialogs.queuedialog import *
from settings import getSettings

class QueueDialogTestCase(unittest.TestCase):

    testPath = unicode(QDir.fromNativeSeparators(os.path.dirname(__file__)))
    showPath = testPath + u'/' + u'test-shows'

    def setUp(self):
        self.app = QApplication(sys.argv)
        self.settings = getSettings('test')
        self.settings.settings.clear()
        self.settings.artistDefaults.clear()
        self.settings.artistNames.clear()
        self.settings.completed.clear()
        self.settings['defaultArt'] = 'Visicon'

        self.queuedialog = QueueDialog()

    def tearDown(self):
        del self.app
        self.settings.clearTempFiles()

    def testGetMetadataFromDirGetsMetadataFromTheSpecifiedDirectory(self):
        showPath = self.showPath + '/' + 'show1'
        metadata = self.queuedialog.getMetadataFromDir(showPath)

        self.assertEquals('576ef998d942f9ce90395321d5ae01a5', metadata['hash'])
        expectedAudioFiles = [
            showPath + '/' + '1.flac',
            showPath + '/' + '2.flac',
            showPath + '/' + '3.flac'
        ]
        expectedTempPath = self.settings.settingsDir + '/' + metadata['hash']
        self.assertEquals(expectedAudioFiles, metadata['audioFiles'])
        self.assertEquals('The Foo Bars', metadata['artist'])
        self.assertEquals('Venue', metadata['venue'])
        self.assertEquals(datetime.date(1970, 7, 7), metadata['date'])
        self.assertEquals(
            'The Foo Bars\n1970-07-07\nThe Venue\nLondon\n\nDisc 1\n\n' +
            '01 Track 1\n02 Track 2\n03 Track 3',
            metadata['comments']
        )
        self.assertEquals('London, UK', metadata['location'])
        self.assertEquals(expectedTempPath, metadata['tempDir'] \
            .absolutePath())
        self.assertEquals(
            ['Track 1', 'Track 2', 'Track 3'],
            metadata['tracklist']
        )
        self.assertEquals(showPath, metadata['dir'].absolutePath())

    def testGetMetadataFromDirWorksWhenAudioFilesAreSplitUpInDiffFolders(self):
        showPath = self.showPath + '/' + 'show2'
        metadata = self.queuedialog.getMetadataFromDir(showPath)

        self.assertEquals('78a7e838cef92aec7c4cf189864c58c6', metadata['hash'])
        expectedAudioFiles = [
            showPath + '/' + 'CD1' + '/' + '1.shn',
            showPath + '/' + 'CD1' + '/' + '2.shn',
            showPath + '/' + 'CD2' + '/' + '1.shn',
            showPath + '/' + 'CD2' + '/' + '2.shn'
        ]
        expectedTempPath = self.settings.settingsDir + '/' + metadata['hash']
        self.assertEquals(expectedAudioFiles, metadata['audioFiles'])
        self.assertEquals('The Foo Bars', metadata['artist'])
        self.assertEquals('Venue', metadata['venue'])
        self.assertEquals(datetime.date(1970, 7, 8), metadata['date'])
        self.assertEquals(
            'The Foo Bars\n1970-07-08\nThe Venue\nLondon\n\nDisc 1\n\n'
            + '01 Track 1\n02 Track 2\n\nDisc 2\n\n01 Track 3\n02 Track 4',
            metadata['comments']
        )
        self.assertEquals('London, UK', metadata['location'])
        self.assertEquals(expectedTempPath, metadata['tempDir'].absolutePath())
        self.assertEquals(
            ['Track 1', 'Track 2', 'Track 3', 'Track 4'],
            metadata['tracklist']
        )
        self.assertEquals(showPath, metadata['dir'].absolutePath())

    def testIfMoreTracksInTextFileThanAudioFilesIgnoreExtras(self):
        """
        The extra tracks are probably something else
        being listed in the text file.

        """
        showPath = self.showPath + '/' + 'show3'
        metadata = self.queuedialog.getMetadataFromDir(showPath)

        self.assertEquals('082225a633ead0ce383409370ba1fec3', metadata['hash'])
        expectedAudioFiles = [
            showPath + '/' + '1.flac',
            showPath + '/' + '2.flac',
            showPath + '/' + '3.flac'
        ]
        expectedTempPath = self.settings.settingsDir + '/' + metadata['hash']
        self.assertEquals(expectedAudioFiles, metadata['audioFiles'])
        self.assertEquals('The Foo Bars', metadata['artist'])
        self.assertEquals('Venue', metadata['venue'])
        self.assertEquals(datetime.date(1970, 7, 7), metadata['date'])

        self.assertEquals('London, UK', metadata['location'])
        self.assertEquals(expectedTempPath, metadata['tempDir'].absolutePath())
        self.assertEquals(
            ['Track 1', 'Track 2', 'Track 3'],
            metadata['tracklist']
        )
        self.assertEquals(showPath, metadata['dir'].absolutePath())

    def testIfMoreAudioFilesThanTracksInTheTxtFileFillWithEmptyStrings(self):
        showPath = self.showPath + '/' + 'show4'
        metadata = self.queuedialog.getMetadataFromDir(showPath)
        self.assertEquals(3, len(metadata['tracklist']))
        self.assertEquals('', metadata['tracklist'][2])


    def testGetMetadataFromDirAndSubDirsFindsAllShowsInSubDirs(self):
        metadataTuple = self.queuedialog \
                            .getMetadataFromDirAndSubDirs(self.showPath)
        self.assertTrue(isinstance(metadataTuple, tuple))

    def testUmlautTest(self):
        """
        Umlauts in path names handled without error.

        """
        srcPath  = self.showPath + u'/show4/1.flac'
        destPath = self.showPath + u'/show5/ümlaüt.flac'
        shutil.copy(srcPath, destPath)
        metadata = self.queuedialog.getMetadataFromDir(
            self.showPath + '/show5'
        )
        # Just need to make sure that the saved string can be passed
        # to functions and work without error.
        self.assertEquals(os.path.exists(metadata['audioFiles'][0]), True)
        os.unlink(metadata['audioFiles'][0])
        self.assertEquals(os.path.exists(metadata['audioFiles'][0]), False)

    def testTracknamesWithNoLeadingZeroInTheTrackNumber(self):
        """
        Track names with no leading zero in the track number are sorted
        correctly, so that track 2 follows track 1, and not track 10

        """
        showPath = self.showPath + '/' + 'show6'
        metadata = self.queuedialog.getMetadataFromDir(showPath)        
        for i in range(1, 13):
            self.assertEquals('Track %d' % i, metadata['tracklist'][i - 1])
            self.assertEquals(
                showPath + '/%d.flac' % i,
                metadata['audioFiles'][i - 1]
            )

    def testTrackNumberedAsTrackZeroIsSortedCorrectly(self):
        """
        A regression test.

        """
        tracklist = ['00.Zeroth', '01.First', '02.Second', '03.Third']
        sorted = self.queuedialog._getSortedFiles(tracklist)
        self.assertEquals(sorted, tracklist)

    def testFailedMd5ChecksInMd5FileForASingleShow(self):
        """
        If a seperate .md5 file exists containing md5 hashes, its contents
        will be checked against the hashes of the audio files.  If any
        hashes don't match, the file paths will be noted in the metadata dict.

        """
        showPath = self.showPath + '/' + 'show7'
        metadata = self.queuedialog.getMetadataFromDir(showPath)
        self.assertEquals(
            metadata['md5_mismatches'],
            [showPath + '/3.flac']
        )

    def testFailedMd5ChecksForMultipleShows(self):
        """
        For multiple shows no dialog box appears, but tracks with hash
        mismatches appear in yellow.

        """
        pass

if __name__ == '__main__':    
    unittest.main()