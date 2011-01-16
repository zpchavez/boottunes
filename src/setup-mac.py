"""
This is a setup.py script generated by py2applet, but then tweaked to get it to work.

Usage:
    python setup-mac.py py2app
"""
import os
import shutil
import re
from setuptools import setup
from modulefinder import ModuleFinder

os.system("rm -rf dist")
os.system("rm -rf build")

thisPath = os.path.dirname(os.path.realpath(__file__))

NAME = 'BootTunes'
VERSION = '0.2.0'
APP = ['boottunes.pyw']
DATA_FILES = ['data']
OPTIONS = {
    'argv_emulation': False,
     'includes': ['sip', 'PyQt4.QtGui', 'PyQt4.QtCore'],
    'iconfile': 'data/media/logo.icns',
    'plist'   : {'CFBundleName': NAME,
                 'CFShortVersionString': VERSION,
                 'CFBundleGetInfoString': ' '.join([NAME, VERSION]),
                 'CFBundleExecutable': NAME,
                 'CFBundleIdentifier': 'com.chavezsoft.BootTunes'}
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

# Add to the system path the directory where the .so files are kept
file = open('dist/BootTunes.app/Contents/Resources/__boot__.py', 'r')
bootContents = file.read()
file = open('dist/BootTunes.app/Contents/Resources/__boot__.py', 'w')
file.write("""import os, sys \nsys.path = [os.path.join(
    os.environ['RESOURCEPATH'], 'lib', 'python2.6', 'lib-dynload')] + sys.path\n""" + bootContents
)
# Create qt.conf file to prevent "...loading two sets of Qt binaries..." error.
file = open('dist/boottunes.app/Contents/Resources/qt.conf', 'w')
file.write('[Paths]\nPrefix = .\nBinaries = .')

# Delete unneeded files
os.system("rm -f dist/BootTunes.app/Contents/Frameworks/QtCore.framework/Versions/4/QtCore_debug")
os.system("rm -f dist/BootTunes.app/Contents/Frameworks/QtGui.framework/Versions/4/QtGui_debug")

# py2app uses symlinks.  Replace these with the actual files, so that the same version of Python
# will be used regardless of the version installed on the user's system.

appPath = thisPath + '/dist/BootTunes.app/Contents'

os.system('rm ' + appPath + '/MacOS/python')
shutil.copy('/usr/bin/python', appPath + '/MacOS/python')
shutil.copy('/usr/bin/python2.6', appPath + '/MacOS/python2.6')
shutil.copytree(appPath + '/Resources/include', appPath + '/Resources/include2')
os.system('rm ' + appPath + '/Resources/include')
os.rename(appPath + '/Resources/include2', appPath + '/Resources/include')

# config dir symlink doesn't seem to be necessary, so delete it
os.system('rm ' + appPath + '/Resources/lib/python2.6/config')

# Also copy into the package all of the used module files.
finder = ModuleFinder()

finder.run_script('boottunes.pyw')

pythonFiles = []
cFiles = []

modulePath = '/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/'
cModulePath = '/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/lib-dynload'

for name, mod in finder.modules.iteritems():
    if mod.__file__:
        if re.search('^' + modulePath, mod.__file__):
            if mod.__file__ and re.search('\.so$', mod.__file__):
                cFiles.append(mod.__file__)
            elif mod.__file__:
                relPath = mod.__file__.replace(modulePath, '').replace('.py', '.pyc')
                pythonFiles.append(relPath)

cFiles.append(cModulePath + '/_multibytecodec.so')
cFiles.append(cModulePath + '/_codecs_cn.so')
cFiles.append(cModulePath + '/_codecs_hk.so')
cFiles.append(cModulePath + '/_codecs_iso2022.so')
cFiles.append(cModulePath + '/_codecs_jp.so')
cFiles.append(cModulePath + '/_codecs_kr.so')
cFiles.append(cModulePath + '/_codecs_tw.so')

for file in cFiles:
    shutil.copy(file, appPath + '/Resources/lib/python2.6/lib-dynload/' + os.path.basename(file))

# Encodings files are needed as well
pythonFiles.append('encodings/*.pyc')
os.system('cd /usr/lib/python2.6; zip -r ' + appPath + '/Resources/lib/python26.zip ' + ' '.join(pythonFiles))

# Need to copy JPEG and GIF plugins
os.mkdir(appPath + '/plugins')
os.mkdir(appPath + '/plugins/imageformats')
shutil.copy('/Developer/Applications/Qt/plugins/imageformats/libqgif.dylib', appPath + '/plugins/imageformats')
shutil.copy('/Developer/Applications/Qt/plugins/imageformats/libqjpeg.dylib', appPath + '/plugins/imageformats')
# Set the path to the Qt frameworks in the plugins
pluginPath = appPath + '/plugins/imageformats'
os.system(
    'install_name_tool -change QtGui.framework/Versions/4/QtGui ' +
    '@executable_path/../Frameworks/QtGui.framework/Versions/4/QtGui ' +
    pluginPath + '/libqjpeg.dylib'
)
os.system(
    'install_name_tool -change QtCore.framework/Versions/4/QtCore ' +
    '@executable_path/../Frameworks/QtCore.framework/Versions/4/QtCore ' +
    pluginPath + '/libqjpeg.dylib'
)
os.system(
    'install_name_tool -change QtGui.framework/Versions/4/QtGui ' +
    '@executable_path/../Frameworks/QtGui.framework/Versions/4/QtGui ' +
    pluginPath + '/libqgif.dylib'
)
os.system(
    'install_name_tool -change QtCore.framework/Versions/4/QtCore ' +
    '@executable_path/../Frameworks/QtCore.framework/Versions/4/QtCore ' +
    pluginPath + '/libqgif.dylib'
)