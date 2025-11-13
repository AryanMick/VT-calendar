from datetime import datetime, timezone
import requests


BASE_URL = "https://canvas.vt.edu"  

def get_current_courses(headers):
    """Fetch the user's currently enrolled active courses."""
    url = f"{BASE_URL}/api/v1/courses"
    params = {
        "enrollment_state": "active",
        "include[]": "term"
    }

    courses = []
    while url:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        courses.extend(data)
        url = resp.links.get("next", {}).get("url")
    return courses

def get_upcoming_assignments(course_id, headers):
    """Fetch assignments that are not yet due."""
    url = f"{BASE_URL}/api/v1/courses/{course_id}/assignments"
    assignments = []

    while url:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        assignments.extend(data)
        url = resp.links.get("next", {}).get("url")

    # Filter by due date
    now = datetime.now(timezone.utc)
    upcoming = [
        a for a in assignments
        if a.get("due_at") and datetime.fromisoformat(a["due_at"].replace("Z", "+00:00")) > now
    ]
    return upcoming

def main(headers):
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


# Example usage
if __name__ == "__main__":
    user_token = ""
    headers = { 
        "Authorization": f"Bearer {user_token}"
    }
    main(headers)