"""
Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""
import os
import cPickle
import codecs
from PyQt4.QtCore import QDir

class SettingsError(Exception): pass

class Settings:
    """
    Set and retrieve settings as if the instance were a dict.
    """

    defaults = {'albumTitleFormat' : '[date] - [location] - [venue]',
                'defaultFolder'    : '/',
                'dateFormat'       : '%Y-%m-%d',
                'defaultArt'       : 'Visicon',
                'checkForUpdates'  : True,
                'sendErrorReports' : True,
                'skipVersion'      : ''}

    def __getitem__(self, key):
        if key not in self.settings:
            return self.defaults[key] if key in self.defaults else None
        return self.settings[key]

    def __setitem__(self, key, item):
        if isinstance(item, str):
            self.settings[key] = unicode(item)
        else:
            self.settings[key] = item

    def __contains__(self, key):
        if key not in self.settings:
            return key in self.defaults
        return key in self.settings

    def __init__(self, file='settings'):
        """
        @type  file: string
        @param file: the prefix of the settings files used.  Used for testing.
        """
        userDir = QDir(os.path.expanduser('~'))

        userDir.cd('Application Data') or userDir.cd('AppData') or userDir.cd('Library')
        if not userDir.cd('BootTunes'):
            userDir.mkdir('BootTunes')
            userDir.cd('BootTunes')

        self.settingsDir = unicode(userDir.absolutePath())

        basePath = unicode(userDir.absolutePath())
        self.settingsPath  = settingsPath  = basePath + '/' + file + '-settings'
        self.defaultsPath  = defaultsPath  = basePath + '/' + file + '-defaults'
        self.namesPath     = namesPath     = basePath + '/' + file + '-names'
        self.completedPath = completedPath = basePath + '/' + file + '-completed'

        pathsAndProperties = [
            (settingsPath,  'settings'),
            (defaultsPath,  'artistDefaults'),
            (namesPath,     'artistNames'),
            (completedPath, 'completed')
        ]

        for pathAndProperty in pathsAndProperties:
            filePath = pathAndProperty[0]
            property = pathAndProperty[1]
            setattr(self, property, {})
            if os.path.exists(filePath):
                fileObj = codecs.open(filePath, 'r')
                try:
                    setattr(self, property, cPickle.load(fileObj) or {})
                except (cPickle.UnpicklingError, AttributeError, EOFError, ImportError, IndexError):
                    pass
                fileObj.close()

    def initAddToITunesPath(self):
        """
        Check that the "Automatically Add to iTunes" path is set and that the directory
        actually exists.  If it does not, check all the standard locations.

        Raises SettingsError if the folder isn't set and could not be found.
        """
        if 'addToITunesPath' not in self.settings or not os.path.exists(self.settings['addToITunesPath']):
            self.settings['addToITunesPath'] = self.getDetectedAddToITunesPath()

        if not self.settings['addToITunesPath']:
            raise SettingsError('Could not find Automatically Add to iTunes path')

    def getDetectedAddToITunesPath(self):
        """
        Check the usual locations for the Automatically Add to iTunes folder and return it
        if found, or None if not.

        @rtype: unicode
        """
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
                return unicode(possiblePath)
        return None

    def getArtistDefaults(self, artist):
        """
        @type  artist: unicode
        @param artist: The artist name, either preferred or non-preferred

        @rtype:  dict
        @return: A dict containing the preferred name as 'name' and other defaults,
            or None if not found.
        """

        artist = artist.encode('utf_8')

        defaultKeys = ['preferred_name', 'genre']

        if artist in self.artistNames:
            id = self.artistNames[artist]
            try:
                defaults = self.artistDefaults[id]
            except KeyError:
                # defaults file must have lost data somehow.
                return None
            for defaultKey in defaultKeys:
                if defaultKey not in defaults:
                    defaults[defaultKey] = ''
            return defaults
        return None

    def setArtistDefaults(self, name, defaults):
        """
        Update the artist defaults.

        @type  name: unicode
        @param name: The artist name, as originally found in the txt file

        @type  defaults: dict
        @param defaults: A dict of the defaults, including the following keys: 'preferred_name'.
                         The values are unicode strings.
        """
        if defaults['preferred_name'] == '':
            return

        name = name.encode('utf_8')
        defaults['preferred_name'] = defaults['preferred_name'].encode('utf_8')
        defaults['genre'] = defaults['genre'].encode('utf_8')

        if name in self.artistNames:
            id = self.artistNames[name]
            submittedPreferredName = defaults['preferred_name']
            try:
                existingPreferredName = self.artistDefaults[id]['preferred_name']
            except KeyError:                
                # File data must have been lost.
                self.artistDefaults[id] = {'preferred_name': submittedPreferredName}
                existingPreferredName = submittedPreferredName

            if name == existingPreferredName:
                self.artistDefaults[id] = defaults
                del self.artistNames[existingPreferredName]
                self.artistNames[name] = id
            elif submittedPreferredName not in self.artistNames:
                newId = len(self.artistDefaults)
                self.artistDefaults[newId] = defaults
                self.artistNames[name] = newId
                self.artistNames[submittedPreferredName] = newId
            else:
                self.artistNames[submittedPreferredName] = id
                self.artistNames[name] = id
                self.artistDefaults[id] = defaults
        else:
            if defaults['preferred_name'] in self.artistNames:
                id = self.artistNames[defaults['preferred_name']]
                self.artistDefaults[id] = defaults
            else:
                id = len(self.artistDefaults)
                self.artistDefaults[id] = defaults
            self.artistNames[name] = id
            self.artistNames[defaults['preferred_name']] = id

    def addCompleted(self, hash):
        """
        Add a hash to the list of converted recordings.

        @type hash: string
        """
        if 0 not in self.completed:
            self.completed[0] = []
        self.completed[0].append(hash)

    def isCompleted(self, hash):
        """
        Check if a recording has already been converted as identified by the md5 hash
        of the contents of its text file.

        @type hash: string
        """
        return 0 in self.completed and hash in self.completed[0]

    def removeCompleted(self, hash):
        """
        Remove a hash from the completed list.

        @type hash: string
        """
        if hash in self.completed[0]:
            self.completed[0].remove(hash)

    def pickleAndStore(self):
        """
        Pickle and save the settings
        """
        fileSettings = codecs.open(self.settingsPath, 'w', 'utf_8')
        fileDefaults = codecs.open(self.defaultsPath, 'w', 'utf_8')
        fileNames = codecs.open(self.namesPath, 'w', 'utf_8')
        fileCompleted = codecs.open(self.completedPath, 'w', 'utf_8')

        cPickle.dump(self.settings, fileSettings)
        cPickle.dump(self.artistDefaults, fileDefaults)
        cPickle.dump(self.artistNames, fileNames)
        cPickle.dump(self.completed, fileCompleted)

        fileSettings.close()
        fileDefaults.close()
        fileNames.close()
        fileCompleted.close()

    def clearTempFiles(self):
        """
        Clear the directories created for each recording added to the queue
        and the files they contain.
        """
        settingsQDir = QDir(self.settingsDir)
        settingsQDir.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
        for dir in settingsQDir.entryList():
            tempQDir = QDir(self.settingsDir + '/' + dir)
            tempQDir.setFilter(QDir.Files)
            for tempFile in tempQDir.entryList():
                tempQDir.remove(tempFile)
            settingsQDir.rmdir(self.settingsDir + '/' + dir)


def getSettings(file = 'settings'):
    """
    To share settings between modules, use this function
    instead of creating new instances of Settings.

    @type  file: string
    @param file: the prefix of the settings files used.  Used for testing.
                 This parameter will be ignored for all subsequent calls.
    """
    if not hasattr(getSettings, 'settings'):
        getSettings.settings = Settings(file)
    return getSettings.settings