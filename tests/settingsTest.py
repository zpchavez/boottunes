import unittest
import os
from settings import *

class SettingsTestCase(unittest.TestCase):

    def setUp(self):        
        self.settings = Settings("test")                
        self.settings.settings.clear()
        self.settings.artist_defaults.clear()
        self.settings.artist_names.clear()

    def tearDown(self):        
        del self.settings

    def testSetArtistDefaultsWhenNameAndPreferredNameBothNew(self):
        setDefaults = {'preferred_name': 'The Foo Bars', 'genre': 'Rock'}
        returnedDefaults = {'preferred_name': 'The Foo Bars', 'genre': 'Rock'}

        self.settings.setArtistDefaults('Foo Bars', setDefaults)

        self.assertEquals(returnedDefaults, self.settings.getArtistDefaults('Foo Bars'))
        self.assertEquals(returnedDefaults, self.settings.getArtistDefaults('The Foo Bars'))

    def testSetArtistDefaultsWhenNameNewAndPreferredNameExists(self):
        setDefaults = {'preferred_name': 'The Foo Bars', 'genre': 'Rock'}
        returnedDefaults = {'preferred_name': 'The Foo Bars', 'genre': 'Rock'}

        self.testSetArtistDefaultsWhenNameAndPreferredNameBothNew();

        self.settings.setArtistDefaults('Phoo Bars', setDefaults)

        self.assertEquals(returnedDefaults, self.settings.getArtistDefaults('Phoo Bars'))
        self.assertEquals(returnedDefaults, self.settings.getArtistDefaults('Foo Bars'))
        self.assertEquals(returnedDefaults, self.settings.getArtistDefaults('The Foo Bars'))

    def testSetArtistDefaultsWhenNameExistsAndPreferredNameNew(self):        
        setDefaults = {'preferred_name': 'The Foo Bazzes', 'genre': 'Rock'}
        returnedDefaults = {'preferred_name': 'The Foo Bazzes', 'genre': 'Rock'}

        self.testSetArtistDefaultsWhenNameAndPreferredNameBothNew();

        self.settings.setArtistDefaults('Foo Bars', setDefaults)

        self.assertEquals(returnedDefaults, self.settings.getArtistDefaults('Foo Bars'))
        # Previously preferred name still exists, but no longer connected to 'Foo Bars"
        self.assertEquals(
            {'genre': 'Rock', 'preferred_name': 'The Foo Bars'},
            self.settings.getArtistDefaults('The Foo Bars')
        )

    def testSetArtistDefaultsWhenNameExistsAndPreferredNameExists(self):
        self.testSetArtistDefaultsWhenNameAndPreferredNameBothNew();
        self.testSetArtistDefaultsWhenNameAndPreferredNameBothNew();

    def testANameMayReturnAPreferredNameThatDiffersOnlyInCase(self):
        setDefaults = {'preferred_name': 'The Foo Bars', 'genre': 'Rock'}
        returnedDefaults = {'preferred_name': 'The Foo Bars', 'genre': 'Rock'}

        self.settings.setArtistDefaults('THE FOO BARS', setDefaults)

        self.assertEquals(returnedDefaults, self.settings.getArtistDefaults('THE FOO BARS'))
        self.assertEquals(returnedDefaults, self.settings.getArtistDefaults('The Foo Bars'))

    def testMaySwitchThePreferredAndNonPreferred(self):
        self.testSetArtistDefaultsWhenNameAndPreferredNameBothNew()

        setDefaults = {'preferred_name': 'Foo Bars', 'genre': 'Rock'}
        returnedDefaults = {'preferred_name': 'Foo Bars', 'genre': 'Rock'}

        self.settings.setArtistDefaults('The Foo Bars', setDefaults)

        self.assertEquals(returnedDefaults, self.settings.getArtistDefaults('The Foo Bars'))

    def testIfNamePassedToSetArtistIsPreferredAlreadyThenThePreferredNameWillBeChanged(self):
        self.testSetArtistDefaultsWhenNameAndPreferredNameBothNew();

        setDefaults = {'preferred_name': 'The Fooo Bars', 'genre': 'Rock'}
        returnedDefaults = {'preferred_name': 'The Fooo Bars', 'genre': 'Rock'}

        self.settings.setArtistDefaults('The Foo Bars', setDefaults)

        self.assertEquals(returnedDefaults, self.settings.getArtistDefaults('Foo Bars'))

    def testPassingABlankPreferredNameWillNotSetAnyDefaults(self):
        setDefaults = {'preferred_name': '', 'genre': 'Rock'}        

        self.settings.setArtistDefaults('The Foo Bars', setDefaults)

        self.assertEquals(None, self.settings.getArtistDefaults('The Foo Bars'))

if __name__ == '__main__':
    unittest.main()