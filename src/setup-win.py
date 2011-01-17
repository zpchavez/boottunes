"""
Usage:
    python setup-win.py py2exe
"""

from distutils.core import setup
import py2exe
import shutil
import os
os.system("rmdir dist /S /Q")
os.system("rmdir build /S /Q")

NAME = 'BootTunes'
VERSION = '0.2.0'

APP = ['boottunes.pyw']
DATA_FILES = [('data/media', [
                  'data/media/logo.png',
                  'data/media/play.png',
                  'data/media/stop.png',
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

# Copy QT plugins for displaying JPEG and GIF files
thisPath = os.path.dirname(os.path.realpath(__file__))
imageFormatsPath = thisPath + '/dist/imageFormats'

os.mkdir(imageFormatsPath)

shutil.copy(
    '/Python26/Lib/site-packages/PyQt4/plugins/imageformats/qjpeg4.dll',
    imageFormatsPath
)
shutil.copy(
    '/Python26/Lib/site-packages/PyQt4/plugins/imageformats/qgif4.dll',
    imageFormatsPath
)