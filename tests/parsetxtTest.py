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

# Format used in MOTB releases
motbText = \
"""MOTB Release: 12345
Release Date: 2010-01-01
Band: The Foo Bars
Date: 1980-12-01 (Monday)
Venue: The Venue
Location: New York, NY
Analog Audience Sournce: X
Medium Stock Brands: Y
Analog Lineage: Z
Analog Sound Preservation: XYZ
Taped By: Foo Baz
Transfer By: Baz Bar
Mastering By: Bar Foo

Set 1
d1t01 - Barcelona
d1t02 - Lisbon
d1t03 - London

Set 2
d2t01 - Austin
d2t02 - Dallas
d2t03 - El Paso
"""

class ParsetxtTestCase(unittest.TestCase):

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

        # Artist can begin with whitespace
        artist = TxtParser("  The Foo Bars\n1980-12-01\nTopeka, KS")._findArtist()
        self.assertEquals("The Foo Bars", artist)

        artist = TxtParser("\tThe Foo Bars\n1980-12-01\nTopeka, KS")._findArtist()
        self.assertEquals("The Foo Bars", artist)

        artist = TxtParser("Chicago\n1985-12-01\nBoston, MA")._findArtist()
        self.assertEquals("Chicago", artist)

        artist = TxtParser('Architecture in Helsinki\n2003-03-03\nMelbourne\nVenue')._findArtist()
        self.assertEquals('Architecture in Helsinki', artist)

        artist = TxtParser('The Foo Bars | Venue, New York, NY | 23.11.2010')._findArtist()
        self.assertEquals('The Foo Bars', artist)

        artist = TxtParser(motbText)._findArtist()
        self.assertEquals('The Foo Bars', artist)

    def testFindDateReturnsStringForFirstThingThatLooksLikeADate(self):
        date = TxtParser(sampleTxt)._findDate()
        self.assertEquals("1980-12-01", date)

        date = TxtParser("The Foo Bars\n12/01/80")._findDate()
        self.assertEquals('12/01/80', date)

        date = TxtParser("The Foo Bars\n05 05 1988")._findDate()
        self.assertEquals('05 05 1988', date)

        date = TxtParser("The Foo Bars\n85.12.25")._findDate()
        self.assertEquals('85.12.25', date)

        date = TxtParser("The Foo Bars\nJuly 22nd, 1982")._findDate()
        self.assertEquals("July 22nd, 1982", date)

        date = TxtParser("The Foo Bars\n14th August, 1991")._findDate()
        self.assertEquals("14th August, 1991", date)

        date = TxtParser('The Foo Bars\n5 Nov 90')._findDate()
        self.assertEquals('5 Nov 90', date)

        date = TxtParser('The Foo Bars | Venue, New York, NY | 23.11.2010')._findDate()
        self.assertEquals('23.11.2010', date)

        date = TxtParser(motbText)._findDate()
        self.assertEquals('1980-12-01', date)

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

        date = TxtParser._convertDateToDateObject('5 Nov 90').isoformat()
        self.assertEquals('1990-11-05', date)

        date = TxtParser._convertDateToDateObject('5-10-2005').isoformat()
        self.assertEquals('2005-05-10', date)

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
        self.assertEquals(['Song I Know', ' ', ' ', 'Another Song I Know'], tracklist)

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

        anotherTest = (
            "1. Funk (Prelude, part 1) (12:39)\r\n2. Ife (17:25)\r\n"
          + "3. Moja (03:16)\r\n4. Willie Nelson on Tune in 5 (05:48)"
        )

        tracklist = TxtParser(anotherTest)._findTracklist()
        self.assertEquals(['Funk (Prelude, part 1)', 'Ife', 'Moja', 'Willie Nelson on Tune in 5'], tracklist)

        # Forgive skipped track numbers
        tracklist = TxtParser('1) One\n2) Two\n3) Three\n5) Four')._findTracklist()
        self.assertEquals(['One', 'Two', 'Three', 'Four'], tracklist)

        # Forgive repeated track numbers
        tracklist = TxtParser('1) One\n2) Two\n3) Three\n3) Four')._findTracklist()
        self.assertEquals(['One', 'Two', 'Three', 'Four'], tracklist)

        # Tracklists indented with tabs read correctly
        tracklist = TxtParser('\t01. One\n\t02. Two\n\t03. Three')._findTracklist()
        self.assertEquals(['One', 'Two', 'Three'], tracklist)

        # Tracklists indented with spaces read correctly
        tracklist = TxtParser('    01. One\n    02. Two\n    03. Three')._findTracklist()
        self.assertEquals(['One', 'Two', 'Three'], tracklist)

        # Format common for Grateful Dead shows
        tracklist = TxtParser(
            'Set1\nd1t01 - One >\nd1t02 - Two >\nd1t03 - Three\n\nSet2\nd2t01 - Four'
          + '\nd2t02 - Five\nd2t03 - Six\n~encore~\nd2t04 - Seven'
        )._findTracklist()
        self.assertEquals(['One >', 'Two >', 'Three', 'Four', 'Five', 'Six', 'Seven'], tracklist)

        # Another format common for Grateful Dead shows
        tracklist = TxtParser(
            'Set1\n101-d1t01 - One >\n102-d1t02 - Two >\n103-d1t03 - Three\n\nSet2\n201-d2t01 - Four'
          + '\n202-d2t02 - Five\n203-d2t03 - Six\n~encore~\n204-d2t04 - Seven'
        )._findTracklist()
        self.assertEquals(['One >', 'Two >', 'Three', 'Four', 'Five', 'Six', 'Seven'], tracklist)

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

        # City name must match the whole word ("Parish" not mistaken for "Paris").
        location = TxtParser('The Foo Bars\n1980-12-01\nThe New Parish\nOakland, CA')._findLocation()
        self.assertEquals('Oakland, CA', location)

        # Handle confusing cases where the artist name is or contains a common city name
        location = TxtParser("Chicago\n1985-12-01\nBoston, MA")._findLocation()
        self.assertEquals("Boston, MA", location)

        location = TxtParser("Boston\n1985-12-01\nChicago, IL\nVenue")._findLocation()
        self.assertEquals("Chicago, IL", location)

        location = TxtParser('Architecture in Helsinki\n2003-03-03\nMelbourne\nVenue')._findLocation()
        self.assertEquals('Melbourne, Australia', location)

        location = TxtParser('The Foo Bars | Venue, New York, NY | 23.11.2010')._findLocation()
        self.assertEquals('New York, NY', location)

        location = TxtParser('Wilco\n2010-09-21\nCapitol\nOffenbach am Main, Germany')._findLocation()
        self.assertEquals('Offenbach, Germany', location)

        # Go with the location that appears first, even if other city names in the file appear earlier in
        # the common-cities.json file.
        location = TxtParser(
            'The Foo Bars\n1980-01-01\nTucson, AZ\nThe Venue\n\n01 New York\n02 London\n03 France'
        )._findLocation()
        self.assertEquals('Tucson, AZ', location)

        location = TxtParser(motbText)._findLocation()
        self.assertEquals('New York, NY', location)

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
        venue = TxtParser(
            'The Foo Bars\n1980-12-01\nLive at The Venue\nTopeka, KS (USA)\nLength: 01:02:33'
        )._findVenue()
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

        venue = TxtParser('The Foo Bars\nThe Venue\n1980-12-01\nTucson')._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('The Foo Bars\n1980-12-01\nTucson, AZ\nThe Merry-Go-Round')._findVenue()
        self.assertEquals('Merry-Go-Round', venue)

        venue = TxtParser(motbText)._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('The Foo Bars\n1980-12-01\nThe Venue\nTucson\nArizona')._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('Wilco\n2010-09-21\nCapitol\nOffenbach am Main, Germany')._findVenue()
        self.assertEquals('Capitol', venue)

        venue = TxtParser('The Foo Bars\nVenue\nAustin, TX\n 1990-09-09 (Sunday)')._findVenue()
        self.assertEquals('Venue', venue)

        venue = TxtParser('The Foo Bars | Venue, New York, NY | 23.11.2010')._findVenue()
        self.assertEquals('Venue', venue)

        # Capitalized option picked over non capitalized
        venue = TxtParser('The Foo Bars\n1990-09-09\nVenue\nAustin, TX\nlower cased')._findVenue()
        self.assertEquals('Venue', venue)

        # Otherwise, the one closest to 10 characters
        venue = TxtParser('The Foo Bars\n1990-09-09\nVenue\nAustin, TX\nTaper: Chip Dipson')._findVenue()
        self.assertEquals('Venue', venue)

        # If neither candidate is capitalized, pick the one closest to 10 characters
        txt = "The Foo Bars\n23 March 2010\n" \
            + "actual venue\nWashington DC\n" \
            + "LINEAGE: iRiver h320 > USB > wavelab > DSP > FLAC"
        venue = TxtParser(txt)._findVenue()
        self.assertEquals('actual venue', venue)

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