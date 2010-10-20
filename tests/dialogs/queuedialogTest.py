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

    def setUp(self):
        self.settings = Settings('test')
        self.settings.settings.clear()
        self.settings.artist_defaults.clear()
        self.settings.artist_names.clear()
        self.settings.completed.clear()

        self.queuedialog = QueueDialog()

    def tearDown(self):
        settings.clearTempFiles()

    def testGetMetadataFromDirGetsMetadataFromTheSpecifiedDirectory(self):
        testPath = os.path.dirname(__file__)
        showPath = os.path.realpath(testPath + os.sep + '..') + os.sep + 'test-shows' + os.sep + 'show1'
        metadata = self.queuedialog.getMetadataFromDir(showPath)

        self.assertEquals('576ef998d942f9ce90395321d5ae01a5', metadata['hash'])
        expectedAudioFiles = [
            showPath + os.sep + '1.flac',
            showPath + os.sep + '2.flac',
            showPath + os.sep + '3.flac'
        ]
        expectedTempPath = settings.settingsDir + os.sep + metadata['hash']
        self.assertEquals(expectedAudioFiles, metadata['audioFiles'])
        self.assertEquals('The Foo Bars', metadata['artist'])
        self.assertEquals(expectedTempPath + os.sep + 'visicon.png', metadata['cover'])
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
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    unittest.main()
else:
    app = QApplication(sys.argv)