"""
Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""
import sys
import os
import tempfile
import urllib2
import urllib
import json
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from dialogs.queuedialog import QueueDialog
from dialogs.messagebox import MessageBox
from dialogs.newversion import NewVersionDialog
from settings import getSettings, SettingsError
import data

__version__ = "0.2.5"

class MainWindow(QMainWindow):
    def __init__(self, parent=None):        
        super(MainWindow, self).__init__(parent)

        try:
            getSettings().initAddToITunesPath()
        except SettingsError:
            dir = QFileDialog.getExistingDirectory(
                None,
                'Please Locate your "Automatically Add to iTunes" folder'
            )
            if not dir:
                sys.exit()
            getSettings()['addToITunesPath'] = dir

        menuBar = QMenuBar()
        helpMenu = menuBar.addMenu('&Help')
        aboutAction = helpMenu.addAction('about')
        self.connect(aboutAction, SIGNAL("triggered()"), self.about)
        self.setMenuBar(menuBar)
        self.setWindowTitle('BootTunes')
        self.setCentralWidget(QueueDialog())

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
            <a href="http://people.csail.mit.edu/hubert/pyaudio/">PyAudio</a> and
            <a href="http://http://www.portaudio.com/">PortAudio</a> <br /><br />
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
            jsonString = urllib2.urlopen(
                'http://zacharychavez.com/boottunes/latest?version=' + __version__,
                timeout=3
            ).read()
            jsonDict = json.loads(jsonString)
            if jsonDict['version'] > __version__ and jsonDict['version'] != getSettings()['skipVersion']:
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

errorLogFilePath = getSettings().settingsDir + os.sep + 'errorlog.log'
sys.stderr = open(errorLogFilePath, 'w')

window = MainWindow()
window.show()

logoPixmap = QPixmap(data.path + '/' + 'media' + '/' + 'logo.png')
icon = QIcon(logoPixmap)
app.setWindowIcon(icon)

if getSettings()['checkForUpdates']:
    window.checkForUpdate()

app.exec_()

sys.stderr.close()
if (getSettings()['sendErrorReports'] and os.path.getsize(errorLogFilePath)):
    if sys.platform == 'win32':
        body = unicode(sys.getwindowsversion())
    elif sys.platform == 'darwin':
        sysInfo = os.uname()
        # Remove nodename
        sysInfo = list(sysInfo)
        del sysInfo[1]
        body = unicode(sysInfo)
    body += '\n\n' + 'BootTunes Version: ' + __version__
    body += ('\n\n' + open(errorLogFilePath, 'r').read())    
    queryDict = {'body': body}
    try:        
        urllib2.urlopen('http://zacharychavez.com/error-report.php?' + urllib.urlencode(queryDict))
    except:
        pass

getSettings().pickleAndStore()
getSettings().clearTempFiles()