"""
Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""
import os
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from ui.ui_choosecover import Ui_ChooseCoverDialog
from coverart import CoverArtRetriever

class ChooseCoverDialog(QDialog, Ui_ChooseCoverDialog):

    def __init__(self, metadata, parent=None):
        """
        @type  metadata: dict
        @param metadata: The dict returned by QueueDialog.getMetadataFromDir()
        """
        super(ChooseCoverDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        self.metadata = metadata                
        self.coverImageChoices = CoverArtRetriever().getCoverImageChoices(metadata)

        for index, fileTuple in enumerate(self.coverImageChoices):
            self.chooseCoverComboBox.addItem(os.path.basename(fileTuple[0]), index)

    def chooseCover(self, index):
        """
        Slot for currentIndexChanges(int) on self.chooseCoverComboBox
        """        
        image = self.coverImageChoices[index][1]
        if not image:
            self.imageLabel.setPixmap(QPixmap())
        else:
            image = image.scaledToWidth(384)
            image = image.scaledToHeight(384)
            self.imageLabel.setPixmap(image)

    def accept(self):
        index = self.chooseCoverComboBox.currentIndex()
        self.metadata['cover'] = self.coverImageChoices[index][0]
        self.parentWidget().addToQueue(self.metadata)
        self.parentWidget().refreshQueue()        
        self.close()