"""
Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""
import re
import os
import StringIO
import identicon
import visicon
from PIL import Image
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from settings import settings

class CoverArtRetriever():

    @staticmethod
    def imagePathToPixmap(imagePath):
        """
        Return a QPixmap given the path to a gif, png, or jpeg file.

        @type imagePath: unicode

        @rtype QPixmap
        """        
        # Workaround for loss of JPEG functionality when the app is packaged with py2app or py2exe.
        if re.search('/\.jpeg|\.jpg$', imagePath, re.IGNORECASE):
            image = Image.open(imagePath)
            stringIO = StringIO.StringIO()
            image.save(stringIO, format='png')            
            pixmap = QPixmap()
            pixmap.loadFromData(stringIO.getvalue())
            return pixmap
        else:
            pixmap = QPixmap(imagePath)
            return pixmap

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

        imageFiles = tempDir.entryList() + dir.entryList()
        
        pathList = [
            unicode(tempDirPath + '/' + 'identicon.png'),
            unicode(tempDirPath + '/' + 'visicon.png')
        ]
        pixMapList = [
            QPixmap(pathList[0]),
            QPixmap(pathList[1])
        ]
        if settings['defaultArt'] in ['Visicon', 'Image File => Visicon']:
            pixMapList.reverse()
            pathList.reverse()

        if 'Image File' in settings['defaultArt']:
            for file in imageFiles:
                if file not in ['identicon.png', 'visicon.png']:
                    pixMapList.insert(0, CoverArtRetriever.imagePathToPixmap(
                        unicode(dir.absolutePath() + '/' + file))
                    )
                    pathList.insert(0, unicode(dir.absolutePath() + '/' + file))
        else:
            for file in imageFiles:
                if file not in ['identicon.png','visicon.png']:
                    pixMapList.append(CoverArtRetriever.imagePathToPixmap(
                        unicode(dir.absolutePath() + '/' + file))
                    )
                    pathList.append(unicode(dir.absolutePath() + '/' + file))

        return tuple([(pathList[i], pixMapList[i]) for i in range(len(pathList))])