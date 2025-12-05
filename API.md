# VT Calendar Backend API Documentation

## Overview

This document describes all backend API routes for the VT Calendar application.

It is intended for:

- Developers extending the backend or frontend.
- Test writers (unit, integration, Selenium).
- Integrators who need a clear reference of available endpoints, expected inputs, and returned outputs.

The backend is implemented in `backend/app.py` using Flask and SQLite.

---

## Authentication & Conventions

- **Transport & format**
  - All endpoints are HTTP(S) and accept/return **JSON** unless otherwise specified.
  - Requests must set `Content-Type: application/json` when sending JSON bodies.

- **Authentication model**
  - Primary auth is **session-based** using Flask sessions.
  - After successful `POST /api/auth/login` or `POST /api/auth/verify-2fa`, the server sets a **session cookie**.
  - Many endpoints also accept a `userId` in the query string or request body to simplify testing (e.g., `/api/calendar/events?userId=1`), but the canonical user identity is the session.

- **Common response patterns**
  - On success, responses typically include:
    - `success: true`
    - Additional data (e.g., `userId`, `events`, etc.).
  - On error, responses typically include:
    - Appropriate HTTP status (`400`, `401`, `500`, …).
    - An `error` string (and sometimes `error_code`).

- **Timestamps**
  - Timestamps are ISO 8601 strings, e.g. `"2025-01-20T13:00:00Z"`.

---

## Authentication APIs

### POST `/api/auth/register`

Register a new VT Calendar user using a Virginia Tech email.

**Request Body**

```json
{
  "email": "student@vt.edu",
  "password": "PlaintextPassword1",
  "canvasUserId": "optional-canvas-id"
}
```

**Validation rules**

- `email`:
  - Must end with `@vt.edu`.
- `password`:
  - Minimum length: 8 characters.
  - Must contain at least:
    - One uppercase letter.
    - One lowercase letter.
    - One digit.

**Success Response (200 OK)**

```json
{
  "success": true,
  "userId": 1,
  "email": "student@vt.edu"
}
```

**Error Responses**

- `400 Bad Request` – invalid email domain or weak password:
  ```json
  { "error": "Must use a Virginia Tech email (@vt.edu)" }
  ```
  or
  ```json
  { "error": "Password must be at least 8 characters long" }
  ```
- `400 Bad Request` – duplicate email:
  ```json
  { "error": "Email already exists" }
  ```

---

### POST `/api/auth/login`

Password-based login.

**Request Body**

```json
{
  "email": "student@vt.edu",
  "password": "PlaintextPassword1"
}
```

**Behavior**

- Validates VT email domain and password.
- If user does **not** have 2FA enabled:
  - Creates a new session token.
  - Persists it in the `users` table.
  - Sets session cookie.

**Success Response (no 2FA required)**

```json
{
  "success": true,
  "requires2FA": false,
  "userId": 1,
  "sessionToken": "random-session-token"
}
```

**Success Response (2FA required)**

```json
{
  "success": true,
  "requires2FA": true,
  "userId": 1,
  "message": "Two-factor authentication required"
}
```

**Error Responses**

- `400 Bad Request` – invalid VT email:
  ```json
  { "error": "Invalid VT email address" }
  ```
- `401 Unauthorized` – invalid credentials:
  ```json
  { "error": "Invalid credentials" }
  ```

---

### POST `/api/auth/verify-2fa`

Second step for login when the user has 2FA enabled.

**Request Body**

```json
{
  "userId": 1,
  "code": "123456"
}
```

**Behavior**

- Looks up user by `userId`.
- Verifies 2FA is enabled and compares the code against a TOTP-like code derived from a secret.
- Accepts a special development code `"000000"` for testing.
- On success:
  - Generates a new session token.
  - Updates the user.
  - Sets session cookie.

**Success Response**

```json
{
  "success": true,
  "userId": 1,
  "sessionToken": "new-session-token",
  "email": "student@vt.edu"
}
```

**Error Responses**

- `401 Unauthorized` – invalid user or session:
  ```json
  { "error": "Invalid session" }
  ```
- `400 Bad Request` – 2FA not enabled:
  ```json
  { "error": "2FA not enabled for this account" }
  ```
- `401 Unauthorized` – wrong 2FA code:
  ```json
  { "error": "Invalid 2FA code" }
  ```

---

## Canvas Integration APIs

### POST `/api/canvas/link`

Link a Canvas token, import courses, and sync assignments into the local calendar.

**Auth**

- Uses session if available (`session['userId']`).
- Falls back to `userId` in the body for development/testing.

**Request Body**

```json
{
  "userId": 1,
  "canvasToken": "your-canvas-api-token"
}
```

**Behavior**

- Uses the Canvas API to:
  - Fetch enrolled courses.
  - For each course, fetch upcoming assignments.
- Stores courses in `canvas_courses`.
- Stores assignments as rows in `calendar_events` with:
  - `source = "Canvas"`
  - `course_name` and `canvas_course_id` populated.
- Persists the Canvas token in `connected_accounts` (`account_type = "Canvas"`).

**Success Response**

```json
{
  "success": true,
  "coursesLinked": 3,
  "syncedCount": 12
}
```

**Error Responses**

- `400 Bad Request` – missing token:
  ```json
  { "error": "Canvas token required" }
  ```
- `500 Internal Server Error` – failure while calling Canvas or writing data:
  ```json
  { "error": "Failed to link Canvas account" }
  ```

---

## Calendar Event APIs

### GET `/api/calendar/events`

Return all calendar events for a given user, sorted by due date.

**Query Parameters**

- `userId` (optional but recommended for tests) – numeric user ID.
  - If omitted, the backend will try `session['userId']`.

**Example**

```http
GET /api/calendar/events?userId=1
```

**Behavior**

- Reads from `calendar_events` ordered by `due_date ASC`.
- Enriches each event with:
  - `start`
  - `end`
  
  These are set from `due_date` (or `start_time` if present) to make events compatible with Google-style event expectations.

**Example Response**

```json
{
  "events": [
    {
      "id": 1,
      "user_id": 1,
      "title": "Exam 1",
      "description": "Midterm",
      "due_date": "2025-01-20T13:00:00Z",
      "source": "Canvas",
      "course_name": "CS 2104",
      "canvas_course_id": "12345",
      "start": "2025-01-20T13:00:00Z",
      "end": "2025-01-20T13:00:00Z"
    },
    {
      "id": 2,
      "user_id": 1,
      "title": "Team Sync Meeting",
      "description": "",
      "due_date": "2025-01-21T15:00:00Z",
      "source": "Google",
      "course_name": "Primary Calendar",
      "start": "2025-01-21T15:00:00Z",
      "end": "2025-01-21T16:00:00Z"
    }
  ]
}
```

**Notes**

- Tests in `backend/google_test.py` assert that for Google events:
  - `title`, `start`, `end`, and `source` are present.
  - `source == "Google"`.
  - `course_name` is present (used as “calendar name”).

---

### POST `/api/calendar/events`

Create a manual event (not from Canvas or Google).

**Request Body**

```json
{
  "userId": 1,
  "title": "Exam",
  "description": "Midterm for CS 2104",
  "dueDate": "2025-01-20T13:00:00Z"
}
```

**Behavior**

- Inserts a row into `calendar_events` with:
  - `source = "Manual"`.
  - `due_date` derived from `dueDate`.

**Success Response**

```json
{
  "success": true,
  "id": 42
}
```

---

## Settings APIs

### GET `/api/settings`

Return notification & privacy settings for a user.

**Query Parameters**

- `userId` (optional) – numeric user ID.
  - If omitted, uses `session['userId']` if present.

**Behavior**

- Queries `user_settings` by `user_id`.
- If no row exists, inserts a default row then returns it.

**Example Response**

```json
{
  "settings": {
    "id": 1,
    "user_id": 1,
    "email_notifications": 1,
    "push_notifications": 1,
    "reminder_before_hours": 24,
    "reminder_before_minutes": 60,
    "privacy_mode": "standard",
    "data_sharing": 0
  }
}
```

---

### PUT `/api/settings`

Update notification & privacy settings for a user.

**Request Body (example)**

```json
{
  "userId": 1,
  "email_notifications": true,
  "push_notifications": false,
  "reminder_before_hours": 24,
  "reminder_before_minutes": 30,
  "privacy_mode": "strict",
  "data_sharing": false
}
```

**Behavior**

- If a `user_settings` row exists for the user, it is updated.
- Otherwise, a new row is inserted with the provided values.

**Success Response**

```json
{ "success": true }
```

---

## Google OAuth & Calendar APIs

### GET `/api/auth/google/authorize`

Initiate Google OAuth flow for the currently logged-in user.

**Auth**

- Requires `session['user_id']` to be set.
- If not, returns `401 Unauthorized`.

**Success Response**

```json
{
  "success": true,
  "auth_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

**Error Responses**

- `401 Unauthorized` – user not authenticated:
  ```json
  { "error": "Not authenticated" }
  ```
- `500 Internal Server Error` – failure generating auth URL:
  ```json
  {
    "success": false,
    "error": "Failed to initiate Google authentication"
  }
  ```

---

### GET `/api/auth/google/callback`

Handle Google OAuth callback after the user grants permissions.

**Usage**

- This endpoint is typically called by Google directly, not by frontend code.
- On success, it:
  - Exchanges the authorization code for tokens.
  - Uses the Google Calendar API to identify the users primary calendar and email.
  - Stores tokens and metadata in:
    - `connected_accounts` (provider `"google"`).
    - `google_oauth_tokens` (legacy compatibility).
  - Updates `users.google_email`.

**Behavior**

- If no `session['user_id']`, redirects to frontend with an error:
  - `http://localhost:3001/login?error=not_authenticated`.
- On error from Google, redirects:
  - `http://localhost:3001/settings?google_sync_error={error}`.
- On success, redirects:
  - `http://localhost:3001/settings?google_sync=success`.

_No direct JSON body is returned; this is a redirect-based OAuth flow._

---

### GET `/api/google/events`

Fetch upcoming Google Calendar events using stored OAuth tokens.

**Auth**

- Requires `session['user_id']`.

**Behavior**

- Looks up tokens in `connected_accounts` (`provider = "google"`).
- Falls back to `google_oauth_tokens` (legacy).
- Uses the Google Calendar API to:
  - List all calendars.
  - Fetch events for each calendar within the next 30 days.
  - Filter out very old events.
- Returns a flattened list of events.

**Success Response**

```json
{
  "success": true,
  "events": [
    {
      "id": "google_abcdef123",
      "title": "Team Sync Meeting",
      "description": "Weekly sync",
      "start": "2025-01-20T13:00:00Z",
      "end": "2025-01-20T14:00:00Z",
      "location": "Zoom",
      "source": "Google",
      "calendar_id": "primary",
      "calendar_name": "Primary",
      "allDay": false
    }
  ],
  "total_events": 1,
  "calendars": 1
}
```

**Error Responses**

- `401 Unauthorized` – not logged in:
  ```json
  {
    "success": false,
    "error": "Not authenticated"
  }
  ```
- `400 Bad Request` – Google account not connected:
  ```json
  {
    "success": false,
    "error": "Google account not connected",
    "error_code": "not_connected"
  }
  ```
- `500 Internal Server Error` – error talking to Google:
  ```json
  {
    "success": false,
    "error": "Failed to fetch Google Calendar events",
    "details": "..."
  }
  ```

---

### POST `/api/google/calendar/sync`

Mock Google Calendar sync used by automated tests.

**Purpose**

- This endpoint is **not** a real Google sync.
- It inserts two canned Google events into `calendar_events` for the **most recently created user**.
- Used by:
  - `backend/google_test.py`
  - `backend/google_calendar.py` Selenium test

**Behavior**

- Finds `user_id = MAX(id)` from `users`.
- Inserts two events with `source = "Google"`, `course_name` as a calendar-like label, and appropriate `due_date`.
- Returns counts for test assertions.

**Success Response**

```json
{
  "success": true,
  "events_synced": 2,
  "total_events": 2
}
```

**Error Responses**

- If no users exist:
  ```json
  {
    "success": false,
    "error": "No users found to sync",
    "events_synced": 0,
    "calendars_synced": 0
  }
  ```
- `500 Internal Server Error` – on unexpected failure.

---

## Health Check

### GET `/api/health`

Simple health check for the backend.

**Success Response**

```json
{
  "status": "ok",
  "message": "VT Calendar API is running"
}
```

