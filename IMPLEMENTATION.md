## Ethan - Canvas API Interface
The code in canvas_test.py reaches out to two endpoints: the current users courses, and the current users course assignments. These endpoints return the respective JSON data which is then consolidated into two lists of dictionaries. The first list is for courses, the second is for course assignments. This will serve as the foundation for further implementation where the retrieved information is used to populate the database used by the frontend. This was the expected behavior from the prompt. ChatGPT was used here due to the simplicity of the requirement, as writing queries for a well documented API is trivial for a model such as ChatGPT. As the implementation goes more in depth and is tailored to the application, there will be less usage of AI since it will becomes less dependable.

## Aryan - VT Calender UI
I designed the VT Calendar interface  with HTML, CSS, and JavaScript without the help of any AI or AI tools. I constructed the layout from scratch and used some online examples to guide my choice of palette, button styles, and spacing. The maroon and orange colors stem from Virginia Tech's branding guidelines.  The UI has minor flaws such as two logout buttons which is indicative that this was a  effort working by hand with corrections as I went along. Everything related to the structure, styles, and alignment of content was written by me. This represents a functional first draft of the interface.

## Shoumik - Backend API Documentation
For the code review assignment, I implemented a comprehensive backend API reference in `API.md` that documents all current Flask routes in `backend/app.py`. This includes:
- Authentication endpoints (`/api/auth/register`, `/api/auth/login`, `/api/auth/verify-2fa`)
- Canvas integration (`/api/canvas/link`)
- Calendar event endpoints (`/api/calendar/events` for listing and POST for manual events)
- User settings endpoints (`/api/settings` GET/PUT)
- Google OAuth and calendar endpoints (`/api/auth/google/authorize`, `/api/auth/google/callback`, `/api/google/events`, `/api/google/calendar/sync`)
- Health check (`/api/health`)

The documentation describes request/response shapes, validation rules, authentication behavior (session cookies and optional `userId` parameters), and example payloads. It is aligned with the existing unit and integration tests in `backend/google_test.py` and the Selenium test in `backend/google_calendar.py`, so that the docs match the behavior the tests expect.

AI use: I used the Cascade AI coding assistant to help analyze the existing Flask code and tests, draft the initial structure of `API.md`, and ensure all implemented endpoints were covered accurately. I reviewed and integrated the generated content into the repository, and verified that the documented routes correspond to real endpoints in `backend/app.py`.

