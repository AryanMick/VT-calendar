# VT Calendar - Project Structure

## Overview
Complete web application for consolidating course calendars from Canvas, Google, and Microsoft accounts.

## File Structure

```
VTCalender/
├── server.js                 # Express backend server with API endpoints
├── package.json             # Node.js dependencies and scripts
├── start.sh                 # Unix/Mac startup script
├── start.bat                # Windows startup script
├── env.template             # Environment variables template
├── README.md                # Project documentation
├── USAGE.md                 # Usage guide
├── .gitignore              # Git ignore rules
│
├── public/                  # Frontend files served by Express
│   ├── index.html          # Main HTML interface
│   ├── app.js              # Client-side JavaScript
│   └── style.css           # Styling with VT branding
│
├── extension/               # Chrome extension
│   ├── manifest.json       # Extension manifest
│   ├── popup.html          # Extension popup interface
│   ├── popup.js            # Extension JavaScript
│   └── icons/              # Extension icons
│       ├── icon.svg        # Vector icon
│       ├── icon16.png     # 16x16 icon
│       ├── icon32.png     # 32x32 icon
│       ├── icon48.png     # 48x48 icon
│       └── icon128.png    # 128x128 icon
│
└── (generated at runtime)
    └── calendar.db         # SQLite database

```

## Technology Stack

### Backend
- **Node.js** - Runtime environment
- **Express** - Web framework
- **SQLite3** - Database
- **Axios** - HTTP requests
- **Passport** - Authentication
- **CORS** - Cross-origin resource sharing

### Frontend
- **HTML5** - Markup
- **CSS3** - Styling with VT color scheme
- **JavaScript (ES6+)** - Client-side functionality

### Extension
- **Chrome Extension Manifest V3**
- **HTML/CSS/JS** - Popup interface

## Key Features

1. **Canvas Integration** (`/api/canvas/assignments`)
   - Fetches courses and assignments from Canvas LMS
   - Uses Canvas REST API

2. **Google Calendar Integration** (`/api/google/calendar`)
   - Syncs events from Google Calendar
   - Uses Google Calendar API v3

3. **Microsoft Integration** (Ready for implementation)
   - Connects to Microsoft Graph API
   - Syncs Outlook events

4. **Manual Event Management** (`/api/calendar/events`)
   - Add, update, delete custom events
   - Full CRUD operations

5. **Chrome Extension**
   - Quick access to consolidated calendar
   - Shows upcoming events
   - Lightweight popup interface

## Database Schema

### users
- id (INTEGER PRIMARY KEY)
- canvas_user_id (TEXT)
- google_email (TEXT)
- ms_email (TEXT)
- created_at (DATETIME)

### calendar_events
- id (INTEGER PRIMARY KEY)
- user_id (INTEGER, FOREIGN KEY)
- title (TEXT)
- description (TEXT)
- due_date (DATETIME)
- source (TEXT: Canvas, Google, Manual)
- completed (BOOLEAN)
- reminder_sent (BOOLEAN)

### connected_accounts
- id (INTEGER PRIMARY KEY)
- user_id (INTEGER, FOREIGN KEY)
- account_type (TEXT: Canvas, Google, Microsoft)
- access_token (TEXT, encrypted)
- refresh_token (TEXT, encrypted)
- expires_at (DATETIME)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/users` | Create user account |
| GET | `/api/user/:id` | Get user data |
| GET | `/api/canvas/assignments` | Fetch Canvas assignments |
| GET | `/api/google/calendar` | Fetch Google Calendar events |
| GET | `/api/calendar/events` | Get consolidated events |
| POST | `/api/calendar/events` | Add manual event |
| PUT | `/api/calendar/events/:id` | Update event |
| DELETE | `/api/calendar/events/:id` | Delete event |
| POST | `/api/accounts/connect` | Connect external account |
| POST | `/api/calendar/sync` | Sync all calendars |

## Setup Instructions

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Configure Environment**
   ```bash
   cp env.template .env
   # Edit .env with your API credentials
   ```

3. **Start Server**
   ```bash
   npm start
   # or
   ./start.sh      # Unix/Mac
   start.bat       # Windows
   ```

4. **Load Chrome Extension**
   - Open `chrome://extensions/`
   - Enable Developer mode
   - Click "Load unpacked"
   - Select `extension/` folder

## Development

### Running in Development Mode
```bash
npm run dev
```
Uses nodemon for auto-restart on file changes.

### Environment Variables
Required in `.env`:
- `PORT` - Server port (default: 3000)
- `CANVAS_API_URL` - Canvas API endpoint
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth secret
- `MICROSOFT_CLIENT_ID` - Microsoft OAuth client ID
- `MICROSOFT_CLIENT_SECRET` - Microsoft OAuth secret

## Color Scheme (VT Branding)

- **Maroon**: `#630031` - Primary brand color
- **Orange**: `#CF4520` - Secondary brand color
- **Dark**: `#2C2C2C` - Text color
- **Light**: `#F5F5F5` - Background color
- **Border**: `#E0E0E0` - Border color

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Authors

- **Ethan Lunsford** - ethanl03@vt.edu
- **Sam Jordon** - jordo@vt.edu
- **Shoumik Bisoi** - shoumik77@vt.edu
- **Aryan Bhowmick**

## License

MIT License

