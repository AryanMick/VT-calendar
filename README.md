# VT Calendar - Course Calendar Consolidating Tool

A web application that consolidates course calendars from Canvas, Google Calendar, and Microsoft accounts into one unified calendar for Virginia Tech students.

## Authors
- Ethan Lunsford (ethanl03@vt.edu)
- Sam Jordon (jordo@vt.edu)
- Shoumik Bisoi (shoumik77@vt.edu)
- Aryan Bhowmick (aryanmick@vt.edu)

## Features

- **Canvas Integration**: Automatically sync assignments and due dates from Canvas
- **Google Calendar Integration**: Connect and sync Google Calendar events
- **Microsoft Integration**: Connect Microsoft school accounts
- **Manual Event Management**: Add custom events not found in other platforms
- **Chrome Extension**: Quick access to your consolidated calendar
- **Clean Interface**: Modern, intuitive UI with Virginia Tech branding
- **Notifications**: Reminders for upcoming assignments

## Setup

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn

### Installation

1. Clone the repository:
```bash
cd VTCalender
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the root directory:
```env
PORT=3000
CANVAS_API_URL=https://canvas.vt.edu/api/v1
```

4. Start the server:
```bash
npm start
```

For development with auto-restart:
```bash
npm run dev
```

### Chrome Extension Setup

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" in the top right
3. Click "Load unpacked"
4. Select the `extension` folder from this project
5. The VT Calendar icon will appear in your extensions toolbar

## Usage

1. Open your browser and navigate to `http://localhost:3000`
2. Log in with your Canvas credentials (username@vt.edu)
3. Connect additional calendars (Google, Microsoft) as needed
4. Click "Sync All Calendars" to pull in all events
5. Use the Chrome extension for quick access to your consolidated calendar

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/canvas/assignments?userId={id}` - Fetch Canvas assignments
- `GET /api/google/calendar?userId={id}` - Fetch Google Calendar events
- `GET /api/calendar/events?userId={id}` - Get consolidated events
- `POST /api/calendar/events` - Add manual event
- `PUT /api/calendar/events/:id` - Update event
- `DELETE /api/calendar/events/:id` - Delete event
- `POST /api/calendar/sync` - Sync all calendars

## Database

The application uses SQLite to store:
- User accounts and connections
- Calendar events from all sources
- Connected account tokens (encrypted)

## Development Methodology

Scrum methodology with sprint-based development.

## References

- [Canvas LMS REST API Documentation](https://canvas.instructure.com/doc/api/)
- [Google Calendar API](https://developers.google.com/calendar/api)
- [Microsoft Graph API](https://docs.microsoft.com/graph/api/overview)

## License

MIT License

## Support

For questions or issues, contact the development team.

