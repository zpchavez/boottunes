import unittest
import os
import sys
from hashlib import md5
from PyQt4.QtCore import QDir
from PyQt4.QtGui import *
from coverart import CoverArtRetriever
from settings import Settings

class CoverArtRetrieverTestCase(unittest.TestCase):

    testPath = unicode(QDir.fromNativeSeparators(os.path.dirname(__file__)))
    showPath = testPath + '/test-shows'
    outputPath = testPath + '/output'
    
    metadata = {'tempDir': QDir(outputPath), 'hash': md5('Any value here will do.').hexdigest()}
    """The value passed to the getCoverImageChoices method"""

    def setUp(self):
        self.settings = Settings("test")
        self.app = QApplication(sys.argv)

    def tearDown(self):
        del self.settings
        del self.metadata['dir']
        del self.app
        outputDir = QDir(self.outputPath)
        outputDir.setFilter(QDir.Files)
        for file in outputDir.entryList():
            filePath = unicode(self.outputPath + '/' + file)
            os.unlink(filePath)

    def testIfNoImageFilesForShowIdenticonChoicesWillBeAvailable(self):
        self.settings['defaultArt'] = 'Visicon'
        self.metadata['dir'] = QDir(self.showPath + '/show1')
        choices = CoverArtRetriever.getCoverImageChoices(self.metadata)
        print choices
        self.assertEquals(self.outputPath + '/visicon.png', choices[0][0])
        self.assertEquals(self.outputPath + '/identicon.png', choices[1][0])
        self.assertEquals(QPixmap(self.outputPath + '/visicon.png').cacheKey(), choices[0][1].cacheKey())
        self.assertEquals(QPixmap(self.outputPath + '/identicon.png').cacheKey(), choices[1][1].cacheKey())        

    def testImagesFoundInTopLevelDirectoryOfShow(self):
        self.settings['defaultArt'] = 'Image File => Visicon'
        self.metadata['dir'] = QDir(self.showPath + '/show2')
        choices = CoverArtRetriever.getCoverImageChoices(self.metadata)        
        self.assertEquals(self.showPath + '/show2/art.png', choices[0][0])
        self.assertEquals(self.showPath + '/show2/art.jpg', choices[1][0])
        self.assertEquals(self.showPath + '/show2/art.gif', choices[2][0])
        self.assertEquals(self.outputPath + '/visicon.png', choices[3][0])
        self.assertEquals(self.outputPath + '/identicon.png', choices[4][0])
        self.assertEquals(QPixmap(self.showPath + '/show2/art.png').cacheKey(), choices[0][1].cacheKey())
        self.assertEquals(QPixmap(self.showPath + '/show2/art.jpg').cacheKey(), choices[1][1].cacheKey())
        self.assertEquals(QPixmap(self.showPath + '/show2/art.gif').cacheKey(), choices[2][1].cacheKey())
        self.assertEquals(QPixmap(self.outputPath + '/visicon.png').cacheKey(), choices[3][1].cacheKey())
        self.assertEquals(QPixmap(self.outputPath + '/identicon.png').cacheKey(), choices[4][1].cacheKey())

    def testImagesFoundInSubFolders(self):
        self.settings['defaultArt'] = 'Image File => Visicon'
        self.metadata['dir'] = QDir(self.showPath + '/show3')
        choices = CoverArtRetriever.getCoverImageChoices(self.metadata)
        self.assertEquals(self.showPath + '/show3/artwork/art.png', choices[0][0])        
        self.assertEquals(self.outputPath + '/visicon.png', choices[1][0])
        self.assertEquals(self.outputPath + '/identicon.png', choices[2][0])
        self.assertEquals(QPixmap(self.showPath + '/show3/artwork/art.png').cacheKey(), choices[0][1].cacheKey())
        self.assertEquals(QPixmap(self.outputPath + '/visicon.png').cacheKey(), choices[1][1].cacheKey())
        self.assertEquals(QPixmap(self.outputPath + '/identicon.png').cacheKey(), choices[2][1].cacheKey())

if __name__ == '__main__':
    unittest.main()