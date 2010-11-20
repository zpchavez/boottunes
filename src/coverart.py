"""
Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""
import identicon
import visicon
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from settings import getSettings

class CoverArtRetriever():

    @staticmethod
    def getCoverImageChoices(metadata):
        """
        Get the filenames of possible cover art found in the specified
        directory.  The default cover, as determined by settings, will appear
        first.  Results are a tuple of tuples, the first element of which is
        the filename, the second element of which is a QPixmap.

        @type  dir: QDir
        @param dir: The directory of the recording

        @type  metadata: dict
        @param metadata: Metadata for the recording

        @rtype:  tuple
        @return: A tuple
        """
        dir = metadata['dir']
        tempDir = metadata['tempDir']
        tempDirPath = tempDir.absolutePath()

        dir.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
        dir.setNameFilters(['*'])
        subDirs = dir.entryList()

        nameFilters = ['*.gif', '*.png', '*.jpg', '*.jpeg']
        tempDir.setNameFilters(nameFilters)
        tempDir.setFilter(QDir.Files)
        dir.setNameFilters(nameFilters)
        dir.setFilter(QDir.Files)

        # Create identicon and visicon
        hash = metadata['hash']
        identiconImage = identicon.render_identicon(
            int(hash, 16),
            128
        )
        identiconPath = unicode(tempDirPath + '/' + 'identicon.png')
        identiconImage.save(identiconPath, 'PNG')

        visiconImage = visicon.Visicon(hash, 'seed', size=384)
        visiconPath = unicode(tempDirPath + '/' + 'visicon.png')
        visiconImage.draw_image().save(visiconPath, 'PNG')

        imageFiles = list(tempDir.entryList()) + list(dir.entryList())
        for subDir in subDirs:
            subDirQDir = QDir(dir.absolutePath() + '/' + subDir)
            subDirQDir.setNameFilters(nameFilters)
            subDirQDir.setFilter(QDir.Files)
            for imageFile in list(subDirQDir.entryList()):
                imageFiles.append(subDir + '/' + imageFile)

        pathList = [
            unicode(tempDirPath + '/' + 'identicon.png'),
            unicode(tempDirPath + '/' + 'visicon.png')
        ]
        pixMapList = [
            QPixmap(pathList[0]),
            QPixmap(pathList[1])
        ]
        if getSettings()['defaultArt'] in ['Visicon', 'Image File => Visicon']:
            pixMapList.reverse()
            pathList.reverse()

        if 'Image File' in getSettings()['defaultArt']:
            for file in imageFiles:
                if file not in ['identicon.png', 'visicon.png']:
                    pixMapList.insert(0, QPixmap(
                        unicode(dir.absolutePath() + '/' + file)
                    ))
                    pathList.insert(0, unicode(dir.absolutePath() + '/' + file))
        else:
            for file in imageFiles:
                if file not in ['identicon.png','visicon.png']:
                    pixMapList.append(QPixmap(
                        unicode(dir.absolutePath() + '/' + file)
                    ))
                    pathList.append(unicode(dir.absolutePath() + '/' + file))

        return tuple([(pathList[i], pixMapList[i]) for i in range(len(pathList))])