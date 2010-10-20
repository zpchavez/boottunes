"""
Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""
import sys
import os
import tempfile
import urllib2
import json
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from dialogs.queuedialog import QueueDialog
from dialogs.messagebox import MessageBox
from dialogs.newversion import NewVersionDialog
from settings import settings
import data

__version__ = "0.1.2"

class MainWindow(QMainWindow):
    def __init__(self, parent=None):        
        super(MainWindow, self).__init__(parent)
        self.initAddToITunesPath()
        menuBar = QMenuBar()
        helpMenu = menuBar.addMenu('&Help')
        aboutAction = helpMenu.addAction('about')
        self.connect(aboutAction, SIGNAL("triggered()"), self.about)
        self.setMenuBar(menuBar)
        self.setWindowTitle('BootTunes')
        self.setCentralWidget(QueueDialog())

    def initAddToITunesPath(self):
        """
        Check that the "Automatically Add to iTunes" path is set and that the directory
        actually exists.  If it does not, check all the standard locations.  If still
        not found, prompt the user to locate it.
        """
        if 'addToITunesPath' not in settings or not os.path.exists(settings['addToITunesPath']):
            possibilities = [
                'Music' + os.sep + 'iTunes' + os.sep + 'iTunes Media',
                'Music' + os.sep + 'iTunes' + os.sep + 'iTunes Music',
                'My Documents' + os.sep + 'My Music' + os.sep + 'iTunes' + os.sep + 'iTunes Media',
                'My Documents' + os.sep + 'My Music' + os.sep + 'iTunes' + os.sep + 'iTunes Music'
            ]
            userDir = os.path.expanduser('~')
            for possibility in possibilities:
                possiblePath = userDir + os.sep + possibility + os.sep + 'Automatically Add to iTunes'
                if os.path.exists(possiblePath):
                    settings['addToITunesPath'] = possiblePath

        if 'addToITunesPath' not in settings or not os.path.exists(settings['addToITunesPath']):
            dir = QFileDialog.getExistingDirectory(
                None,
                'Please Locate your "Automatically Add to iTunes" folder'
            )
            if not dir:
                sys.exit()
            settings['addToITunesPath'] = dir

    def event(self, event):
        """
        Map minus key and backspace to QueueDialog.removeSelectedItem() and
        the plus key and spacebar to QueueDialog.openFileDialog()
        """
        if event.type() == QEvent.ShortcutOverride:
            if event.key() in (Qt.Key_Backspace, Qt.Key_Minus):
                self.centralWidget().removeSelectedItem()
            elif event.key() in (Qt.Key_Plus, Qt.Key_Space):
                self.centralWidget().openFileDialog()
            else:
                return QMainWindow.event(self, event)
            event.accept()
            return True
        return QMainWindow.event(self, event)

    def about(self):
        aboutContent = """BootTunes version: """ + __version__ + """ <br />
            <a href="http://code.google.com/p/boottunes">Project Page</a>
            <br /><br />
            Created by Zachary Chavez &lt;boottunes&#64;zacharychavez&#46;com&gt;<br />
            <hr />
            Acknowledgements <br /><br />
            The following open source tools were used in BootTunes. <br/><br />
            <a href="http://audiotools.sourceforge.net/">Python Audio Tools</a> <br /><br />
            <a href="http://www.riverbankcomputing.co.uk/software/pyqt/intro">PyQt</a> <br /><br />
            <a href="http://github.com/jsocol/identicon">Identicon</a> <br /><br />
            <a href="http://code.google.com/p/visicon">Visicon</a> <br /><br />
            <a href="http://www.pythonware.com/products/pil/">The Python Imaging Library (PIL)</a> <br />
            &copy; 1997-2006 by Secret Labs AB <br />
            &copy; 1995-2006 by Fredrik Lundh
        """
        MessageBox.general(self, 'About BootTunes', aboutContent)

    def checkForUpdate(self):
        try:
            jsonString = urllib2.urlopen('http://zacharychavez.com/boottunes/latest', timeout=3).read()            
            jsonDict = json.loads(jsonString)
            if jsonDict['version'] > __version__ and jsonDict['version'] != settings['skipVersion']:
                dialog = NewVersionDialog(jsonDict, parent=self)
                dialog.exec_()
        except:
            pass
        

class SingleInstance:
    """
    Prevent multiple instances of the application from being open at once.

    Posted by Sorin Sbarnea at:
    http://stackoverflow.com/questions/380870/python-single-instance-of-program
    """
    def __init__(self):
        import sys
        self.lockfile = os.path.normpath(tempfile.gettempdir() + '/' + os.path.basename(sys.argv[0]) + '.lock')
        if sys.platform == 'win32':
            try:
                # file already exists, we try to remove (in case previous execution was interrupted)
                if(os.path.exists(self.lockfile)):
                    os.unlink(self.lockfile)
                self.fd =  os.open(self.lockfile, os.O_CREAT|os.O_EXCL|os.O_RDWR)
            except OSError, e:
                if e.errno == 13:
                    print "Another instance is already running, quitting."
                    sys.exit(-1)
                print e.errno
                raise
        else: # non Windows
            import fcntl
            self.fp = open(self.lockfile, 'w')
            try:
                fcntl.lockf(self.fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                print "Another instance is already running, quitting."
                sys.exit(-1)

    def __del__(self):
        import sys
        if sys.platform == 'win32':
            if hasattr(self, 'fd'):
                os.close(self.fd)
                os.unlink(self.lockfile)

me = SingleInstance()

app = QApplication(sys.argv)
app.setOrganizationName('Zachary Chavez')
app.setOrganizationDomain('zacharychavez.com')
app.setApplicationName('BootTunes')

window = MainWindow()
window.show()

logoPixmap = QPixmap(data.path + os.sep + 'media' + os.sep + 'logo.png')
icon = QIcon(logoPixmap)
app.setWindowIcon(icon)

if settings['checkForUpdates']:
    window.checkForUpdate()

app.exec_()
settings.pickleAndStore()
settings.clearTempFiles()