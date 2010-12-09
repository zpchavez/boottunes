"""
Parse the txt file containing information about the recording.  Try to err on
the side of returning an empty value, rather than making an incorrect guess.

Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""
import re
import datetime
import json
import data

# Load JSON files with city, state, and country names into global variables
jsonPath = data.path + '/' + 'json' + '/'
fileCities = open(jsonPath + 'common-cities.json')
fileStates = open(jsonPath + 'states.json')
fileProvinces = open(jsonPath + 'provinces.json')
fileCountries = open(jsonPath + 'countries.json')

cities = json.loads(fileCities.read())
"""Example entry: {'Birmingham': {'state': ['AL']}, {'country': ['UK']}}"""

states = json.loads(fileStates.read())
"""Contains state abbreviation as key and full name as value"""

provinces = json.loads(fileProvinces.read())
"""Contains province abbreviation as key and full name as value"""

countries = json.loads(fileCountries.read())
"""Contains 2-character code as key and full country name as value"""

fileCities.close()
fileStates.close()
fileCountries.close()

class TxtParser(object):
    "Parse text from a text file for metadata"

    def __init__(self, txt):        
        # For reasons unknown, some text files may use just \r for newlines.
        # Normlize all newlines to \n for simplicity.
        self.txt = txt.replace('\r\n', '\n').replace('\r', '\n')        

    def _findMetadataBlock(self):
        """
        Find the section of self.txt that contains the
        artist, date, and location

        @rtype: string
        """        
        if hasattr(self, 'metadataBlock'): return self.metadataBlock
        
        pattern = '\n?((^.{2,60}$\n?){3,6})'
        matches = re.findall(pattern, self.txt, re.MULTILINE)        

        # Default will be the whole string.
        self.metadataBlock = self.txt
        
        # If a date and/or location is found in the block, use it
        for match in matches:
            if match[0] in self._findTracklistString():
                continue            
            # Delete any cached results, so that a new search is performed, rather
            # than simply returning the previous result.
            if hasattr(self, 'location'): del self.location
            if hasattr(self, 'date'): del self.date            
            if (self._findDate() or self._findLocation(searchedText = match[0])):                
                self.metadataBlock = match[0]
                return self.metadataBlock                

        return self.metadataBlock

    def _findArtist(self):
        """
        Find the artist in self.txt

        @rtype: string
        """        
        if hasattr(self, 'artist'): return self.artist

        # Artist listed by itself on one line at the top
        match = re.match('([^\n]{1,25})$[\r\n]{1,2}$', self.txt, re.MULTILINE | re.DOTALL)
        if match:
            self.artist = match.group(1).strip()            
        else:
            # Artist listed at the top of the metadata block
            matches = re.findall(r'^(\S.+)\S*$', self._findMetadataBlock(), re.MULTILINE)
            if len(matches) > 0:
                # Remove, if present, the label for the line
                match = matches[0]
                regex = re.compile('Artist:\s*', re.IGNORECASE)
                match = regex.sub('', matches[0])
                self.artist = match.strip()
            
        self.artist = self.artist.replace(self._findDate(), '')
        self.artist = self.artist.replace(self._findLocation(), '')
        self.artist = self.artist.replace(self._findVenue(), '')
        return self.artist

    def _findDate(self):
        """
        Find the date in self.txt.

        @rtype:  string
        @return: The string as it appears in the file
        """
        if hasattr(self, 'date'): return self.date        

        months = "(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
        pattern = "\d{1,4}.\d{1,2}.\d{2,4}|" + months + " \d{1,2}.*?\d{2,4}|\d{1,2}.*? " + months + ".*? \d{2,4}|" \
                  "\d{2,4}." + months + ".\d{1,2}"
        matches = re.findall(pattern, self.txt, re.IGNORECASE)        
        if len(matches) > 0:            
            self.date = matches[0].strip()
            return matches[0].strip()
        self.date = ''
        return ''

    @staticmethod
    def _convertDateToDateObject(dateTxt):
        """
        Parse the date string as found with self._findDate and convert it to
        a datetime.date object.

        Raises a ParseTxtError if date is invalid.

        @type  date: string
        @param date: A string containing the day, month and year, in one of the
                     common formats
        @rtype: datetime.date
        """
        # If date contains a text month, get it as an integer
        monthInt = None
        if re.search('[a-z]', dateTxt, re.IGNORECASE):
            months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
            for i in range(len(months)):
                pattern = months[i] + '[a-z]*'
                if re.search(pattern, dateTxt, re.IGNORECASE):
                    monthInt = i + 1
                    break
                if i == 11:
                    raise ParseTxtError()

        if monthInt:
            pattern = '(\d{1,2})\D+(\d{4})|(\d{4})\D+(\d{1,2})'
            match = re.search(pattern, dateTxt)            
            if match.group(1) != None:
                dayInt = int(match.group(1))
                yearInt = int(match.group(2))
            else:
                dayInt = int(match.group(4))
                yearInt = int(match.group(3))
        else:
            pattern = '(\d{2,4})\D+(\d{2})\D+(\d{2,4})'            
            match = re.search(pattern, dateTxt)
            if not match:
                return None            
            dateParts = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if dateParts[0] > 99:
                yearInt = dateParts[0]
                dateParts = dateParts[1:]
            elif dateParts[2] > 99:
                yearInt = dateParts[2]
                dateParts = dateParts[:2]
            elif dateParts[0] > 12:                
                yearInt = dateParts[0]
                dateParts = dateParts[1:]
            elif dateParts[2] > 12:
                yearInt = dateParts[2]
                dateParts = dateParts[:2]
            else:
                return None # Can't tell which is the year

            # If we only have two number for the year, make the following assumptions
            # 1. The date is not in the future.  2. The more recent date is most likely meant
            if yearInt <= 99:
                currentYear = datetime.datetime.now().year
                currentCentury = int(str(currentYear)[:2])
                currentDecadeAndYear = int(str(currentYear)[2:])                
                if yearInt > currentDecadeAndYear:
                    yearInt = int(str(currentCentury - 1) + str(yearInt))
                else:
                    yearInt = int(str(currentCentury) + str(yearInt))

            # Consider the first number to be the month, unless it is too big
            monthInt, dayInt = (dateParts[0], dateParts[1]) if dateParts[0] < 13 else (dateParts[1], dateParts[0])

        try:
            dateObj = datetime.date(yearInt, monthInt, dayInt)
        except ValueError:
            raise ParseTxtError("Invalid Date")

        return dateObj

    def _findTracklistString(self):
        """
        Get the tracklist as a string

        @rtype: unicode
        """
        if hasattr(self, 'tracklistStr'): return self.tracklistStr

        pattern = r"""\n?((^[\t\s]*[0-9]{1,2}[\W](.*)$\n?){1,})"""
 
        # There may be line breaks with text in between signifying an encore, so
        # look through and get all the pieces that look like a tracklist segments,
        # then concatenate them together.
        txt = self.txt
        previousTxt = None
        tracklistStr = ''
        while txt != previousTxt:
            match = re.search(pattern, txt, re.MULTILINE)
            if match == None:
                break;
            tracklistStr += match.group(0)            
            previousTxt = txt                        
            txt = txt.replace(match.group(0), '')            
        
        self.tracklistStr = unicode(tracklistStr)        
        return self.tracklistStr

    def _findTracklist(self):
        """
        Get the tracklist in a list object.

        @rtype: list
        """
        if hasattr(self, 'tracklist'): return self.tracklist

        tracklistStr = self._findTracklistString()
        
        if tracklistStr == '':
            return None

        # Make sure the numbers count up incrementally.  Remove anything that doesn't match.
        trackLines = tracklistStr.splitlines(True);
        tracklistStr = '' # use the same name for the filtered tracklist string
        expectedTrackNum = 1
        for trackLine in trackLines:
            # Don't count if the line contains an md5 hash            
            if re.search('[0-9a-f]{32}', trackLine, re.IGNORECASE):
                continue
            match = re.search('(\d{1,2}).*', trackLine)
            actualTrackNum = int(match.group(1)) if match else None            
            # Allow for common mistakes of repeating track numbers and skipping track numbers
            expectedTrackNums = [expectedTrackNum, expectedTrackNum - 1, expectedTrackNum + 1]
            if match and actualTrackNum in expectedTrackNums:
                tracklistStr += trackLine
                expectedTrackNum = actualTrackNum + 1
            # Sometimes the tracklist starts at zero
            elif match and expectedTrackNum == 1 and actualTrackNum == 0:
                tracklistStr += trackLine
            elif match and expectedTrackNum != 1 and actualTrackNum in [0, 1]:
                # If tracklist seperated into multiple discs, the counting may start over
                tracklistStr += trackLine
                expectedTrackNum = int(match.group(1)) + 1        
        trackTimePattern = '([([]?\d{1,2}:[0-6][0-9][)\]]?)'        
        # Filter out the track numbers and, if present, track times, to get just the titles
        pattern = r"""^[\t\s]*[0-9]{1,2}[ .\-)]*                # Track number, separator, and whitespace
                      """ + trackTimePattern + """?      # Track time if present before the title
                      (.*?)                              # The actual title
                      (?:[ -]*?)                         # White space or dash separator
                      """ + trackTimePattern + """?\s*$  # Track time if present after the title"""
        matches = re.findall(pattern, tracklistStr, re.MULTILINE | re.VERBOSE)
    
        # If the second group is empty, assume that what looked like the track time was actually the track title
        self.tracklist = [match[1].strip() if match[1] else match[0] for match in matches]
        return self.tracklist

    def _findLocation(self, asIs = False, searchedText = None):
        """
        Return the geographical location of the recording.

        @type  asIs: Boolean
        @param asIs: Whether to return the location name exactly as it appears in the file
                     rather than shortening US state names to their abbreviations and expanding
                     country abbreviations to their full names.

        @rtype: string
        """
        if asIs and searchedText == None and hasattr(self, 'locationAsIs'):
            return self.locationAsIs
        elif not asIs and searchedText == None and hasattr(self, 'location'):
            return self.location

        if searchedText == None:
            metadataBlock = self._findMetadataBlock()
        else:
            metadataBlock = searchedText
        
        metadataBlock = self._findMetadataBlock()        

        # Check for a city from the common-cities list
        for city, cityDetails in cities.iteritems():
            match = re.search('\W' + city + r'(\W|\Z)', metadataBlock)
            if match:                
                if 'province' in cityDetails:
                    for provinceAbbr in cityDetails['province']:
                        provinceFull = provinces[provinceAbbr]
                        pattern = city + "[,\s]*" + provinceFull + "|" + city + "[,\s]*" + provinceAbbr + "|" \
                                + city + "[,\s]*Canada"
                        match = re.search(pattern, metadataBlock, re.IGNORECASE)
                        if match:
                            if asIs:
                                self.locationAsIs = match.group(0)
                                return self.locationAsIs
                            else:
                                self.location = city + ', ' + provinceFull + ', Canada'
                                return self.location
                        # If the city isn't qualified, but the city only has one state or country associated
                        # with it, assume that city
                        elif len(cityDetails) == 1 and len(cityDetails['province']) == 1:
                            if asIs:
                                self.locationAsIs = city
                                return self.locationAsIs
                            else:
                                self.location = city + ', ' + provinceFull + ', Canada'
                                return self.location
                if 'state' in cityDetails:
                    for stateAbbr in cityDetails['state']:
                        stateFull = states[stateAbbr]
                        pattern = city + "[,\s]*" + stateFull + "|" + city + "[,\s]*" + stateAbbr
                        match = re.search(pattern, metadataBlock, re.IGNORECASE)
                        if match:
                            if asIs:
                                self.locationAsIs = match.group(0)
                                return self.locationAsIs
                            else:
                                self.location = city + ', ' + stateAbbr
                                return self.location
                        # If the city isn't qualified, but the city only has one state or country associated
                        # with it, assume that city
                        elif len(cityDetails) == 1 and len(cityDetails['state']) == 1:
                            if asIs:
                                self.locationAsIs = city
                                return self.locationAsIs
                            else:
                                self.location = city + ', ' + stateAbbr
                                return self.location

                if 'country' in cityDetails:
                    for countryCode in cityDetails['country']:                                                
                        countryFull = countries[countryCode]
                        pattern = city + "[,\s]*" + countryFull + "|" + city + "[,\s]*" + countryCode
                        match = re.search(pattern, metadataBlock, re.IGNORECASE)
                        if match:
                            if asIs:
                                self.locationAsIs = match.group(0)
                                return self.locationAsIs
                            else:
                                self.location = city + ', ' + countryFull
                                return self.location
                        elif len(cityDetails) == 1 and len(cityDetails['country']) == 1:
                            if asIs:
                                self.locationAsIs = city
                                return self.locationAsIs
                            else:
                                self.location = city + ', ' + countryFull
                                return self.location


        # If no match found from cities in the common city list, just search for a line that looks
        # like a location line, i.e. contains a comma
        matches = re.findall('^.+,.+$', metadataBlock, re.MULTILINE)
        if not matches:
            self.location = ''
            return self.location
        lineTxt = ''        
        for match in matches:
            # Don't mistake the date as the location
            if self._findDate() not in match:
                lineTxt = match
                break

        labelMatch = re.match('Location:(.*)', lineTxt, re.IGNORECASE)
        if labelMatch:
            lineTxt = labelMatch.group(1)        
        cityStateMatch = re.search('([a-z ]+, [a-z]{2})(\s|,|$)', lineTxt, re.IGNORECASE)        
        if cityStateMatch:
            self.location = cityStateMatch.group(1).strip()
            return self.location

        # If a venue is included on the same line after a dash, isolate the location
        locationMatch = re.search('(.*)( - .*)', lineTxt)
        if locationMatch:
            self.location = locationMatch.group(1).strip()
            return self.location

        self.location = lineTxt.strip()
        return self.location

    def _findVenue(self):
        """
        Return the best guess at the venue.

        @rtype: string
        """        
        if hasattr(self, 'venue'): return self.venue

        # Venue is usually directly after or before the location line
        locationTxt = self._findLocation(True)
        
        if not locationTxt:
            return ''

        metadataBlock = self._findMetadataBlock()        
        metadataBlock = metadataBlock.replace(self._findArtist(), '')                
        metadataBlock = metadataBlock.replace(self._findDate(), '')        

        matches = re.search(            
            '((?:live at )?(.*)[,\s\-]*)?' + locationTxt + '((?: \(USA\))?(?:live at )?[,\s\-]*(.*))?',
            metadataBlock,
            re.IGNORECASE | re.MULTILINE
        )

        fullLocationText = self._findLocation(False)
        countryOrStateMatch = re.findall(', (.*)', fullLocationText)
        if countryOrStateMatch:
            countryOrState = countryOrStateMatch[0]

        if matches:
            strippedChars = ' ,\r\t\n-'
            possibilities = [matches.group(4).strip(strippedChars), matches.group(2).strip(strippedChars)]            
            for index, possibility in enumerate(possibilities):
                if possibility == '': # May be blank after stripped out insignificant characters
                    continue
                if countryOrStateMatch and (countryOrState in possibility):
                    continue
                if re.search('\W?USA\W?', possibility):
                    continue
                if re.search('\W?Canada\W?', possibility):
                    continue
                if re.search('\d{2}:\d{2}', possibility): # Probably the play length
                    continue
                if re.search('\(.*\)', possibility): # If it's in parentheses, it's probably not the venue
                    continue
                if index == 0 and len(possibility) > 50: # A venue name that long wouldn't even fit on the sign
                    continue
                else:                    
                    self.venue = re.sub('^[tT]he ', '', possibility, 1) # Filter out "the"
                    return self.venue
                
        self.venue = ''
        return self.venue
    
    def parseTxt(self):
        """
        Get a dictionary of all the metadata found in self.txt.

        @rtype:     dict
        @return:    A dictionary containing keys "artist", "venue", "date",
                    "location", "comments", and "tracks".  All but "tracks" and "date"
                    are strings.  "tracks" is a list of unicode strings and "date" is a
                    datetime.date object.
        """

        dateTxt = self._findDate()        
        if dateTxt:            
            try:
                dateObj = self._convertDateToDateObject(self._findDate())
            except ParseTxtError:
                dateObj = None
        else:
            dateObj = None

        return {'artist'    : unicode(self._findArtist()),
                'date'      : dateObj,
                'location'  : unicode(self._findLocation()),
                'venue'     : unicode(self._findVenue()),
                'tracklist' : self._findTracklist(),
                'comments'  : unicode(self.txt)}
    
class ParseTxtError(Exception): pass