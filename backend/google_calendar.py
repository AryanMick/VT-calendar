"""Module handling interface with Google Calendar API.

The Google Calendar API exposes endpoints to retrieve a user's calendars
and their upcoming events. This module mirrors the structure of
`backend/canvas_test.py` to make combining sources straightforward.

AI Usage: All code in this module was generated with ChatGPT with the exception
of the code inside 'if __name__ == "__main__"'. All comments were written by a
member of the team.

Prompts used:
How can I use the Google Calendar API to pull a user's upcoming events?
Give the implementation in python
Write code that iterates over the user's calendars and fetches upcoming events
"""
from datetime import datetime, timezone
import requests

# base URL of Google Calendar REST API
BASE_URL = "https://www.googleapis.com/calendar/v3"


def get_calendars(headers):
    """Fetch the current user's calendars."""

    # define calendars endpoint, return the list of calendars for the user
    url = f"{BASE_URL}/users/me/calendarList"
    params = {"maxResults": 250}

    # loop over paginated results, add json data objects (dict) to calendars list
    calendars = []
    while url:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        calendars.extend(data.get("items", []))
        page_token = data.get("nextPageToken")
        if page_token:
            url = f"{BASE_URL}/users/me/calendarList"
            params = {"maxResults": 250, "pageToken": page_token}
        else:
            url = None
    return calendars


def get_upcoming_events(calendar_id, headers, time_min=None):
    """Fetch upcoming events for a given calendar."""

    # default to now if no lower bound is provided
    if time_min is None:
        time_min = datetime.now(timezone.utc).isoformat()

    # define events endpoint for a specific calendar, parameters select upcoming events
    url = f"{BASE_URL}/calendars/{calendar_id}/events"
    params = {
        "timeMin": time_min,
        "singleEvents": True,
        "orderBy": "startTime",
        "maxResults": 2500,
    }

    # loop over paginated results, add json objects to events list
    events = []
    while True:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        events.extend(data.get("items", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
        params["pageToken"] = page_token
    return events


def main(headers):
    """Fetch all upcoming events from the user's calendars."""

    calendars = get_calendars(headers)
    print(f"Found {len(calendars)} calendars.\n")

    # iterate over calendars and print upcoming events in a readable format
    now = datetime.now(timezone.utc)
    for cal in calendars:
        cal_id = cal.get("id")
        cal_summary = cal.get("summary", "Unnamed Calendar")

        events = get_upcoming_events(cal_id, headers)
        upcoming = []
        for e in events:
            start = e.get("start", {})
            when = start.get("dateTime") or start.get("date")
            if not when:
                continue
            # handle both timed and all-day events
            if "T" in when:
                dt = datetime.fromisoformat(when.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(when + "T00:00:00+00:00")
            if dt >= now:
                upcoming.append((dt, e))

        if upcoming:
            print(f"🗓️ {cal_summary}:")
            for dt, e in upcoming:
                title = e.get("summary", "(No title)")
                display = dt.astimezone().strftime("%Y-%m-%d %H:%M")
                print(f"  • {title} (starts {display})")
            print()
        else:
            print(f"🗓️ {cal_summary}: No upcoming events.\n")


if __name__ == "__main__":
    # user access token (OAuth 2.0) with calendar.readonly scope
    access_token = ""
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    main(headers)
