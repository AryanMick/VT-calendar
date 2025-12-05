# VT Calendar Backend API Documentation

## Overview
This document describes all backend API routes for the VT Calendar application.
It is intended for developers, maintainers, and integrators who need a clear reference of available endpoints, expected inputs, and returned outputs.

---

## 🔐 Authentication APIs

### POST `/api/auth/register`
Register a new user using a VT email.

**Body**
```json
{
  "email": "student@vt.edu",
  "password": "plaintext",
  "canvasUserId": "optional"
}
```

**Responses**
- `200 OK` – user created
- `400 Bad Request` – invalid email or duplicate

---

### POST `/api/auth/login`
Step 1 login (password-based).

**Body**
```json
{
  "email": "student@vt.edu",
  "password": "plaintext"
}
```

**Responses**
- `200 OK` – may require 2FA
- `401 Unauthorized` – invalid credentials

---

### POST `/api/auth/verify-2fa`
Step 2 login if 2FA is enabled.

**Body**
```json
{
  "userId": 1,
  "code": "123456"
}
```

---

### POST `/api/auth/setup-2fa`
Enable two-factor authentication (requires authenticated session).

**Example Response**
```json
{
  "success": true,
  "secret": "xxxxxxxx"
}
```

---

### GET `/api/auth/2fa-qr`
Returns the QR code for enabling 2FA for the authenticated user.

---

## 📚 Canvas Integration APIs

### POST `/api/canvas/link`
Link a Canvas token and import courses + assignments.

**Body**
```json
{
  "userId": 1,
  "canvasToken": "..."
}
```

---

### GET `/api/canvas/courses`
Return all stored Canvas courses for the logged-in user.

---

### GET `/api/canvas/assignments`
Fetch upcoming assignments directly from Canvas API (used during on-demand sync).

---

## 📅 Calendar Event APIs

### GET `/api/calendar/events?userId=1`
Return all events for the specified user, sorted by date.

---

### POST `/api/calendar/events`
Create a manual event.

**Body**
```json
{
  "userId": 1,
  "title": "Exam",
  "description": "Midterm",
  "dueDate": "2025-01-20T13:00:00Z"
}
```

---

### PUT `/api/calendar/events/:id`
Update an existing event by ID.

---

### DELETE `/api/calendar/events/:id`
Delete an event by ID.

---

### POST `/api/calendar/sync`
Trigger a sync of Google + Canvas data for the authenticated user.

---

## 🗓 Google Calendar APIs

### GET `/api/google/calendar`
Fetch upcoming Google events using the stored OAuth token for the authenticated user.

---

## 👤 User APIs

### GET `/api/user/:id`
Fetch basic user profile info by user ID.

---

### POST `/api/users`
Create a new blank user (primarily for internal/debug use).

---

## ⚙️ Settings APIs

### GET `/api/settings`
Return settings for the current user.

---

### PUT `/api/settings`
Update user settings.

**Body** (example)
```json
{
  "userId": 1,
  "email_notifications": true,
  "push_notifications": false
}
```

---

## 🔍 Health Check

### GET `/api/health`
Simple health check.

**Example Response**
```json
{ "status": "ok", "message": "VT Calendar API is running" }
```

---

## 🧩 Notes

- All routes assume session-based authentication unless otherwise noted.
- Some routes additionally accept `userId` as a query or body parameter to simplify development and testing.
- SQLite is used as the primary database for local development.
- This API surface is subject to change as the project evolves; keep this document updated when routes are added or modified.
