"""
Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""
from pydenticon import Pydenticon
from visicon import Visicon
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from settings import getSettings

class CoverArtRetriever():

    @staticmethod
    def getCoverImageChoices(metadata, no_pixmap=False):
        """
        Get the filenames of possible cover art found in the specified
        directory.  The default cover, as determined by settings, will appear
        first.  Results are a tuple of tuples, the first element of which is
        the filename, the second element of which is a QPixmap.

        If no_pixmap is set to True, will return a tuple of filenames only.

        @type  dir: QDir
        @param dir: The directory of the recording

        @type  metadata: dict
        @param metadata: Metadata for the recording

        @type no_pixmap: boolean
        @param no_pixmap: If True, will return a tuple of filenames only.

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
        identicon = Pydenticon(hash=hash, size=384)
        identiconPath = unicode(tempDirPath + '/' + 'identicon.png')
        identicon.save(identiconPath)
        
        visiconImage = Visicon(hash, 'seed', size=384)
        visiconPath = unicode(tempDirPath + '/' + 'visicon.png')
        visiconImage.draw_image().save(visiconPath, 'PNG')

        imageFiles = list(tempDir.entryList()) + list(dir.entryList())
        for subDir in subDirs:
            subDirQDir = QDir(dir.absolutePath() + '/' + subDir)
            subDirQDir.setNameFilters(nameFilters)
            subDirQDir.setFilter(QDir.Files)
            for imageFile in list(subDirQDir.entryList()):
                imageFiles.append(subDir + '/' + imageFile)

        optionsList = [
            unicode(tempDirPath + '/' + 'identicon.png'),
            unicode(tempDirPath + '/' + 'visicon.png'),
            u'No Cover Art'
        ]

        if no_pixmap:
            # A dummy list, to save from having to use a bunch of ifs
            pixMapList = [None, None, None]
        else:
            pixMapList = [
                QPixmap(optionsList[0]),
                QPixmap(optionsList[1]),
                None
            ]

        # Reverse order if Visicon is the preferred
        if getSettings()['defaultArt'] in ['Visicon', 'Image File => Visicon']:
            optionsList.insert(0, optionsList.pop(1))
            pixMapList.insert(0, pixMapList.pop(1))
        elif getSettings()['defaultArt'] in ['No Cover Art',
                                             'Image File => No Cover Art']:
            optionsList.insert(0, optionsList.pop(2))
            pixMapList.insert(0, pixMapList.pop(2))

        if 'Image File' in getSettings()['defaultArt']:
            for file in imageFiles:
                if file not in ['identicon.png', 'visicon.png']:
                    if not no_pixmap:
                        pixMapList.insert(
                            0,
                            QPixmap(unicode(dir.absolutePath() + '/' + file))
                        )
                    optionsList.insert(
                        0,
                        unicode(dir.absolutePath() + '/' + file)
                    )
        else:
            for file in imageFiles:
                if file not in ['identicon.png','visicon.png']:
                    if not no_pixmap:
                        pixMapList.append(
                            QPixmap(
                                unicode(dir.absolutePath() + '/' + file)
                            )
                        )
                    optionsList.append(
                        unicode(dir.absolutePath() + '/' + file)
                    )

        if no_pixmap:
            return tuple(optionsList[i] for i in range(len(optionsList)))
        else:
            return tuple(
                [(optionsList[i], pixMapList[i])
                for i in range(len(optionsList))]
            )