"""Module containing tests for functions in canvas_import_starter.py

AI Usage: All code in this module was generated using ChatGPT.

Prompt used:
Write a suite of unit tests using mocking for the following Canvas API interface code: 
[code contained in canvas_import_starter] 
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
import pytest

from backend.canvas_import_starter import (
    get_current_courses,
    get_upcoming_assignments,
    main,
    BASE_URL,
)

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def make_mock_response(json_data, next_url=None):
    """Create a mock requests.get response."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = json_data
    mock_resp.links = {"next": {"url": next_url}} if next_url else {}
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# -------------------------------------------------------------------
# Tests for get_current_courses()
# -------------------------------------------------------------------

@patch("requests.get")
def test_get_current_courses_single_page(mock_get):
    mock_get.return_value = make_mock_response(
        json_data=[{"id": 1, "name": "Course A"}],
        next_url=None
    )

    headers = {"Authorization": "Bearer fake"}
    result = get_current_courses(headers)

    assert len(result) == 1
    assert result[0]["name"] == "Course A"

    mock_get.assert_called_once()
    mock_get.assert_called_with(
        f"{BASE_URL}/api/v1/courses",
        headers=headers,
        params={"enrollment_state": "active", "include[]": "term"},
    )


@patch("requests.get")
def test_get_current_courses_paginated(mock_get):
    # page 1
    r1 = make_mock_response(
        json_data=[{"id": 1}, {"id": 2}],
        next_url="next_page_url"
    )
    # page 2
    r2 = make_mock_response(
        json_data=[{"id": 3}],
        next_url=None
    )

    mock_get.side_effect = [r1, r2]

    headers = {}
    result = get_current_courses(headers)

    assert len(result) == 3
    assert [c["id"] for c in result] == [1, 2, 3]


# -------------------------------------------------------------------
# Tests for get_upcoming_assignments()
# -------------------------------------------------------------------

@patch("requests.get")
def test_get_upcoming_assignments_filters_past(mock_get):
    now = datetime.now(timezone.utc)

    assignments = [
        {"name": "Past Work", "due_at": (now - timedelta(days=1)).isoformat()},
        {"name": "Future Work", "due_at": (now + timedelta(days=1)).isoformat()}
    ]

    mock_get.return_value = make_mock_response(assignments)

    result = get_upcoming_assignments(course_id=123, headers={})

    assert len(result) == 1
    assert result[0]["name"] == "Future Work"


@patch("requests.get")
def test_get_upcoming_assignments_pagination(mock_get):
    now = datetime.now(timezone.utc)

    # Page 1 has one future assignment
    r1 = make_mock_response(
        [{"name": "A1", "due_at": (now + timedelta(hours=5)).isoformat()}],
        next_url="next_page"
    )
    # Page 2 has one more
    r2 = make_mock_response(
        [{"name": "A2", "due_at": (now + timedelta(hours=10)).isoformat()}],
        next_url=None
    )
    mock_get.side_effect = [r1, r2]

    result = get_upcoming_assignments(course_id=55, headers={})

    assert len(result) == 2
    assert {a["name"] for a in result} == {"A1", "A2"}


@patch("requests.get")
def test_get_upcoming_assignments_no_due_dates(mock_get):
    mock_get.return_value = make_mock_response(
        [{"name": "No Due"}]
    )

    result = get_upcoming_assignments(course_id=10, headers={})

    assert result == []


# -------------------------------------------------------------------
# Tests for main()
# -------------------------------------------------------------------

@patch("builtins.print")
@patch("backend.canvas_import_starter.get_upcoming_assignments")
@patch("backend.canvas_import_starter.get_current_courses")
def test_main_prints_correct_output(mock_courses, mock_assign, mock_print):
    # Mock course list
    mock_courses.return_value = [
        {"id": 1, "name": "Math"},
        {"id": 2, "name": "History"},
    ]

    # Mock upcoming assignments per course
    mock_assign.side_effect = [
        [{"name": "HW1", "due_at": datetime.now(timezone.utc).isoformat()}],
        []
    ]

    main(headers={})

    # First line: number of courses
    mock_print.assert_any_call("Found 2 active courses.\n")

    # Should print assignments for Math
    printed = " ".join(str(call) for call in mock_print.call_args_list)
    assert "📘 Math:" in printed
    assert "HW1" in printed

    # Should print no assignments for History
    assert "📘 History: No upcoming assignments." in printed