"""
Some tests for the audiotools functions that BootTunes uses.
"""
import unittest
import os
import audiotools
from  PyQt4.QtCore import QDir

class AudiotoolsTestCase(unittest.TestCase):

    testPath = unicode(QDir.fromNativeSeparators(os.path.dirname(__file__)))
    showPath = testPath + '/' + 'test-shows'

    antiCrashBin = []
    """PCMReader objects going out of scope causes Windows 7 to crash, hence the antiCrashBin"""

    def tearDown(self):
        outputDir = QDir(self.testPath + '/output')
        outputDir.setNameFilters(['*.m4a'])
        for outputFile in outputDir.entryList():
            outputDir.remove(outputFile)            

    def testFlacConversion(self):
        audioFile = audiotools.open(self.showPath + '/show1/1.flac')
        pcmReader = audioFile.to_pcm()
        self.antiCrashBin.append(pcmReader)        
        alacFile = audiotools.ALACAudio.from_pcm(self.testPath + '/output/1.m4a', pcmReader)
        self.assertTrue(os.path.exists(self.testPath + '/output/1.m4a'))
        pass
    
    def testShnConversion(self):
        audioFile = audiotools.open(self.showPath + '/show2/CD1/1.shn')
        pcmReader = audioFile.to_pcm()
        self.antiCrashBin.append(pcmReader)
        alacFile = audiotools.ALACAudio.from_pcm(self.testPath + '/output/2.m4a')
        self.assertTrue(os.path.exists(self.testPath + '/output/2.m4a', pcmReader))
        pass
    
if __name__ == '__main__':
    unittest.main()