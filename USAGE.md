# VT Calendar - Usage Guide

## Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment
Copy the environment template:
```bash
cp env.template .env
```

Edit `.env` with your API credentials (Canvas, Google, Microsoft).

### 3. Start the Server
```bash
npm start
# or for development with auto-restart:
npm run dev
```

### 4. Open in Browser
Navigate to: http://localhost:3000

## Chrome Extension Setup

1. Open Chrome
2. Go to `chrome://extensions/`
3. Enable "Developer mode"
4. Click "Load unpacked"
5. Select the `extension` folder from this project

## Features Guide

### Login
- Enter your Canvas credentials (username@vt.edu)
- Click "Sign In with Canvas"

### Connect Additional Calendars
After logging in:
- Click "Connect Google Calendar" to link your Google account
- Click "Connect Microsoft Account" to link Microsoft

### Sync Calendars
- Click "Sync All Calendars" to pull in all events from connected sources
- Events are organized chronologically

### Add Manual Events
1. Fill in the "Add Manual Event" form at the bottom
2. Enter title, description, and due date
3. Click "Add Event"

### View Events
All events are displayed in chronological order with:
- Source (Canvas, Google, Manual)
- Due date and time
- Description

## API Integration

### Canvas API
- Endpoint: `https://canvas.vt.edu/api/v1`
- Requires OAuth2 authentication
- Fetches courses and assignments

### Google Calendar API
- Endpoint: `https://www.googleapis.com/calendar/v3`
- Requires OAuth2 authentication
- Syncs calendar events

### Microsoft Graph API
- Endpoint: `https://graph.microsoft.com/v1.0`
- Requires OAuth2 authentication
- Syncs Outlook calendar events

## Database

The application uses SQLite (`calendar.db`):
- User accounts stored securely
- Calendar events from all sources
- Connected account tokens (encrypted)

## Troubleshooting

### Server won't start
- Check if port 3000 is available
- Ensure all dependencies are installed
- Check `.env` file exists

### Can't connect to Canvas
- Verify Canvas API credentials in `.env`
- Check network connectivity
- Ensure OAuth tokens are valid

### Extension not loading
- Verify manifest.json is valid
- Check Chrome Developer Tools for errors
- Ensure popup.html and popup.js exist

## Architecture

### Frontend
- `index.html` - Main UI
- `app.js` - Client-side JavaScript
- `style.css` - Stylesheet with VT branding

### Backend
- `server.js` - Express server with API endpoints
- SQLite database for data persistence
- Integration with Canvas, Google, and Microsoft APIs

### Extension
- `extension/popup.html` - Extension popup UI
- `extension/popup.js` - Extension functionality
- `extension/manifest.json` - Chrome extension manifest

## Security Notes

- Never commit `.env` file to version control
- Store API tokens securely
- Use HTTPS in production
- Implement proper authentication in production


