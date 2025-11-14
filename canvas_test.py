"""Module handling interface with Canvas API.

The Canvas API provides multiple endpoints containing the necessary 
information needed to populate the calendar w/ upcoming Canvas assignments.

AI Usage: All code in this module was generated with ChatGPT with the exception 
of the code inside 'if __name__ == "__main__":'. All comments were written by a
member of the team.

Prompts used:
How can I use the Canvas API to pull a users assignments list? 
Give the implementation in python
Write code that iterates over the courses taken in the current semester 
and fetches upcoming assignments
"""
from datetime import datetime, timezone
import requests

# define url of VT Canvas domain
BASE_URL = "https://canvas.vt.edu"  

def get_current_courses(headers):
    """Fetch current users active courses."""

    # define courses endpoint, parameters specify active courses
    url = f"{BASE_URL}/api/v1/courses"
    params = {
        "enrollment_state": "active",
        "include[]": "term"
    }

    # loop over paginated results, add json data objects (dict) to courses list
    courses = []
    while url:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        courses.extend(data)
        url = resp.links.get("next", {}).get("url")
    return courses

def get_upcoming_assignments(course_id, headers):
    """Fetch current users assignments."""

    # define assignments endpoint, based on given course
    url = f"{BASE_URL}/api/v1/courses/{course_id}/assignments"
    assignments = []

    # loop over paginated results, add json objects to assignments list
    while url:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        assignments.extend(data)
        url = resp.links.get("next", {}).get("url")

    # only include upcoming assignments 
    now = datetime.now(timezone.utc)
    upcoming = [
        a for a in assignments
        if a.get("due_at") and datetime.fromisoformat(a["due_at"].replace("Z", "+00:00")) > now
    ]
    return upcoming

def main(headers):
    """Fetch all upcoming assignmented from currently enrolled courses."""
    courses = get_current_courses(headers)
    print(f"Found {len(courses)} active courses.\n")

    for course in courses:
        name = course.get("name", "Unnamed Course")
        course_id = course["id"]

        assignments = get_upcoming_assignments(course_id, headers)
        if assignments:
            print(f"📘 {name}:")
            for a in assignments:
                due_date = a.get("due_at")
                if due_date:
                    due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
                    due_date = due_date.astimezone().strftime("%Y-%m-%d %H:%M")
                print(f"  • {a['name']} (due {due_date})")
            print()
        else:
            print(f"📘 {name}: No upcoming assignments.\n")


if __name__ == "__main__":
    # user token specific to current user
    user_token = ""
    headers = { 
        "Authorization": f"Bearer {user_token}"
    }
    main(headers)