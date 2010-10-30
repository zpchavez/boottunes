import unittest
from parsetxt import TxtParser, ParseTxtError

# Typical text arrangement
sampleTxt = \
"""The Foo Bars
1980-12-01
Topeka, KS
The Venue

Recorded on an X using Y

01 - First Song
02 - Second Song
03 - Third Song

Notes: B- Quality

Don't encode in a lossy format, dude!
"""

class ParsetxtTestCase(unittest.TestCase):

    def testFindMetadataBlockTriesToGetTheBlockOfBasicInfoWhichMayNotBeAtTheStartOfTheTxt(self):        
        expected = "The Foo Bars\n1980-12-01\nTopeka, KS\nThe Venue\n"

        block = TxtParser(sampleTxt)._findMetadataBlock()
        self.assertEquals(expected, block)

        # A block of text may come first
        line = "This is my long review of the show.  Man, what a great show.  Recording sounds great!\n"
        txt = line * 5 + "\n\n" + sampleTxt
        block = TxtParser(txt)._findMetadataBlock()
        self.assertEquals(expected, block)

        # If there is no discernible block, the entire string will be returned unchanged
        # Don't return the tracklist
        txt = sampleTxt.replace(expected, '')
        block = TxtParser(txt)._findMetadataBlock()        
        self.assertEquals(txt, block)        

    def testFindArtistTriesToGetTheArtist(self):
        artist = TxtParser(sampleTxt)._findArtist()
        self.assertEquals("The Foo Bars", artist)

        # whitespace may come first
        artist = TxtParser("\n  \n" + sampleTxt)._findArtist()
        self.assertEquals("The Foo Bars", artist)

        # A block of text may come first
        line = "This is my long review of the show.  Man, what a great show.  Recording sounds great!\n"
        txt = line * 5 + "\n\n" + sampleTxt
        artist = TxtParser(txt)._findArtist()
        self.assertEquals("The Foo Bars", artist)

        # A summary line may be the first line, followed by the full block later
        txt = "The Foo Bars - Live at The Venue - Sold out show!!\n\n" + sampleTxt
        artist = TxtParser(txt)._findArtist()
        self.assertEquals("The Foo Bars", artist)

        # Metadata may be labeled
        artist = TxtParser("Artist: The Foo Bars\nDate: 1980-12-01\nLocation: Topeka, KS")._findArtist()
        self.assertEquals("The Foo Bars", artist)

        # Single line at the time followed by a blank line is probably the artist
        artist = TxtParser("The Foo Bars\n\nThe Venue\n1980-12-01\nTopeka, KS\nRunning Time: 60:00")._findArtist()
        self.assertEquals('The Foo Bars', artist)


    def testFindDateReturnsStringForFirstThingThatLooksLikeADate(self):
        date = TxtParser(sampleTxt)._findDate()
        self.assertEquals("1980-12-01", date)

        date = TxtParser("The Foo Bars\r12/01/80")._findDate()
        self.assertEquals('12/01/80', date)

        date = TxtParser("The Foo Bars\r05 05 1988")._findDate()
        self.assertEquals('05 05 1988', date)

        date = TxtParser("The Foo Bars\r85.12.25")._findDate()
        self.assertEquals('85.12.25', date)

        date = TxtParser("The Foo Bars\rJuly 22nd, 1982")._findDate()
        self.assertEquals("July 22nd, 1982", date)

        date = TxtParser("The Foo Bars\r14th August, 1991")._findDate()
        self.assertEquals("14th August, 1991", date)

    def testConvertDateToDateObjectWorksForVariousPermutations(self):
        # If ambigious which number is day and which is month, assume first number is month
        date = TxtParser._convertDateToDateObject('1980-12-01').isoformat()
        self.assertEquals('1980-12-01', date)

        date = TxtParser._convertDateToDateObject('1983-31-10').isoformat()
        self.assertEquals('1983-10-31', date)

        date = TxtParser._convertDateToDateObject('12/01/80').isoformat()
        self.assertEquals('1980-12-01', date)

        date = TxtParser._convertDateToDateObject('05 05 1988').isoformat()
        self.assertEquals('1988-05-05', date)

        date = TxtParser._convertDateToDateObject('85/12/25').isoformat()
        self.assertEquals('1985-12-25', date)

        date = TxtParser._convertDateToDateObject('July 22nd, 1982').isoformat()
        self.assertEquals('1982-07-22', date)

        date = TxtParser._convertDateToDateObject('14th August, 1991').isoformat()
        self.assertEquals('1991-08-14', date)

        # If unclear which is the year (i.e. a recording from 1930), assume year is first
        date = TxtParser._convertDateToDateObject('30-12-25').isoformat()
        self.assertEquals('1930-12-25', date)

    def testConvertDateToDateObjectThrowsExceptionIfDateIsInvalid(self):
        self.assertRaises(ParseTxtError, TxtParser._convertDateToDateObject, '44th August, 1991')
        self.assertRaises(ParseTxtError, TxtParser._convertDateToDateObject, '99/99/99')
        self.assertRaises(ParseTxtError, TxtParser._convertDateToDateObject, '2010/02/29')

    def testFindTracklistWorksWithVariousNumberingFormats(self):
        tracklist = TxtParser(sampleTxt)._findTracklist()
        self.assertEquals(['First Song', 'Second Song', 'Third Song'], tracklist)

        tracklist = TxtParser('1. 1st song\n2. 2nd song\n3. 3rd song')._findTracklist()
        self.assertEquals(['1st song', '2nd song', '3rd song'], tracklist)

        tracklist = TxtParser('01. One\n02. Two\n03. Three')._findTracklist()
        self.assertEquals(['One', 'Two', 'Three'], tracklist);

        # Unknown tracks may just be left blank, but those will be captured too as empty strings
        tracklist = TxtParser('01 Song I Know\n02\n03\n04 Another Song I Know')._findTracklist()
        self.assertEquals(['Song I Know', '', '', 'Another Song I Know'], tracklist)

        # An encore may be split up from the rest of the track list
        tracklist = TxtParser('01. One\n02. Two\n03. Three\n\nEncore\n\n04. Encore')._findTracklist()
        self.assertEquals(['One', 'Two', 'Three', 'Encore'], tracklist);

        # Tracklist may be split up into 2 discs
        tracklist = TxtParser('01. One\n02. Two\n03. Three\nDisc2\n01 Four\n02 Five')._findTracklist()
        self.assertEquals(['One', 'Two', 'Three', 'Four', 'Five'], tracklist)

        # Or even three
        tracklist = TxtParser('01. One\n02. Two\n03. Three\nDisc2\n01 Four\n02 Five\nDisc3\n01 Six')._findTracklist()
        self.assertEquals(['One', 'Two', 'Three', 'Four', 'Five', 'Six'], tracklist)

        # Don't count lines with md5 hashes
        tracklist = TxtParser('01. One\n02. Two\n01. One - 03a575f8f6a1298e22cc204e5f713136')._findTracklist()
        self.assertEquals(['One', 'Two'], tracklist)

        # Track times detected and removed from tracklist
        tracklist = TxtParser('01. [1:11] One\n02. Two (2:22)\n03. Three 3:33\n04. 4:44')._findTracklist()
        self.assertEquals(['One', 'Two', 'Three', '4:44'], tracklist) # 4:44 is the actual song name.

        anotherTest = """1. Funk (Prelude, part 1) (12:39)\r\n2. Ife (17:25)\r\n3. Moja (03:16)\r\n4. Willie Nelson on Tune in 5 (05:48)"""

        tracklist = TxtParser(anotherTest)._findTracklist()
        self.assertEquals(['Funk (Prelude, part 1)', 'Ife', 'Moja', 'Willie Nelson on Tune in 5'], tracklist)

    def testFindLocationTriesToGetGeographicalLocationButNotVenue(self):
        """
        Getting the first line of the metadata block with a comma will work in most cases.

        Filter out venue:
            if line has a " - ", stop.
            If encountered ", AB " where AB are any two capital letters, stop.
        Sometimes
        """
        location = TxtParser(sampleTxt)._findLocation()
        self.assertEquals('Topeka, KS', location)

        location = TxtParser('The Foo Bars\n1980-12-01\nTopeka, KS - The Venue')._findLocation()
        self.assertEquals('Topeka, KS', location)

        location = TxtParser('The Foo Bars\n1980-12-01\nTopeka, Kansas, United States - The Venue')._findLocation()
        self.assertEquals('Topeka, Kansas, United States', location)

        location = TxtParser('The Foo Bars\n1980-12-01\nTopeka, KS (USA) - The Venue')._findLocation()
        self.assertEquals('Topeka, KS', location)

        # Without any commas it can't guess which may be the location
        location = TxtParser('The Foo Bars\n1980-12-01\nTopeka\nKansas\nThe Venue')._findLocation()
        self.assertEquals('', location)

        location = TxtParser('Artist: The Foo Bars\nDate: 1980-12-10\nLocation: Topeka, KS')._findLocation()
        self.assertEquals('Topeka, KS', location)

        location = TxtParser('The Foo Bars\n1980-12-01\nTopeka, KS, The Venue')._findLocation()
        self.assertEquals('Topeka, KS', location)

        location = TxtParser('The Foo Bars\n1980-12-01\nThe Venue, Topeka, KS')._findLocation()
        self.assertEquals('Topeka, KS', location)

        location = TxtParser('The Foo Bars\n1980-12-01\nThe Venue\nLondon\nUK')._findLocation()
        self.assertEquals('London, UK', location)

        location = TxtParser('The Foo Bars\n1980-12-01\nThe Venue, Birmingham, UK')._findLocation()
        self.assertEquals('Birmingham, UK', location)

        location = TxtParser('The Foo Bars\n1980-12-01\nThe Venue, Tucson, Arizona')._findLocation()
        self.assertEquals('Tucson, AZ', location)

        location = TxtParser('The Foo Bars\n1980-12-01\nBirmingham, UK, The Venue')._findLocation()
        self.assertEquals('Birmingham, UK', location)

        location = TxtParser('The Foo Bars\n1980-12-01\nTucson, Arizona, The Venue')._findLocation()
        self.assertEquals('Tucson, AZ', location)

        # Canadian cities return city, province, country
        location = TxtParser('The Foo Bars\n1980-12-01\nToronto, ON\nThe Venue')._findLocation()
        self.assertEquals('Toronto, Ontario, Canada', location)

        location = TxtParser('The Foo Bars\n1980-12-01\nToronto\nThe Venue')._findLocation()
        self.assertEquals('Toronto, Ontario, Canada', location)

        location = TxtParser('The Foo Bars\n1980-12-01\nToronto, Ontario\nThe Venue')._findLocation()
        self.assertEquals('Toronto, Ontario, Canada', location)

        location = TxtParser('The Foo Bars\n1980-12-01\nToronto, Canada\nThe Venue')._findLocation()
        self.assertEquals('Toronto, Ontario, Canada', location)

    def testFindVenueTriesToGetVenue(self):
        venue = TxtParser(sampleTxt)._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('The Foo Bars\n1980-12-01\nTopeka, KS - The Venue')._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('The Foo Bars\n1980-12-01\nTopeka, Kansas, United States - The Venue')._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('The Foo Bars\n1980-12-01\nTopeka, KS (USA) - The Venue')._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('The Foo Bars\n1980-12-01\nTopeka, KS (USA)\nThe Venue')._findVenue()
        self.assertEquals('Venue', venue)

        # "Live at" removed
        venue = TxtParser('The Foo Bars\n1980-12-01\nLive at The Venue\nTopeka, KS (USA)\nLength: 01:02:33')._findVenue()
        self.assertEquals('Venue', venue)

        # With no discernible location to search near, cannot ascertain the venue either
        venue = TxtParser('The Foo Bars\n1980-12-01\nTopeka\nKansas\nThe Venue')._findVenue()
        self.assertEquals('', venue)

        venue = TxtParser('The Foo Bars\n1980-12-01\nTopeka, KS, The Venue')._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('The Foo Bars\n1980-12-01\nTopeka, KS (USA), The Venue')._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('The Foo Bars\n1980-12-01\nThe Venue, Topeka, KS')._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('The Foo Bars\n1980-12-01\nThe Venue, Birmingham, UK')._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('The Foo Bars\n1980-12-01\nThe Venue, Tucson, Arizona')._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('The Foo Bars\n1980-12-01\nThe Venue, Tucson')._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('The Foo Bars\n1980-12-01\nBirmingham, UK, The Venue')._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('The Foo Bars\n1980-12-01\nTucson, Arizona, The Venue')._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('The Foo Bars\n1980-12-01\nTucson, The Venue')._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('The Foo Bars\n1980-12-01\nThe Venue\nTucson\nArizona')._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('Wilco\n2010-09-21\nCapitol\nOffenbach am Main, Germany')._findVenue()
        self.assertEquals('Capitol', venue)


    def testParseTxtReturnsDictionaryWithAllFoundMetadata(self):
        txtParser = TxtParser(sampleTxt)
        metadata = txtParser.parseTxt()
        self.assertTrue(isinstance(metadata, dict))
        self.assertTrue('artist' in metadata.keys())
        self.assertEquals('The Foo Bars', metadata['artist'])
        self.assertEquals('1980-12-01', metadata['date'].isoformat())
        self.assertEquals('Topeka, KS', metadata['location'])
        self.assertEquals('Venue', metadata['venue'])
        self.assertEquals(['First Song', 'Second Song', 'Third Song'], metadata['tracklist'])
        self.assertEquals(sampleTxt, metadata['comments'])
        
if __name__ == '__main__':
    unittest.main()