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
from settings import settings

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

        for fileTuple in CoverArtRetriever().getCoverImageChoices(metadata):
            self.chooseCoverComboBox.addItem(fileTuple[1], fileTuple[0])

    def chooseCover(self, index):
        """
        Slot for currentIndexChanges(int) on self.chooseCoverComboBox
        """
        imagePath = self.chooseCoverComboBox.itemData(index).toString()        
        image = QImage(imagePath).scaledToWidth(384)
        self.imageLabel.setPixmap(QPixmap.fromImage(image))

    def accept(self):
        index = self.chooseCoverComboBox.currentIndex()
        self.metadata['cover'] = unicode(self.chooseCoverComboBox.itemData(index).toString())        
        self.parentWidget().addToQueue(self.metadata)
        self.parentWidget().refreshQueue()        
        self.close()