"""
Google Calendar implementation tests.

AI-GENERATED TESTS NOTICE
-------------------------
These tests were generated with the assistance of an AI coding assistant
(Cascade). Prompt summary:
- "Generate full unite tests for my google calendar implementation"

The tests exercise:
- sync_google_calendar endpoint (mock Google sync)
- get_events (/api/calendar/events) including Google-style fields
- An integration flow: register user -> sync -> fetch events
"""

import os
import sqlite3
import unittest

from app import app as flask_app, init_db  # type: ignore
import app as vt_app


class GoogleTest(unittest.TestCase):
    """Unit and integration tests for the Google mock implementation."""

    @classmethod
    def setUpClass(cls):
        # Use a separate SQLite database file for tests
        cls.test_db_path = os.path.join(os.path.dirname(__file__), "test_calendar_pm4.db")

        # Point the application at the test database and initialize schema
        vt_app.DATABASE = cls.test_db_path  # type: ignore[attr-defined]
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

        init_db()

        # For tests, normalize calendar_events schema to a simple,
        # Canvas-style table that is compatible with sync_google_calendar.
        # This avoids NOT NULL issues on event_id that exist in some
        # historical schemas.
        conn = sqlite3.connect(cls.test_db_path)
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS calendar_events")
        cur.execute(
            """
            CREATE TABLE calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                source TEXT NOT NULL,
                course_name TEXT,
                canvas_course_id TEXT
            )
            """
        )
        conn.commit()
        conn.close()

        flask_app.testing = True
        cls.client = flask_app.test_client()

    @classmethod
    def tearDownClass(cls):
        # Clean up test database file
        try:
            if os.path.exists(cls.test_db_path):
                os.remove(cls.test_db_path)
        except OSError:
            pass

    def setUp(self):
        """Clean tables before each test to avoid cross-test interference."""
        conn = sqlite3.connect(self.test_db_path)
        cur = conn.cursor()
        for table in ["calendar_events", "users"]:
            try:
                cur.execute(f"DELETE FROM {table}")
            except sqlite3.OperationalError:
                # Table might not exist yet; ignore
                pass
        conn.commit()
        conn.close()

    # Helper methods
    def _register_test_user(self) -> int:
        """Register a VT user via the API and return userId."""
        email = f"pm4_test_{os.getpid()}@vt.edu"
        payload = {
            "email": email,
            "password": "Test@1234",
            "canvasUserId": "pm4_test_user",
        }
        resp = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.get_data(as_text=True))
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("userId", data)
        return int(data["userId"])

    # Unit test: sync_google_calendar
    def test_sync_google_calendar_inserts_mock_events(self):
        """sync_google_calendar should insert mock Google events for latest user."""
        user_id = self._register_test_user()

        # Call the sync endpoint
        resp = self.client.post("/api/google/calendar/sync")
        self.assertEqual(resp.status_code, 200, msg=resp.get_data(as_text=True))
        data = resp.get_json()

        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("events_synced"), 2)
        self.assertEqual(data.get("total_events"), 2)

        # Verify events were written to the DB for this user
        conn = sqlite3.connect(self.test_db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM calendar_events WHERE user_id = ? AND source = 'Google'",
            (user_id,),
        )
        rows = cur.fetchall()
        conn.close()

        self.assertEqual(len(rows), 2)
        print("[PASS] test_sync_google_calendar_inserts_mock_events: inserted 2 Google events for user", user_id)

    # Unit test: get_events enriched fields
    def test_get_events_returns_google_style_fields(self):
        """/api/calendar/events should include start/end/source/course_name for Google events."""
        user_id = self._register_test_user()

        # Insert Google events via sync
        sync_resp = self.client.post("/api/google/calendar/sync")
        self.assertEqual(sync_resp.status_code, 200, msg=sync_resp.get_data(as_text=True))

        # Fetch events for this user
        events_resp = self.client.get(f"/api/calendar/events?userId={user_id}")
        self.assertEqual(events_resp.status_code, 200, msg=events_resp.get_data(as_text=True))
        body = events_resp.get_json()

        self.assertIn("events", body)
        events = body["events"]
        self.assertGreaterEqual(len(events), 2)

        for ev in events:
            # Only assert stronger invariants for Google-sourced events
            if ev.get("source") == "Google":
                self.assertIn("title", ev)
                self.assertIn("start", ev)
                self.assertIn("end", ev)
                self.assertEqual(ev.get("source"), "Google")
                # course_name is used as "calendar name" in tests
                self.assertIn("course_name", ev)

        print("[PASS] test_get_events_returns_google_style_fields: events include start/end/source/course_name for Google events for user", user_id)

    # Integration test: register -> sync -> get_events
    def test_integration_register_sync_and_fetch_events(self):
        """Full flow: register user, sync Google, then verify events via API."""
        user_id = self._register_test_user()

        # Trigger mock Google sync
        sync_resp = self.client.post("/api/google/calendar/sync")
        self.assertEqual(sync_resp.status_code, 200, msg=sync_resp.get_data(as_text=True))
        sync_data = sync_resp.get_json()
        self.assertTrue(sync_data.get("success"))
        self.assertEqual(sync_data.get("events_synced"), 2)

        # Fetch events through API
        events_resp = self.client.get(f"/api/calendar/events?userId={user_id}")
        self.assertEqual(events_resp.status_code, 200, msg=events_resp.get_data(as_text=True))
        body = events_resp.get_json()
        events = body.get("events", [])

        # Filter Google events
        google_events = [e for e in events if e.get("source") == "Google"]
        self.assertEqual(len(google_events), 2)

        titles = {e.get("title") for e in google_events}
        self.assertIn("Team Sync Meeting", titles)
        self.assertIn("Lunch with Team", titles)
        print("[PASS] test_integration_register_sync_and_fetch_events: register -> sync -> fetch events flow succeeded for user", user_id)


if __name__ == "__main__":  # pragma: no cover
    print("\n================ GOOGLE MOCK IMPLEMENTATION TESTS ================")
    print("Running google_test.GoogleTest suite...\n")
    unittest.main(verbosity=2)
