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

## Testing
Frontend:
Setup:
cd frontend
npm init -y  # If no package.json exists
npm install --save-dev jest @testing-library/dom @testing-library/jest-dom

# Run all tests once
npm test

# Run tests in watch mode (auto re-run on file changes)
npm run test:watch

# Run tests with coverage report
npm run test:coverage

# Run tests with verbose output
npm run test:verbose

# Run only unit tests
npm run test:unit

# Run only integration tests
npm run test:integration
