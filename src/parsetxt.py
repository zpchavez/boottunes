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
import urllib2
import data

# Load JSON files with city, state, and country names into global variables.
# Try to get cities list from the web first, falling back to the local json file.
jsonPath = data.path + '/' + 'json' + '/'
try:
    jsonString = urllib2.urlopen(
        'http://boottunes.googlecode.com/svn/trunk/src/data/json/common-cities.json',
        timeout=3
    ).read()
    cities = json.loads(jsonString)    
except:
    fileCities = open(jsonPath + 'common-cities.json')
    cities = json.loads(fileCities.read())    

fileStates = open(jsonPath + 'states.json')
fileProvinces = open(jsonPath + 'provinces.json')
fileCountries = open(jsonPath + 'countries.json')
states = json.loads(fileStates.read())
provinces = json.loads(fileProvinces.read())
countries = json.loads(fileCountries.read())
fileStates.close()
fileProvinces.close()
fileCountries.close()

class TxtParser(object):
    "Parse text from a text file for metadata"

    def __init__(self, txt):        
        # For reasons unknown, some text files may use just \r for newlines.
        # Normlize all newlines to \n for simplicity.
        self.txt = txt.replace('\r\n', '\n').replace('\r', '\n')        

    def _findArtist(self):
        """
        Find the artist in self.txt

        @rtype: string
        """                
        if hasattr(self, 'artist'): return self.artist        


        # Artist listed after label
        match = re.search('^\s*(?:Artist|Band)\s?[:\-]+(.+)$', self.txt, re.MULTILINE)
        if match:            
            self.artist = match.group(1).strip()
            return self.artist

        date = self._findDate()        

        # Probably the short line
        match = re.search('^\s*(.{1,80}?)(\n| - |\|)', self.txt, re.MULTILINE)
        if match and match.group(1) != date:            
            self.artist = match.group(1).strip().replace(date, '')            
            return self.artist

        self.artist = ''
        return self.artist

    def _findDate(self):
        """
        Find the date in self.txt.

        @rtype:  string
        @return: The string as it appears in the file
        """        
        if hasattr(self, 'date'): return self.date

        match = re.search('^\s*Date: ([a-zA-Z0-9\-, ]+).*$', self.txt, re.MULTILINE)
        if match:            
            self.date = match.group(1).strip()
            return self.date

        dateSep = '(?:|nd|rd|st|th)?[' + re.escape('-/\.|, ') + ']+'

        months = "(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
        pattern = (
            "\d{1,4}" + dateSep + "\d{1,2}" + dateSep + "\d{2,4}|"
            + months + " \d{1,2}" + dateSep + "\d{2,4}|"
            + "\d{1,4}" + dateSep + months + dateSep + "\d{2,4}"
        )        
        matches = re.findall(pattern, self.txt, re.IGNORECASE)        
        if len(matches) > 0:
            self.date = matches[0].strip()            
            return self.date
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
        currentYear = datetime.datetime.now().year        
        currentCentury = int(str(currentYear)[:2]) * 100
        previousCentury = currentCentury - 100
        currentDecadeAndYear = int(str(currentYear)[2:])
        
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
            pattern = '(\d{1,4})\D+(\d{1,4})'
            match = re.search(pattern, dateTxt)            
            if not match:                
                return None
            if match.group(1) != None:
                match1 = int(match.group(1))
                match2 = int(match.group(2))

                if match1 > 99:
                    yearInt = match1
                    dayInt = match2
                elif match2 > 4:
                    yearInt = match2
                    dayInt = match1
                else:
                    if match1 < 31 and match2 < 31:
                        if match1 > currentDecadeAndYear:
                            dayInt = match1
                            yearInt = match2
                        elif match2 > currentDecadeAndYear:
                            dayInt = match2
                            yearInt = match1
                        else:
                            return None
                    elif match1 != match2:
                        yearInt = max((match1, match2))
                        dayInt = min((match1, match2))
                    else:
                        # Can't tell which number if the year and which is the day
                        return None
                    
        else:
            pattern = '(\d{1,4})\D+(\d{1,2})\D+(\d{1,4})'
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
                yearInt = dateParts[2]
                dateParts = dateParts[:2]                
            
            # Consider the first number to be the month, unless it is too big
            monthInt, dayInt = (dateParts[0], dateParts[1]) if dateParts[0] < 13 else (dateParts[1], dateParts[0])

        # If we only have two numbers for the year, make the following assumptions
        # 1. The date is not in the future.
        # 2. The more recent date is most likely the correct one.
        if yearInt <= 99:
            if yearInt > currentDecadeAndYear:                
                yearInt = previousCentury + yearInt
            else:                
                yearInt = currentCentury + yearInt
        
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

        pattern = r"""
            (
                ^[\t\s]*           # May start with whitespace
                (?:                # Begin of optional prefix
                    (?:\d{3}-)?      # Prefix may start 101, 201, etc.
                    d\dt           # May contain prefix d1t, d2t, etc.
                )?                 # End of optional prefix                                
                [0-9]{1,3}         # One or two numbers
                [\W]               # Some sort of separator
                (.*)               # The actual track name
                $                  # The end of the line
                \n?                # Doesn't work right without this.  Not sure why.                
            ){1,}                  # 1 or more track lines
        """
 
        # There may be line breaks with text in between signifying an encore, so
        # look through and get all the pieces that look like a tracklist segments,
        # then concatenate them together.
        txt = self.txt
        previousTxt = None
        tracklistStr = ''
        while txt != previousTxt:
            match = re.search(pattern, txt, re.MULTILINE | re.VERBOSE)
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
            # or if the line contains the date
            if self._findDate() and trackLine.count(self._findDate()):
                continue            
            match = re.search('(?:(?:\d{3}-)?d\dt)?\d?(\d{1,2}).*', trackLine)
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
        trackTimePattern = r"""
            (
                [([]?          # Possible opening enclosures
                \d{1,2}        # Minutes, with optional opening 0
                [:\']          # Colon separator or ' minutes symbol
                [0-6][0-9]     # Minutes
                (?:\.\d{2})?   # Possible hundredths of seconds
                (?:"|'')?      # Possible " seconds symbol (may be made up of 2 apostrophes)
                [)\]]?         # Possible closing enclosure                
            )
            """
        # Filter out the track numbers and, if present, track times, to get just the titles
        pattern = r"""^(?:(?:\d{3}-)?d\dt)?              # Possible prefix like d1t01 or 101-d1t01
                      [\t\s]*[0-9]{1,3}[ .\-:)]*         # Track number, separator, and whitespace
                      """ + trackTimePattern + """?      # Track time if present before the title
                      (.*?)                              # The actual title
                      (?:[ -]*?)                         # White space or dash separator
                      """ + trackTimePattern + """?\s*$  # Track time if present after the title"""
        matches = re.findall(pattern, tracklistStr, re.MULTILINE | re.VERBOSE)
    
        # If the second group is empty, assume that what looked like the track time was actually the track title
        self.tracklist = [match[1].strip() if match[1] else match[0] for match in matches]
        return self.tracklist

    def _findLocation(self, asIs = False):
        """
        Return the geographical location of the recording.

        @type  asIs: Boolean
        @param asIs: Whether to return the location name exactly as it appears in the file
                     rather than shortening US state names to their abbreviations and expanding
                     country abbreviations to their full names.
        @rtype: string
        """        
        if asIs and hasattr(self, 'locationAsIs'):
            return self.locationAsIs
        elif not asIs and hasattr(self, 'location'):
            return self.location
        
        searchedText = self.txt.replace(self._findArtist(), '') \
                               .replace(self._findDate(), '')
        
        match = re.search('^\s*Location:\s*(.*)$', searchedText, re.MULTILINE)
        if match:            
            self.location = match.group(1)
            return self.location

        # Use the city with the lowest index
        candidate = {'city': None, 'index': len(searchedText)}

        # Check for a city from the common-cities list
        for city, cityDetails in cities.iteritems():                    
            match = re.search('\W(' + re.escape(city) + r')(\W|\Z)', searchedText)
            if match:                
                if 'province' in cityDetails:
                    for provinceAbbr in cityDetails['province']:
                        provinceFull = provinces[provinceAbbr]
                        pattern = city + "[,\s]*" + provinceFull + "|" + city + "[,\s]*" + provinceAbbr + "|" \
                                + city + "[,\s]*Canada"
                        match = re.search(pattern, searchedText, re.IGNORECASE)
                        if match:
                            index = searchedText.find(match.group(0))
                            if index < candidate['index']:
                                candidate['index'] = index
                                if asIs:
                                    candidate['city'] = match.group(0)                                
                                else:                                
                                    candidate['city'] = city + ', ' + provinceFull + ', Canada'
                        # If the city isn't qualified, but the city only has one state or country associated
                        # with it, assume that city
                        elif len(cityDetails) == 1 and len(cityDetails['province']) == 1:
                            index = searchedText.find(city)
                            if asIs:                                
                                if index < candidate['index']:
                                    candidate['city'] = city
                            else:
                                if index < candidate['index']:
                                    candidate['city'] = city + ', ' + provinceFull + ', Canada'
                            candidate['index'] = index                                
                if 'state' in cityDetails:                    
                    for stateAbbr in cityDetails['state']:
                        stateFull = states[stateAbbr]
                        pattern = city + "[,\s]*" + stateFull + "|" + city + "[,\s]*" + stateAbbr
                        match = re.search(pattern, searchedText, re.IGNORECASE)
                        if match:
                            index = searchedText.find(match.group(0))
                            if index < candidate['index']:
                                candidate['index'] = index                            
                                if asIs:
                                    candidate['city'] = match.group(0)
                                else:
                                    candidate['city'] = city + ', ' + stateAbbr                            
                        # If the city isn't qualified, but the city only has one state or country associated
                        # with it, assume that city
                        elif len(cityDetails) == 1 and len(cityDetails['state']) == 1:
                            index = searchedText.find(city)                            
                            if index < candidate['index']:
                                candidate['index'] = index
                                if asIs:
                                    candidate['city'] = city
                                else:
                                    candidate['city'] = city + ', ' + stateAbbr
                if 'country' in cityDetails:
                    for countryCode in cityDetails['country']:                                                
                        countryFull = countries[countryCode]
                        pattern = city + "[,\s]*" + countryFull + "|" + city + "[,\s]*" + countryCode
                        match = re.search(pattern, searchedText, re.IGNORECASE)
                        if match:
                            index = searchedText.find(match.group(0))
                            if index < candidate['index']:
                                candidate['index'] = index
                                if asIs:
                                    candidate['city'] = match.group(0)
                                else:
                                    candidate['city'] = city + ', ' + countryFull                            
                        elif len(cityDetails) == 1 and len(cityDetails['country']) == 1:
                            index = searchedText.find(city)
                            if index < candidate['index']:
                                candidate['index'] = index
                                if asIs:
                                    candidate['city'] = city
                                else:
                                    candidate['city'] = city + ', ' + countryFull                            

        if candidate['city']:
            self.location = candidate['city']
            return self.location

        self.location = ''
                          
        # If no match found from cities in the common city list, just search for a line that looks
        # like a location line, i.e. contains a comma
        match = re.search('^.+,.+$', searchedText, re.MULTILINE)
        if not match:            
            return self.location

        self.location = match.group(0).strip()
        
        cityStateMatch = re.search('([a-z ]+, [a-z]{2})(\s|,|$)', self.location, re.IGNORECASE)
        if cityStateMatch:
            self.location = cityStateMatch.group(1).strip()            

        # If a venue is included on the same line after a dash, isolate the location
        locationMatch = re.search('(.*)( - .*)', self.location)
        if locationMatch:
            self.location = locationMatch.group(1).strip()            

        if len(self.location) > 30:
            self.location = ''
        else:
            self.location = self.location.strip()
            
        return self.location

    def _findVenue(self):
        """
        Return the best guess at the venue.

        @rtype: string
        """        
        if hasattr(self, 'venue'): return self.venue

        match = re.search('^\s*Venue: (?:The )?(.*)\s*$', self.txt, re.MULTILINE)
        if match:
            self.venue = match.group(1).strip();
            return self.venue

        # Venue is usually directly after or before the location line
        locationTxt = self._findLocation(True)

        if not locationTxt:
            return ''

        searchedText = self.txt.replace(self._findArtist(), '') \
                               .replace(self._findDate(), '')

        pattern = r"""
            (?:                
                ([^,\n|]*)      # Venue candidate
                \s*[,\-\n]\s*   # Dash, comma, or newline separator
            )?
            """ + re.escape(locationTxt) + r"""
            (?:
                (?:\s\(USA\))?  # US locations something end with (USA)
                \s*[,\-\n]\s*   # Dash, comma, or newline separator
                ([^\n|]*)       # Venue candidate 2
            )?
        """
        
        matches = re.search(            
            pattern,
            searchedText,
            re.IGNORECASE | re.MULTILINE | re.VERBOSE
        )
        
        if matches:
            strippedChars = ' ,\r\t\n-'
            possibilities = []
            possibilities.append(matches.group(1).strip(strippedChars) if matches.group(1) else '')
            possibilities.append(matches.group(2).strip(strippedChars) if matches.group(2) else '')            
            candidates = []            
            excludePatterns = [
                '\W?USA\W?',
                '\W?Canada\W?',
                '\d{2}:\d{2}',  # Probably the running time
                '^\(.*\)$',     # If it's in parentheses, it's probably not the venue
                '.{50,}',       # A venue name that long wouldn't even fit on the sign
                '^$'
            ]
            
            for index, possibility in enumerate(possibilities):
                isCandidate = True
                for excludePattern in excludePatterns:
                    if re.search(excludePattern, possibility, re.IGNORECASE):
                        isCandidate = False
                        break
                if isCandidate:
                    candidates.append(possibility)            
            
            if len(candidates) == 1:
                choice = candidates[0]
            elif len(candidates) == 2:
                # If one is capitalized, go with that, otherwise go with the one closest to 10 characters.
                # If they are tied, go with the second one
                wordsCapitalizedPattern = ('^([A-Z][a-z]* ?)*$')
                capCount = 0
                for candidate in candidates:
                    match = re.search(wordsCapitalizedPattern, candidate)
                    if match:                        
                        matched = match.group(0)
                        capCount += 1
                if capCount == 2 or capCount == 0:
                    tenCharProximity1 = abs(10 - len(candidates[0]))
                    tenCharProximity2 = abs(10 - len(candidates[1]))
                    if tenCharProximity1 < tenCharProximity2:
                        choice = candidates[0]
                    else:
                        choice = candidates[1]
                elif capCount == 1:                    
                    choice = matched
            else:
                self.venue = ''
                return self.venue

            #self.venue = re.search('[\w\s]+', choice).
            self.venue = choice.strip()
            self.venue = re.sub('^[lL]ive at ', '', self.venue, 1) # Filter out "Live at"
            self.venue = re.sub('^[tT]he ', '', self.venue, 1)      # Filter out "the"
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
                dateObj = self._convertDateToDateObject(dateTxt)
            except ParseTxtError:
                dateObj = None
        else:
            dateObj = None
        
        location  = self._findLocation()        
        artist    = self._findArtist()                
        venue     = self._findVenue()
        tracklist = self._findTracklist()

        return {'artist'    : unicode(artist),
                'date'      : dateObj,
                'location'  : unicode(location),
                'venue'     : unicode(venue),
                'tracklist' : tracklist,
                'comments'  : unicode(self.txt)}
    
class ParseTxtError(Exception): pass