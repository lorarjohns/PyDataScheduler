from __future__ import print_function
from datetime import datetime, timedelta
import re
import json
import pprint
from time import sleep
from tqdm import tqdm

from collections import Counter

import requests
import pickle
import os.path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from bs4 import BeautifulSoup

from ascii_logo import pydata_pride

"""
to-do;

fix local/global scoping - not dry
clean up json schema
tests & error handling
re-link to calendar
nlp and data viz time
"""

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
BASE_URL = "https://pydata.org"
BASE_SCHEDULE = "/nyc2019/schedule/"


def main():

    """
    Usage: Create event for each in schedule.
    """

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    now = datetime.utcnow().isoformat() # 'Z' indicates UTC time
    # print('Getting the upcoming 10 events')
    # result = service.calendarList().list().execute()
    
    cldr = {
    
        'summary': 'PyData NYC 2019',
        'timeZone': 'America/New_York'
                }
                
    new_calendar = service.calendars().insert(body=cldr).execute()

    cldr_id = new_calendar['id']
    

    # events().list(calendarId='primary', timeMin=now,
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

    soup = soupify(BASE_URL + BASE_SCHEDULE)

    sessions = make_sessions_dict(soup)

    jsonify(sessions, "events.json")

    with open("events.json", "rb") as file:
        sessions = json.load(file)

    for i in range(len(sessions["sessions"])):

        organizer = sessions["info"]["organizer"]
        try:
            location = ", ".join(
                [
                    sessions["sessions"][i]["room"],
                    sessions["info"]["location"],
                    sessions["info"]["address"],
                ]
            )
        except:
            location = ", ".join(
                [sessions["info"]["location"], sessions["info"]["address"]]
            )
        summary = sessions["sessions"][i]["name"]
        timezone = sessions["info"]["timezone"]
        start_dt = sessions["sessions"][i]["start"]
        end_dt = sessions["sessions"][i]["end"]
        url = sessions["sessions"][i]["url"]
        description = sessions["sessions"][i]["description"]

        e = {
            "organizer": {"displayName": organizer,},
            "summary": summary,
            "location": location,
            "description": description,
            "start": {
                "dateTime": start_dt,  # combined date-time value (formatted according to RFC3339)
                "timeZone": timezone,
            },
            "source": {"url": url,},
            "end": {
                # date: yy-mm-dd,
                "dateTime": end_dt,
                "timeZone": timezone,
            },
        }

        # event = (
        #     service.events()	
        #     .insert(calendarId=cldr_id, body=e, sendNotifications=True)
        #     .execute()
        # )
        #print(f"Event created! {event['summary']}")
        #sleep(0.1)
    
""""""


def soupify(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup


def get_schedule(item, date):

    """Usage: return start time, end time, and duration of event item.
    Not adjusted for timezone offset.
    start_dt_iso : the datetime stamp of the start time in ISO format
    end_dt_iso : the datetime stamp of the end time in ISO format
    duration: a string-cast time delta"""

    start_time = item.find_previous("td", "time").string
    end_time = item.find_next("td", "time").string

    start_dt = datetime.strptime(date + " " + start_time, "%A %b. %d, %Y %I:%M %p")
    start_dt_iso = str(start_dt.isoformat()) #+ "Z"

    end_dt = datetime.strptime(date + " " + end_time, "%A %b. %d, %Y %I:%M %p")
    end_dt_iso = str(end_dt.isoformat()) #+ "Z"

    duration = str(end_dt - start_dt)
    return start_dt_iso, end_dt_iso, duration


def get_social_events(html, date, t="td", attr="slot-"):

    """Usage: return a generator object to append records 
    for each non-core event to the master dictionary"""

    for tag in tqdm(html.find_all(t, attr)):
        if len(tag.text.strip()) > 0 and int(tag.attrs["colspan"]) > 1:
            title = tag.text.strip()
            start_dt, end_dt, duration = get_schedule(tag, date)
            if tag.find("a"):
                url = tag.a.get("href")
                print(url)  # .a.attrs["href"]
            else:
                url = BASE_URL + BASE_SCHEDULE
            # pydata["sessions"].append()

            attr_dict = {
                "name": title,
                "performer": None,
                "@type": "other",
                "description": None,
                "summary": None,
                "level": None,
                "room": None,
                "url": BASE_URL + url,
                "date": date,
                "start": start_dt,
                "end": end_dt,
                "duration": duration,
            }

            yield attr_dict


def get_href(url):

    """Usage: return details of individual
    sessions from embedded urls.
    
    room : the room location and number
    level : the intended audience knowledge
    description : short summary of talk
    abstract : longer explanation of talk"""

    soup = soupify(BASE_URL + url)

    r = re.compile(r"(?<=in )([A-Za-z\s]+)(\([\d\w]+\))")
    room = re.search(r, soup.find("h4").text)
    try:
        room = "".join(room.groups())
    except:
        room = "Microsoft"

    abstract = soup.find("div", "abstract").text.strip()
    description = soup.find("div", "description").text.strip()
    level = soup.find("dd").text

    return room, level, abstract, description


def sessionify(item, date, *regex):

    """Usage: return attributes of individual sessions."""

    regex_date, regex_kind = regex
    contents = item.find("span", "title")
    title = contents.text.strip()
    speaker = item.find("span", "speaker").text.strip().split(",")
    kind = re.sub(regex_kind, r"\g<2>", item.attrs["class"][1])
    url = contents.a.get("href")

    start_dt, end_dt, duration = get_schedule(item, date)
    room, level, abstract, description = get_href(url)

    attr_dict = {
        "name": title,
        "performer": speaker,
        "@type": kind,
        "description": abstract,
        "summary": description,
        "level": level,
        "room": room,
        "url": BASE_URL + url,
        "date": date,
        "start": start_dt,
        "end": end_dt,
        "duration": duration,
    }

    return attr_dict


def countify(day, *regex):

    """Usage: return frequency dict of session type per day."""

    regex_date, regex_kind = regex
    header = day.find_previous("h3").text
    date = re.search(regex_date, header).group()
    sessions = day.find_all(
        "td", ["slot-talk", "slot-tutorial", "slot-plenary", "slot-discussion"]
    )
    counts = Counter([s.attrs["class"][1] for s in sessions])

    print(f"There are {len(sessions)} sessions on {date}:\n")
    freq = {}

    for k, v in counts.items():
        new = re.sub(regex_kind, r"\g<2>", k).title()
        freq[new] = v
    for k, v in freq.items():
        print("{} : {}".format(k, v))
    print()
    freq_dict = {"date": date, "counts": freq}
    return date, freq_dict


def get_sessions(html, date, *regex):

    """Usage: yield attribute dict as evaluated 
    on a session-by-session basis. """

    regex_date, regex_kind = regex
    sessions = html.find_all(
        "td", ["slot-talk", "slot-tutorial", "slot-plenary", "slot-discussion"]
    )

    for item in tqdm(sessions):
        yield sessionify(item, date, regex_date, regex_kind)


def make_sessions_dict(soup):

    organizer = "PyData"
    sponsor = "NumFocus"
    location = "Microsoft Conference Center"
    address = "11 Times Square, New York, NY 10036"
    timezone = "America/New_York"

    pydata = {}
    pydata["info"] = {
        "organizer": organizer,
        "sponsor": sponsor,
        "location": location,
        "address": address,
        "timezone": timezone,
    }

    pydata["date"] = []
    pydata["sessions"] = []

    regex_date = re.compile(r"([A-Z][a-z]+day.*?\d{4})")
    regex_kind = re.compile(r"(slot-)|(\w+)")

    days = soup.find_all("table", "calendar table table-bordered")

    print(f"There are {len(days)} days in the conference!\n")

    for day in days:
        date, freq = countify(day, regex_date, regex_kind)
        pydata["date"].append({"day": date, "count":freq})
        sessions = day.find_all(
            "td", ["slot-talk", "slot-tutorial", "slot-plenary", "slot-discussion"]
        )

        for item in tqdm(get_sessions(day, date, regex_date, regex_kind)):
            pydata["sessions"].append(item)

    for item in tqdm(get_social_events(day, date, "td", "slot-")):
        pydata["sessions"].append(item)

    return pydata


def jsonify(dictionary, fname):

    """Usage: write attrs to json"""

    # check if exists, has file extension

    with open(fname, "w") as file:
        json.dump(dictionary, file)


if __name__ == "__main__":

    main()
    pydata_pride()