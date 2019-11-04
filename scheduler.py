from __future__ import print_function
from datetime import datetime, timedelta
import re
import json

from collections import Counter


import pickle
import os.path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from bs4 import BeautifulSoup

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']
BASE_URL = "https://pydata.org"
BASE_SCHEDULE = "/nyc2019/schedule/"

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    # print('Getting the upcoming 10 events')
    # events_result = service.events().list(calendarId='primary', timeMin=now,
    #                                     maxResults=10, singleEvents=True,
    #                                     orderBy='startTime').execute()
    # events = events_result.get('items', [])
# 
    # if not events:
    #     print('No upcoming events found.')
    # for event in events:
    #     start = event['start'].get('dateTime', event['start'].get('date'))
    #     print(start, event['summary'])
    
    # calendarList().list 
    # "primary"
    
    # if ["accessRole"] in ["reader", "writer"]:
''''''
def soupify(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text)
    return soup
	
def get_schedule(item):

	'''Usage: return start time, end time, and duration of event item.
	Not adjusted for timezone offset.
	start_dt_iso : the datetime stamp of the start time in ISO format
	end_dt_iso : the datetime stamp of the end time in ISO format
	duration: a string-cast time delta'''
	
	start_time = item.find_previous("td", "time").string
	end_time = item.find_next("td", "time").string
	
	start_dt = datetime.strptime(date + " " + start_time, "%A %b. %j, %Y %I:%M %p")
	start_dt_iso = start_dt.isoformat() + 'Z'
	
	end_dt = datetime.strptime(date + " " + end_time, "%A %b. %j, %Y %I:%M %p")
	end_dt_iso = end_dt.isoformat() + 'Z'
	
	duration = str(end_dt-start_dt)
	
	return start_dt_iso, end_dt_iso, duration

def get_social_events(html, t="td", attr="slot-"):
    
	'''Usage: return a generator object to append records 
	for each non-core event to the master dictionary'''

    for tag in html.find_all(t, attr):
        if len(tag.text.strip()) > 0 and int(tag.attrs['colspan']) > 1:
            title = tag.text.strip()
            start_dt, end_dt, duration = get_schedule(tag)
            if tag.find('a'):
                url = tag.a.get("href")
            else:
                url = BASE_URL + BASE_SCHEDULE
            
            attr_dict = {
                        "name": title,
                        "@type": "other",
                        "url": url,
                        "date": date,
                        "start": start_dt,
                        "end": end_dt,
                        "duration": duration
            }
            yield attr_dict
            
def get_href(url):

    '''Usage: return details of individual
    sessions from embedded urls.
    
    room : the room location and number
    level : the intended audience knowledge
    description : short summary of talk
    abstract : longer explanation of talk'''
    
    soup = soupify(BASE_URL + url)
    soup.find("h4")
    
    r = re.compile(r"\n|r\n|\t|r\t|\s{2,3}")
    room = re.sub(r, "", s.find('h4').text)[27:]
    abstract = soup.find("div", "abstract").text
    description = soup.find("div", "description").text
    level = soup.find("dd").text
    
    return room, level, abstract, description

def sessionify(item):
	'''Usage: return attributes of individual sessions.'''

    
    #regex_date = re.compile(r"([A-Z][a-z]+day.*?\d{4})")
    regex_kind = re.compile(r"(slot-)|(\w+)")
    
    contents = item.find("span", "title")
    title = contents.text.strip()
    speaker = item.find("span",  "speaker").text.strip().split(",")
    kind = re.sub(regex_kind, r"\g<2>", item.attrs['class'][1])
    url = contents.a.get("href")
    
    start_dt, end_dt, duration = get_schedule(item)
    room, level, abstract, description = get_href(url)
    
    attr_dict = {
        "name": title,
        "performer": speaker,
        "@type": kind,
        "description": abstract,
        "summary": description,
        "level": level,
        "room": room,
        "url": url,
        "date": date,
        "start": start_dt,
        "end": end_dt,
        "duration": duration
    }
    
    return attr_dict
    
def get_href(url):

    '''Usage: return details of individual
    sessions from embedded urls.
    
    room : the room location and number
    level : the intended audience knowledge
    description : short summary of talk
    abstract : longer explanation of talk'''
    
    soup = soupify(BASE_URL + url)
    soup.find("h4")
    
    r = re.compile(r"\n|r\n|\t|r\t|\s{2,3}")
    room = re.sub(r, "", s.find('h4').text)[27:]
    abstract = soup.find("div", "abstract").text.strip()
    description = soup.find("div", "description").text.strip()
    level = soup.find("dd").text
    
    
    return room, level, abstract, description

def countify(day, **regex):
    '''Usage: return frequency dict of session type per day.'''

    #regex_kind = re.compile(r"(slot-)|(\w+)")
    
    header = day.find_previous("h3").text
    date = re.search(regex_date, header).group()    
    sessions = day.find_all("td", ["slot-talk", "slot-tutorial", "slot-plenary", "slot-discussion"])
    counts = Counter([s.attrs["class"][1] for s in sessions])
    
    print(f"There are {len(sessions)} sessions on {date}:\n")
    freq = {}
    
    for k,v in counts.items():
        new = re.sub(regex_kind, r'\g<2>', k).title()
        freq[new] = v
    for k,v in freq.items():
        print("{} : {}".format(k,v))
    print()
    freq_dict = {
        "date": date,
        "counts": freq
        }
    return date, freq_dict

def get_sessions(html):
    '''Usage: yield attribute dict as evaluated 
    on a session-by-session basis. '''
    sessions = html.find_all("td", ["slot-talk", "slot-tutorial", "slot-plenary", "slot-discussion"])
    
    for item in sessions:
         yield sessionify(item)  

def build_dict(soup):
        
    pydata = {}
    pydata["info"] = {
    "organizer": organizer,
    "sponsor": sponsor,
    "location": location, 
    "address": address,
    "timezone": timezone
    }

    pydata["date"] = []
    pydata["sessions"] = []
    
    regex_date = re.compile(r"([A-Z][a-z]+day.*?\d{4})")
    regex_kind = re.compile(r"(slot-)|(\w+)")
    
    organizer = "PyData"
    sponsor = "NumFocus"
    location = "Microsoft Conference Center"
    address = "11 Times Square, New York, NY 10036"
    timezone = "America/New_York"
    
    days = soup.find_all("table", "calendar table table-bordered")
    
    print(f"There are {len(days)} days in the conference!\n")
    
    for day in days:
        date, freq = countify(day)
        sessions = day.find_all("td", ["slot-talk", "slot-tutorial", "slot-plenary", "slot-discussion"])
        
        for item in get_sessions(day):
            pydata["sessions"].append(item)
            # print(f"Title: {title}\nSpeaker(s): {speaker}\nNumber of Speakers: {len(speaker)}\nKind: {kind}\nStart: {start_dt}\tEnd: {end_dt}\nURL: {url}\nDuration: {duration}\n")        

    
    for item in get_social_events(day, "td", "slot-"):    
        pydata["sessions"].append(item)
        # print(f"Title: {title}\nSpeaker(s): {speaker}\nNumber of Speakers: {len(speaker)}\nKind: {kind}\nStart: {start_dt}\tEnd: {end_dt}\nURL: {url}\nDuration: {duration}\n")     
        
    jsonify(pydata, "events.json")
    
def jsonify(dictionary, fname):
	'''Usage: write attrs to json'''
	
	# check if exists, has file extension
	
	with open(fname, "w") as file:
        json.dump(pydata, file)




'''
to-do;

fix local/global scoping
clean up json schema
tests & error handling
re-link to calendar
nlp and data viz time
'''












	
	
def make_event(url, calendarId="primary", file="events.json"):
    
    with open(fname,"rb") as f:
    	sessions = json.load(f)
    	
    organizer = "PyData",
    location = ""
    timezone = "America/New_York",
    start_dt = ""
    end_dt = ""
    url = url
    summary = ""
	description = ""
    
        
    event = {
    	"organizer": {
    		"displayName": organizer,
    		},
    	"summary:" summary,
    	"start": {
    		"timeZone": time_zone, #IANA Time Zone Database name
    		"dateTime": start_dt, #combined date-time value (formatted according to RFC3339)
    		},
    	"source": {
    		"htmlLink": url,
    		# "title", page_title,
    		},
    	"location": location,
    	"description": description,
    	"end": {
    		# date: yy-mm-dd,
    		"timeZone": time_zone,
    		"dateTime": end_dt
    		},
    
    	}
    return event
    

    event = service.event.insert(calendarId="primary", body=event, sendNotifications=None).execute()
    print(f"Event created: {event.get("htmlLink"}")
# 
if __name__ == '__main__':
    main()