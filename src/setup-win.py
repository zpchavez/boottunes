"""
Usage:
    python setup-win.py py2exe
"""

from distutils.core import setup
import py2exe
import os
os.system("rmdir dist /S /Q")
os.system("rmdir build /S /Q")

NAME = 'BootTunes'
VERSION = '1.0.0'

APP = ['boottunes.pyw']
DATA_FILES = [('data/media', [
                  'data/media/logo.png',
                  'data/media/complete.wav']),
              ('data/json', [
                  'data/json/common-cities.json',
                  'data/json/countries.json',
                  'data/json/provinces.json',
                  'data/json/states.json'])]
OPTIONS = {
    'includes': ['sip', 'PyQt4.QtGui', 'PyQt4.QtCore']
}

setup(
    windows=[{'script'        : 'boottunes.pyw',
              'icon_resources': [(1, 'data/media/logo.ico')]}],
    data_files=DATA_FILES,
    options={'py2exe': OPTIONS}
)

# Need to add to the system path
#file = open('dist/BootTunes.app/Contents/Resources/__boot__.py', 'r')
#bootContents = file.read()
#file = open('dist/BootTunes.app/Contents/Resources/__boot__.py', 'w')
#file.write("""import os, sys \nsys.path = [os.path.join(
#    os.environ['RESOURCEPATH'], 'lib', 'python2.6', 'lib-dynload')] + sys.path\n""" + bootContents
#)
# Create empty qt.conf file to prevent "...loading two sets of Qt binaries..." error.
#open('dist/boottunes.app/Contents/Resources/qt.conf', 'w')
## Delete unneeded files
#os.system("rm -f dist/BootTunes.app/Contents/Frameworks/QtCore.framework/Versions/4/QtCore_debug")
#os.system("rm -f dist/BootTunes.app/Contents/Frameworks/QtGui.framework/Versions/4/QtGui_debug")