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

    defaults = {'albumTitleFormat': '[date] - [location] - [venue]',
                'defaultFolder'   : '/',
                'dateFormat'      : '%Y-%m-%d',
                'defaultArt'      : 'Visicon',
                'checkForUpdates' : True,
                'skipVersion'     : ''}
                
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
        userDir = QDir(os.path.expanduser('~'))

        userDir.cd('Application Data') or userDir.cd('AppData') or userDir.cd('Library')
        if not userDir.cd('BootTunes'):
            userDir.mkdir('BootTunes')
            userDir.cd('BootTunes')

        self.settingsDir = unicode(userDir.absolutePath())

        basePath = unicode(userDir.absolutePath())
        self.settingsPath = settingsPath = basePath + '/' + file + '-settings'
        self.defaultsPath = defaultsPath = basePath + '/' + file + '-defaults'
        self.namesPath = namesPath = basePath + '/' + file + '-names'
        self.completedPath = completedPath = basePath + '/' + file + '-completed'
            
        if os.path.exists(settingsPath):
            fileSettings = codecs.open(settingsPath, 'r')
            try:
                self.settings = cPickle.load(fileSettings) or {}
            except EOFError:
                self.settings = {}
            fileSettings.close()
        else:
            self.settings = {}

        if os.path.exists(defaultsPath):
            fileDefaults = codecs.open(defaultsPath, 'r')
            try:
                self.artist_defaults = cPickle.load(fileDefaults) or {}
            except EOFError:
                self.artist_defaults = {}
            fileDefaults.close()            
        else:
            self.artist_defaults = {}

        if os.path.exists(namesPath):
            fileNames = codecs.open(namesPath, 'r')
            try:
                self.artist_names = cPickle.load(fileNames) or {}
            except EOFError:
                self.artist_names = {}
            fileNames.close()
        else:
            self.artist_names = {}

        if os.path.exists(completedPath):
            completed = codecs.open(completedPath, 'r')
            try:
                self.completed = cPickle.load(completed) or {}
            except EOFError:
                self.completed = {}
            completed.close()            
        else:
            self.completed = {0:[]}

    def initAddToITunesPath(self):
        """
        Check that the "Automatically Add to iTunes" path is set and that the directory
        actually exists.  If it does not, check all the standard locations.

        Raises SettingsError if the folder isn't set and could not be found.

        """
        if 'addToITunesPath' not in self.settings or not os.path.exists(self.settings['addToITunesPath']):
            settings['addToITunesPath'] = self.getDetectedAddToITunesPath()

        if not self.settings['addToITunesPath']:
            raise SettingsError('Could not find Automatically Add to iTunes path')

    def getDetectedAddToITunesPath(self):
        """
        Check the usual locations for the Automatically Add to iTunes folder and return it
        if found, or None if not.

        @rtype: unicode
        """
        possibilities = [
            'Music' + '/' + 'iTunes' + '/' + 'iTunes Media',
            'Music' + '/' + 'iTunes' + '/' + 'iTunes Music',
            'My Documents' + '/' + 'My Music' + '/' + 'iTunes' + '/' + 'iTunes Media',
            'My Documents' + '/' + 'My Music' + '/' + 'iTunes' + '/' + 'iTunes Music'
        ]
        userDir = os.path.expanduser('~')
        for possibility in possibilities:
            possiblePath = userDir + '/' + possibility + '/' + 'Automatically Add to iTunes'
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

        if artist in self.artist_names:
            id = self.artist_names[artist]
            defaults = self.artist_defaults[id]
            defaults['preferred_name'] = defaults['preferred_name']            
            return self.artist_defaults[id]
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

        if name in self.artist_names:
            id = self.artist_names[name]
            submittedPreferredName = defaults['preferred_name']
            existingPreferredName = self.artist_defaults[id]['preferred_name']            

            if name == existingPreferredName:            
                self.artist_defaults[id] = defaults
                del self.artist_names[existingPreferredName]
                self.artist_names[name] = id
            elif submittedPreferredName not in self.artist_names:            
                newId = len(self.artist_defaults)
                self.artist_defaults[newId] = defaults
                self.artist_names[name] = newId
                self.artist_names[submittedPreferredName] = newId
            else:                
                self.artist_names[submittedPreferredName] = id
                self.artist_names[name] = id
                self.artist_defaults[id] = defaults
        else:            
            if defaults['preferred_name'] in self.artist_names:
                id = self.artist_names[defaults['preferred_name']]
                self.artist_defaults[id] = defaults
            else:
                id = len(self.artist_defaults)
                self.artist_defaults[id] = defaults
            self.artist_names[name] = id            
            self.artist_names[defaults['preferred_name']] = id

    def addCompleted(self, hash):
        """
        Add a hash to the list of converted recordings.

        @type hash: string
        """        
        self.completed[0].append(hash)        

    def isCompleted(self, hash):
        """
        Check if a recording has already been converted as identified by the md5 hash
        of the contents of its text file.

        @type hash: string
        """
        return hash in self.completed[0]        

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
        cPickle.dump(self.artist_defaults, fileDefaults)
        cPickle.dump(self.artist_names, fileNames)
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

settings = Settings()
"""To share settings between modules, use this instance instead of creating new instances of Settings"""