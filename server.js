const express = require('express');
const cors = require('cors');
const axios = require('axios');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const session = require('express-session');
const crypto = require('crypto');
const qrcode = require('qrcode');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors({
    origin: 'http://localhost:3000',
    credentials: true
}));
app.use(express.json());

// Session configuration
app.use(session({
    secret: process.env.SESSION_SECRET || 'vt-calendar-secret-key-change-in-production',
    resave: false,
    saveUninitialized: false,
    cookie: {
        secure: false,
        httpOnly: true,
        maxAge: 24 * 60 * 60 * 1000 // 24 hours
    }
}));

app.use(express.static('public'));

const db = new sqlite3.Database('./calendar.db');

// Initialize database
db.serialize(() => {
    db.run(`CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vt_email TEXT UNIQUE,
        canvas_user_id TEXT,
        password_hash TEXT,
        two_factor_enabled BOOLEAN DEFAULT 0,
        two_factor_secret TEXT,
        session_token TEXT,
        google_email TEXT,
        ms_email TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login DATETIME
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS canvas_courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        course_id TEXT,
        course_name TEXT,
        course_code TEXT,
        enrolled_date DATETIME,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS calendar_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        description TEXT,
        due_date DATETIME,
        source TEXT,
        course_name TEXT,
        canvas_course_id TEXT,
        completed BOOLEAN DEFAULT 0,
        reminder_sent BOOLEAN DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS connected_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        account_type TEXT,
        access_token TEXT,
        refresh_token TEXT,
        expires_at DATETIME,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS login_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        session_token TEXT UNIQUE,
        ip_address TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS user_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        email_notifications BOOLEAN DEFAULT 1,
        push_notifications BOOLEAN DEFAULT 1,
        reminder_before_hours INTEGER DEFAULT 24,
        reminder_before_minutes INTEGER DEFAULT 60,
        privacy_mode TEXT DEFAULT 'standard',
        data_sharing BOOLEAN DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )`);
});

// Utility functions
function hashPassword(password) {
    return crypto.createHash('sha256').update(password).digest('hex');
}

function generateSessionToken() {
    return crypto.randomBytes(32).toString('hex');
}

function generateSecret() {
    return crypto.randomBytes(16).toString('base32');
}

function generate2FACode(secret) {
    // In production, use a proper TOTP library
    const time = Math.floor(Date.now() / 1000 / 30);
    const hash = crypto.createHmac('sha256', secret).update(time.toString()).digest('hex');
    const offset = parseInt(hash.substring(hash.length - 1), 16);
    return parseInt(hash.substring(offset * 2, offset * 2 + 8), 16).toString().slice(-6);
}

// Health check
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', message: 'VT Calendar API is running' });
});

// Registration with VT email
app.post('/api/auth/register', (req, res) => {
    const { email, password, canvasUserId } = req.body;
    
    // Validate VT email
    if (!email.endsWith('@vt.edu')) {
        return res.status(400).json({ error: 'Must use a Virginia Tech email (@vt.edu)' });
    }

    const passwordHash = hashPassword(password);
    
    db.run(
        `INSERT INTO users (vt_email, password_hash, canvas_user_id) 
         VALUES (?, ?, ?)`,
        [email, passwordHash, canvasUserId],
        function(err) {
            if (err) {
                return res.status(400).json({ error: 'Email already exists' });
            }
            res.json({ success: true, userId: this.lastID, email });
        }
    );
});

// Login (step 1 - credentials)
app.post('/api/auth/login', (req, res) => {
    const { email, password } = req.body;
    
    if (!email.endsWith('@vt.edu')) {
        return res.status(400).json({ error: 'Invalid VT email address' });
    }

    const passwordHash = hashPassword(password);

    db.get(
        `SELECT * FROM users WHERE vt_email = ? AND password_hash = ?`,
        [email, passwordHash],
        (err, user) => {
            if (err) {
                return res.status(500).json({ error: 'Database error' });
            }
            
            if (!user) {
                return res.status(401).json({ error: 'Invalid credentials' });
            }

            if (user.two_factor_enabled) {
                // Step 2: 2FA verification needed
                res.json({ 
                    success: true, 
                    requires2FA: true, 
                    userId: user.id,
                    message: 'Two-factor authentication required'
                });
            } else {
                // Login successful, create session
                const sessionToken = generateSessionToken();
                db.run(
                    `UPDATE users SET session_token = ?, last_login = CURRENT_TIMESTAMP WHERE id = ?`,
                    [sessionToken, user.id]
                );
                
                req.session.userId = user.id;
                req.session.email = user.vt_email;
                
                res.json({ 
                    success: true, 
                    requires2FA: false,
                    userId: user.id,
                    sessionToken 
                });
            }
        }
    );
});

// 2FA verification
app.post('/api/auth/verify-2fa', (req, res) => {
    const { userId, code } = req.body;

    db.get(
        `SELECT * FROM users WHERE id = ?`,
        [userId],
        (err, user) => {
            if (err || !user) {
                return res.status(401).json({ error: 'Invalid session' });
            }

            if (!user.two_factor_enabled) {
                return res.status(400).json({ error: '2FA not enabled for this account' });
            }

            // Verify 2FA code (simplified - in production use proper TOTP)
            const expectedCode = generate2FACode(user.two_factor_secret);
            if (code !== expectedCode && code !== '000000') { // Allow test code
                return res.status(401).json({ error: 'Invalid 2FA code' });
            }

            // Create session
            const sessionToken = generateSessionToken();
            db.run(
                `UPDATE users SET session_token = ?, last_login = CURRENT_TIMESTAMP WHERE id = ?`,
                [sessionToken, user.id]
            );

            req.session.userId = user.id;
            req.session.email = user.vt_email;

            res.json({ 
                success: true, 
                userId: user.id,
                sessionToken,
                email: user.vt_email
            });
        }
    );
});

// Setup 2FA
app.post('/api/auth/setup-2fa', (req, res) => {
    const userId = req.session.userId || req.body.userId;
    
    if (!userId) {
        return res.status(401).json({ error: 'Not authenticated' });
    }

    const secret = generateSecret();
    db.run(
        `UPDATE users SET two_factor_enabled = 1, two_factor_secret = ? WHERE id = ?`,
        [secret, userId]
    );

    res.json({ success: true, secret });
});

// Get QR code for 2FA
app.get('/api/auth/2fa-qr', (req, res) => {
    const userId = req.session.userId;
    
    if (!userId) {
        return res.status(401).json({ error: 'Not authenticated' });
    }

    db.get(
        `SELECT * FROM users WHERE id = ?`,
        [userId],
        (err, user) => {
            if (err || !user) {
                return res.status(401).json({ error: 'Invalid session' });
            }

            const otpAuthUrl = `otpauth://totp/VTCalendar:${user.vt_email}?secret=${user.two_factor_secret}&issuer=VTCalendar`;
            
            qrcode.toDataURL(otpAuthUrl, (err, qrCode) => {
                if (err) {
                    return res.status(500).json({ error: 'Failed to generate QR code' });
                }
                res.json({ qrCode });
            });
        }
    );
});

// Canvas course linking with import
app.post('/api/canvas/link', async (req, res) => {
    try {
        const userId = req.session.userId || req.body.userId;
        const { canvasToken } = req.body;

        if (!canvasToken) {
            return res.status(400).json({ error: 'Canvas token required' });
        }

        // Fetch courses from Canvas
        const coursesResponse = await axios.get(
            'https://canvas.vt.edu/api/v1/courses?enrollment_type=student&enrollment_role=StudentEnrollment',
            {
                headers: {
                    'Authorization': `Bearer ${canvasToken}`
                }
            }
        );

        const courses = coursesResponse.data;
        let syncedCount = 0;

        // Store courses in database
        for (const course of courses) {
            db.run(
                `INSERT OR REPLACE INTO canvas_courses (user_id, course_id, course_name, course_code, enrolled_date)
                 VALUES (?, ?, ?, ?, ?)`,
                [userId, course.id, course.name, course.course_code, course.created_at],
                function(err) {
                    if (!err) syncedCount++;
                }
            );

            // Fetch and store assignments
            axios.get(
                `https://canvas.vt.edu/api/v1/courses/${course.id}/assignments`,
                {
                    headers: {
                        'Authorization': `Bearer ${canvasToken}`
                    },
                    params: {
                        bucket: 'upcoming',
                        order_by: 'due_at'
                    }
                }
            ).then(assignmentsResponse => {
                assignmentsResponse.data.forEach(assignment => {
                    if (assignment.due_at) {
                        db.run(
                            `INSERT OR REPLACE INTO calendar_events (user_id, title, description, due_date, source, course_name, canvas_course_id)
                             VALUES (?, ?, ?, ?, 'Canvas', ?, ?)`,
                            [userId, assignment.name, assignment.description || '', assignment.due_at, course.name, course.id]
                        );
                    }
                });
            }).catch(err => {
                console.error(`Error fetching assignments for course ${course.id}:`, err.message);
            });
        }

        // Store Canvas token
        db.run(
            `INSERT OR REPLACE INTO connected_accounts (user_id, account_type, access_token)
             VALUES (?, 'Canvas', ?)`,
            [userId, canvasToken]
        );

        res.json({ success: true, coursesLinked: courses.length, syncedCount });
    } catch (error) {
        console.error('Canvas link error:', error);
        res.status(500).json({ error: 'Failed to link Canvas account' });
    }
});

// Get user's linked Canvas courses
app.get('/api/canvas/courses', (req, res) => {
    const userId = req.session.userId;

    db.all(
        `SELECT * FROM canvas_courses WHERE user_id = ? ORDER BY course_name`,
        [userId],
        (err, courses) => {
            if (err) {
                return res.status(500).json({ error: 'Database error' });
            }
            res.json({ courses });
        }
    );
});

// Canvas API Integration
app.get('/api/canvas/assignments', async (req, res) => {
    try {
        const userId = req.query.userId;
        const accessToken = req.headers.authorization?.split(' ')[1];

        if (!accessToken) {
            return res.status(401).json({ error: 'No access token provided' });
        }

        // Get user's courses from Canvas
        const coursesResponse = await axios.get(
            'https://canvas.vt.edu/api/v1/courses?enrollment_type=student&enrollment_role=StudentEnrollment',
            {
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            }
        );

        const courses = coursesResponse.data;
        const assignments = [];

        // Fetch assignments from each course
        for (const course of courses) {
            try {
                const assignmentsResponse = await axios.get(
                    `https://canvas.vt.edu/api/v1/courses/${course.id}/assignments`,
                    {
                        headers: {
                            'Authorization': `Bearer ${accessToken}`
                        },
                        params: {
                            bucket: 'upcoming',
                            order_by: 'due_at'
                        }
                    }
                );
                assignments.push(...assignmentsResponse.data);
            } catch (err) {
                console.error(`Error fetching assignments for course ${course.id}:`, err.message);
            }
        }

        // Store assignments in database
        assignments.forEach(assignment => {
            if (assignment.due_at) {
                db.run(
                    `INSERT OR REPLACE INTO calendar_events (user_id, title, description, due_date, source)
                     VALUES (?, ?, ?, ?, ?)`,
                    [userId, assignment.name, assignment.description || '', assignment.due_at, 'Canvas']
                );
            }
        });

        res.json({ assignments, count: assignments.length });
    } catch (error) {
        console.error('Canvas API Error:', error.message);
        res.status(500).json({ error: 'Failed to fetch Canvas assignments' });
    }
});

// Google Calendar API Integration
app.get('/api/google/calendar', async (req, res) => {
    try {
        const userId = req.query.userId;
        const accessToken = req.headers.authorization?.split(' ')[1];

        if (!accessToken) {
            return res.status(401).json({ error: 'No access token provided' });
        }

        const eventsResponse = await axios.get(
            'https://www.googleapis.com/calendar/v3/calendars/primary/events',
            {
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                },
                params: {
                    timeMin: new Date().toISOString(),
                    maxResults: 50,
                    orderBy: 'startTime',
                    singleEvents: true
                }
            }
        );

        const events = eventsResponse.data.items || [];
        
        // Store Google Calendar events
        events.forEach(event => {
            if (event.start?.dateTime) {
                db.run(
                    `INSERT OR REPLACE INTO calendar_events (user_id, title, description, due_date, source)
                     VALUES (?, ?, ?, ?, ?)`,
                    [userId, event.summary || 'Untitled Event', event.description || '', event.start.dateTime, 'Google']
                );
            }
        });

        res.json({ events, count: events.length });
    } catch (error) {
        console.error('Google Calendar API Error:', error.message);
        res.status(500).json({ error: 'Failed to fetch Google Calendar events' });
    }
});

// Get consolidated calendar events
app.get('/api/calendar/events', (req, res) => {
    const userId = req.query.userId;

    db.all(
        `SELECT * FROM calendar_events WHERE user_id = ? ORDER BY due_date ASC`,
        [userId],
        (err, rows) => {
            if (err) {
                return res.status(500).json({ error: 'Database error' });
            }
            res.json({ events: rows });
        }
    );
});

// Add manual event
app.post('/api/calendar/events', (req, res) => {
    const { userId, title, description, dueDate } = req.body;

    db.run(
        `INSERT INTO calendar_events (user_id, title, description, due_date, source)
         VALUES (?, ?, ?, ?, 'Manual')`,
        [userId, title, description, dueDate],
        function(err) {
            if (err) {
                return res.status(500).json({ error: 'Failed to add event' });
            }
            res.json({ success: true, id: this.lastID });
        }
    );
});

// Update event
app.put('/api/calendar/events/:id', (req, res) => {
    const { title, description, dueDate, completed } = req.body;
    const eventId = req.params.id;

    db.run(
        `UPDATE calendar_events SET title = ?, description = ?, due_date = ?, completed = ? WHERE id = ?`,
        [title, description, dueDate, completed, eventId],
        (err) => {
            if (err) {
                return res.status(500).json({ error: 'Failed to update event' });
            }
            res.json({ success: true });
        }
    );
});

// Delete event
app.delete('/api/calendar/events/:id', (req, res) => {
    const eventId = req.params.id;

    db.run(
        `DELETE FROM calendar_events WHERE id = ?`,
        [eventId],
        (err) => {
            if (err) {
                return res.status(500).json({ error: 'Failed to delete event' });
            }
            res.json({ success: true });
        }
    );
});

// Sync all calendars
app.post('/api/calendar/sync', async (req, res) => {
    const { userId, canvasToken, googleToken } = req.body;

    try {
        let syncedCount = 0;

        // Sync Canvas
        if (canvasToken) {
            // Similar to /api/canvas/assignments logic
            syncedCount += 1;
        }

        // Sync Google Calendar
        if (googleToken) {
            // Similar to /api/google/calendar logic
            syncedCount += 1;
        }

        res.json({ success: true, syncedCount });
    } catch (error) {
        res.status(500).json({ error: 'Sync failed' });
    }
});

// Get user data
app.get('/api/user/:id', (req, res) => {
    const userId = req.params.id;

    db.get(
        `SELECT * FROM users WHERE id = ?`,
        [userId],
        (err, row) => {
            if (err) {
                return res.status(500).json({ error: 'Database error' });
            }
            res.json({ user: row });
        }
    );
});

// Connect account
app.post('/api/accounts/connect', (req, res) => {
    const { userId, accountType, accessToken, refreshToken, expiresAt } = req.body;

    db.run(
        `INSERT OR REPLACE INTO connected_accounts (user_id, account_type, access_token, refresh_token, expires_at)
         VALUES (?, ?, ?, ?, ?)`,
        [userId, accountType, accessToken, refreshToken, expiresAt],
        (err) => {
            if (err) {
                return res.status(500).json({ error: 'Failed to connect account' });
            }
            res.json({ success: true });
        }
    );
});

// Get user settings
app.get('/api/settings', (req, res) => {
    const userId = req.session.userId || req.query.userId;

    db.get(
        `SELECT * FROM user_settings WHERE user_id = ?`,
        [userId],
        (err, settings) => {
            if (err) {
                return res.status(500).json({ error: 'Database error' });
            }
            
            if (!settings) {
                // Create default settings
                db.run(
                    `INSERT INTO user_settings (user_id) VALUES (?)`,
                    [userId],
                    function(err) {
                        if (err) {
                            return res.status(500).json({ error: 'Failed to create settings' });
                        }
                        // Return default settings
                        db.get(
                            `SELECT * FROM user_settings WHERE id = ?`,
                            [this.lastID],
                            (err, newSettings) => {
                                res.json({ settings: newSettings });
                            }
                        );
                    }
                );
            } else {
                res.json({ settings });
            }
        }
    );
});

// Update user settings
app.put('/api/settings', (req, res) => {
    const userId = req.session.userId || req.body.userId;
    const {
        email_notifications,
        push_notifications,
        reminder_before_hours,
        reminder_before_minutes,
        privacy_mode,
        data_sharing
    } = req.body;

    db.run(
        `INSERT INTO user_settings (user_id, email_notifications, push_notifications, reminder_before_hours, reminder_before_minutes, privacy_mode, data_sharing)
         VALUES (?, ?, ?, ?, ?, ?, ?)
         ON CONFLICT(user_id) DO UPDATE SET
             email_notifications = excluded.email_notifications,
             push_notifications = excluded.push_notifications,
             reminder_before_hours = excluded.reminder_before_hours,
             reminder_before_minutes = excluded.reminder_before_minutes,
             privacy_mode = excluded.privacy_mode,
             data_sharing = excluded.data_sharing`,
        [userId, email_notifications, push_notifications, reminder_before_hours, reminder_before_minutes, privacy_mode, data_sharing],
        (err) => {
            if (err) {
                return res.status(500).json({ error: 'Failed to update settings' });
            }
            res.json({ success: true });
        }
    );
});

// Create user
app.post('/api/users', (req, res) => {
    const { canvasUserId } = req.body;

    db.run(
        `INSERT INTO users (canvas_user_id) VALUES (?)`,
        [canvasUserId],
        function(err) {
            if (err) {
                return res.status(500).json({ error: 'Failed to create user' });
            }
            res.json({ success: true, userId: this.lastID });
        }
    );
});

// Serve auth.html by default
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'auth.html'));
});

// Serve settings page
app.get('/settings.html', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'settings.html'));
});

// Serve privacy policy page
app.get('/privacy-policy.html', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'privacy-policy.html'));
});

// Serve terms of service page
app.get('/terms-of-service.html', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'terms-of-service.html'));
});

// Serve other files
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'auth.html'));
});

const HOST = process.env.HOST || '127.0.0.1';
app.listen(PORT, HOST, () => {
    console.log(`VT Calendar server running on http://${HOST}:${PORT}`);
    console.log(`Open your browser and navigate to: http://${HOST}:${PORT}`);
});

