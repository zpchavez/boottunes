"""
Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""
import os
import identicon
import visicon
from PyQt4.QtCore import *
from settings import settings

class CoverArtRetriever():
    @staticmethod
    def getCoverImageChoices(metadata):
        """
        Get the filenames of possible cover art found in the specified
        directory.  The default cover, as determined by settings, will appear
        first.  Results are a tuple of tuples, the first element of which is
        the full path to the image, the second element of which is the file name
        by itself.

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
        identiconPath = unicode(tempDirPath + os.sep + 'identicon.png')
        identiconImage.save(identiconPath, 'PNG')

        visiconImage = visicon.Visicon(hash, 'seed', size=384)
        visiconPath = unicode(tempDirPath + os.sep + 'visicon.png')
        visiconImage.draw_image().save(visiconPath, 'PNG')

        imageFiles = tempDir.entryList() + dir.entryList()
        
        filenameList = [u'identicon.png', u'visicon.png']        
        pathList = [
            unicode(tempDirPath + os.sep + 'identicon.png'),
            unicode(tempDirPath + os.sep + 'visicon.png')
        ]        
        if settings['defaultArt'] in ['Visicon', 'Image File => Visicon']:
            filenameList.reverse()
            pathList.reverse()

        if 'Image File' in settings['defaultArt']:
            for file in imageFiles:
                if file not in ['identicon.png', 'visicon.png']:
                    filenameList.insert(0, unicode(file))
                    pathList.insert(0, unicode(dir.absolutePath() + os.sep + file))
        else:
            for file in imageFiles:
                if file not in ['identicon.png','visicon.png']:
                    filenameList.append(unicode(file))
                    pathList.append(unicode(dir.absolutePath() + os.sep + file))
        
        returnVal = tuple([(pathList[i], filenameList[i]) for i in range(len(pathList))])        
        return returnVal