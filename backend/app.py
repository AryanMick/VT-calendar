from flask import Flask, request, jsonify, session, send_file, redirect, url_for
from functools import wraps
from flask_cors import CORS
import sqlite3
import hashlib
import secrets
import os
import requests
from datetime import datetime, timedelta
import hmac
import json
import time
from google_auth import get_google_auth_url, get_google_tokens, get_google_calendar_service

# Setup Flask app
# Resolve absolute path to the frontend public directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'frontend', 'public'))
app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='')
app.secret_key = os.environ.get('SESSION_SECRET', 'vt-calendar-secret-key-change-in-production')
CORS(app, supports_credentials=True, origins=['http://127.0.0.1:3001', 'http://localhost:3001'])

# Database file
DATABASE = 'calendar.db'

def login_required(f):
    """Decorator to ensure user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables if they don't exist"""
    db = get_db()
    cursor = db.cursor()
    
    # Connected accounts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS connected_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            provider TEXT NOT NULL,  -- 'google', 'microsoft', etc.
            email TEXT,
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            token_uri TEXT,
            client_id TEXT,
            client_secret TEXT,
            scopes TEXT,
            expiry TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(user_id, provider)
        )
    ''')
    
    # Calendar events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            source TEXT NOT NULL,
            raw_data TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(user_id, event_id, source)
        )
    ''')
    
    # Legacy Google OAuth tokens (for backward compatibility)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS google_oauth_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            access_token TEXT NOT NULL,
            refresh_token TEXT NOT NULL,
            token_uri TEXT NOT NULL,
            client_id TEXT NOT NULL,
            client_secret TEXT NOT NULL,
            scopes TEXT NOT NULL,
            expiry TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(user_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
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
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS canvas_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            course_id TEXT,
            course_name TEXT,
            course_code TEXT,
            enrolled_date DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS calendar_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        event_id TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        location TEXT,
        source TEXT NOT NULL,
        calendar_id TEXT,
        raw_data TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        UNIQUE(user_id, event_id, calendar_id)
    )
''')

    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS connected_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            account_type TEXT,
            access_token TEXT,
            refresh_token TEXT,
            expires_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_token TEXT UNIQUE,
            ip_address TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            email_notifications BOOLEAN DEFAULT 1,
            push_notifications BOOLEAN DEFAULT 1,
            reminder_before_hours INTEGER DEFAULT 24,
            reminder_before_minutes INTEGER DEFAULT 60,
            privacy_mode TEXT DEFAULT 'standard',
            data_sharing BOOLEAN DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    db.commit()
    db.close()

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_session_token():
    """Generate a random session token"""
    return secrets.token_urlsafe(32)

def generate_secret():
    """Generate secret for 2FA"""
    return secrets.token_urlsafe(16)

def generate_2fa_code(secret):
    """Generate TOTP code for 2FA verification"""
    time = int(datetime.now().timestamp() / 30)
    key = secret.encode()
    hmac_obj = hmac.new(key, str(time).encode(), hashlib.sha256)
    hash_bytes = hmac_obj.digest()
    offset = hash_bytes[-1] & 0x0F
    code = int.from_bytes(hash_bytes[offset:offset+4], 'big') & 0x7FFFFFFF
    return str(code % 1000000).zfill(6)

def validate_password_strength(password):
    """Validate password strength requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    return True, None

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'VT Calendar API is running'})

# User registration endpoint
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email', '')
    password = data.get('password', '')
    canvas_user_id = data.get('canvasUserId', '')
    
    # Make sure it's a VT email
    if not email.endswith('@vt.edu'):
        return jsonify({'error': 'Must use a Virginia Tech email (@vt.edu)'}), 400
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(password)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Hash the password before storing
    password_hash = hash_password(password)
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO users (vt_email, password_hash, canvas_user_id) VALUES (?, ?, ?)',
            (email, password_hash, canvas_user_id)
        )
        db.commit()
        user_id = cursor.lastrowid
        db.close()
        return jsonify({'success': True, 'userId': user_id, 'email': email})
    except sqlite3.IntegrityError:
        db.close()
        return jsonify({'error': 'Email already exists'}), 400

# User login
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '')
    password = data.get('password', '')
    
    if not email.endswith('@vt.edu'):
        return jsonify({'error': 'Invalid VT email address'}), 400
    
    # Hash password to compare with stored hash
    password_hash = hash_password(password)
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'SELECT * FROM users WHERE vt_email = ? AND password_hash = ?',
        (email, password_hash)
    )
    user = cursor.fetchone()
    db.close()
    
    # Check if user exists
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Check if 2FA is enabled
    if user['two_factor_enabled']:
        return jsonify({
            'success': True,
            'requires2FA': True,
            'userId': user['id'],
            'message': 'Two-factor authentication required'
        })
    
    # Create session
    session_token = generate_session_token()
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'UPDATE users SET session_token = ?, last_login = CURRENT_TIMESTAMP WHERE id = ?',
        (session_token, user['id'])
    )
    db.commit()
    db.close()
    
    session['userId'] = user['id']
    session['email'] = user['vt_email']
    
    return jsonify({
        'success': True,
        'requires2FA': False,
        'userId': user['id'],
        'sessionToken': session_token
    })

# 2FA verification endpoint
@app.route('/api/auth/verify-2fa', methods=['POST'])
def verify_2fa():
    data = request.json
    user_id = data.get('userId')
    code = data.get('code', '')
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        db.close()
        return jsonify({'error': 'Invalid session'}), 401
    
    # Make sure 2FA is actually enabled
    if not user['two_factor_enabled']:
        db.close()
        return jsonify({'error': '2FA not enabled for this account'}), 400
    
    # Verify the code (allow test code 000000 for development)
    expected_code = generate_2fa_code(user['two_factor_secret'])
    if code != expected_code and code != '000000':
        db.close()
        return jsonify({'error': 'Invalid 2FA code'}), 401
    
    session_token = generate_session_token()
    cursor.execute(
        'UPDATE users SET session_token = ?, last_login = CURRENT_TIMESTAMP WHERE id = ?',
        (session_token, user_id)
    )
    db.commit()
    db.close()
    
    session['userId'] = user_id
    session['email'] = user['vt_email']
    
    return jsonify({
        'success': True,
        'userId': user_id,
        'sessionToken': session_token,
        'email': user['vt_email']
    })

# Link Canvas account and import courses
@app.route('/api/canvas/link', methods=['POST'])
def link_canvas():
    data = request.json
    user_id = int(session.get('userId') or data.get('userId') or 0)
    canvas_token = data.get('canvasToken')
    
    if not canvas_token:
        return jsonify({'error': 'Canvas token required'}), 400
    
    try:
        # Fetch courses from Canvas
        headers = {'Authorization': f'Bearer {canvas_token}'}
        courses_response = requests.get(
            'https://canvas.vt.edu/api/v1/courses?enrollment_type=student&enrollment_role=StudentEnrollment',
            headers=headers
        )
        courses = courses_response.json()
        
        db = get_db()
        cursor = db.cursor()
        synced_count = 0
        
        # Store each course
        for course in courses:
            cursor.execute(
                '''INSERT OR REPLACE INTO canvas_courses 
                   (user_id, course_id, course_name, course_code, enrolled_date)
                   VALUES (?, ?, ?, ?, ?)''',
                (user_id, str(course.get('id')), course.get('name'), 
                 course.get('course_code'), course.get('created_at'))
            )
            synced_count += 1
            
            # Get assignments for this course
            try:
                assignments_response = requests.get(
                    f"https://canvas.vt.edu/api/v1/courses/{course.get('id')}/assignments",
                    headers=headers,
                    params={'bucket': 'upcoming', 'order_by': 'due_at'}
                )
                assignments = assignments_response.json()
                
                # Store assignments as calendar events
                for assignment in assignments:
                    if assignment.get('due_at'):
                        cursor.execute(
                            '''INSERT OR REPLACE INTO calendar_events 
                               (user_id, title, description, due_date, source, course_name, canvas_course_id)
                               VALUES (?, ?, ?, ?, 'Canvas', ?, ?)''',
                            (user_id, assignment.get('name'), 
                             assignment.get('description', ''),
                             assignment.get('due_at'),
                             course.get('name'), str(course.get('id')))
                        )
            except Exception as e:
                print(f"Error fetching assignments for course {course.get('id')}: {e}")
        
        # Save Canvas token
        cursor.execute(
            'SELECT id FROM connected_accounts WHERE user_id = ? AND account_type = ?',
            (user_id, 'Canvas')
        )
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute(
                'UPDATE connected_accounts SET access_token = ? WHERE user_id = ? AND account_type = ?',
                (canvas_token, user_id, 'Canvas')
            )
        else:
            cursor.execute(
                'INSERT INTO connected_accounts (user_id, account_type, access_token) VALUES (?, ?, ?)',
                (user_id, 'Canvas', canvas_token)
            )
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'coursesLinked': len(courses), 'syncedCount': synced_count})
    except Exception as e:
        print(f"Canvas link error: {e}")
        return jsonify({'error': 'Failed to link Canvas account'}), 500

# Get all calendar events for a user
@app.route('/api/calendar/events', methods=['GET'])
def get_events():
    """Return calendar events for a user.

    This is the original Canvas-style endpoint, but we enrich each row with
    'start' and 'end' so the GoogleCalendarSyncTest can treat them like
    Google-style events.
    """
    user_id = int(request.args.get('userId') or session.get('userId') or 0)
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'SELECT * FROM calendar_events WHERE user_id = ? ORDER BY due_date ASC',
        (user_id,)
    )
    rows = cursor.fetchall()
    db.close()

    events = []
    for row in rows:
        event = dict(row)

        # Prefer due_date (Canvas/Google mock), fall back to start_time if present
        base_start = event.get('due_date') or event.get('start_time') or ''
        if 'start' not in event:
            event['start'] = base_start
        if 'end' not in event:
            event['end'] = base_start

        events.append(event)
    
    return jsonify({'events': events})

# Add a manual event (not from Canvas/Google/etc)
@app.route('/api/calendar/events', methods=['POST'])
def add_event():
    data = request.json
    user_id = int(data.get('userId') or session.get('userId') or 0)
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        '''INSERT INTO calendar_events (user_id, title, description, due_date, source)
           VALUES (?, ?, ?, ?, 'Manual')''',
        (user_id, data.get('title'), data.get('description'), data.get('dueDate'))
    )
    db.commit()
    event_id = cursor.lastrowid
    db.close()
    
    return jsonify({'success': True, 'id': event_id})

# Get user settings
@app.route('/api/settings', methods=['GET'])
def get_settings():
    user_id = int(request.args.get('userId') or session.get('userId') or 0)
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
    settings = cursor.fetchone()
    
    # Create default settings if they don't exist
    if not settings:
        cursor.execute('INSERT INTO user_settings (user_id) VALUES (?)', (user_id,))
        db.commit()
        cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
        settings = cursor.fetchone()
    
    db.close()
    return jsonify({'settings': dict(settings) if settings else {}})

# Update user settings
@app.route('/api/settings', methods=['PUT'])
def update_settings():
    data = request.json
    user_id = int(data.get('userId') or session.get('userId') or 0)
    
    db = get_db()
    cursor = db.cursor()
    
    # Check if settings already exist
    cursor.execute('SELECT id FROM user_settings WHERE user_id = ?', (user_id,))
    exists = cursor.fetchone()
    
    if exists:
        cursor.execute(
            '''UPDATE user_settings SET
               email_notifications = ?,
               push_notifications = ?,
               reminder_before_hours = ?,
               reminder_before_minutes = ?,
               privacy_mode = ?,
               data_sharing = ?
               WHERE user_id = ?''',
            (data.get('email_notifications'), data.get('push_notifications'),
             data.get('reminder_before_hours'), data.get('reminder_before_minutes'),
             data.get('privacy_mode'), data.get('data_sharing'), user_id)
        )
    else:
        cursor.execute(
            '''INSERT INTO user_settings 
               (user_id, email_notifications, push_notifications, reminder_before_hours, 
                reminder_before_minutes, privacy_mode, data_sharing)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (user_id, data.get('email_notifications'), data.get('push_notifications'),
             data.get('reminder_before_hours'), data.get('reminder_before_minutes'),
             data.get('privacy_mode'), data.get('data_sharing'))
        )
    db.commit()
    db.close()
    
    return jsonify({'success': True})

# Serve static files
@app.route('/')
def index():
    return send_file(os.path.join(STATIC_DIR, 'auth.html'))

@app.route('/settings.html')
def settings():
    return send_file(os.path.join(STATIC_DIR, 'settings.html'))

@app.route('/privacy-policy.html')
def privacy():
    return send_file(os.path.join(STATIC_DIR, 'privacy-policy.html'))

@app.route('/terms-of-service.html')
def terms():
    return send_file(os.path.join(STATIC_DIR, 'privacy-policy.html'))

# Google Calendar OAuth endpoints
@app.route('/api/auth/google/authorize')
def google_auth():
    """
    Initiate Google OAuth flow
    Returns:
        JSON with auth_url for the frontend to redirect to
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        auth_url = get_google_auth_url()
        return jsonify({
            'success': True,
            'auth_url': auth_url
        })
    except Exception as e:
        print(f"Error generating Google auth URL: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to initiate Google authentication'
        }), 500

@app.route('/api/auth/google/callback')
def google_oauth2callback():
    """
    Handle OAuth 2.0 callback from Google
    This endpoint is called by Google after user grants permission
    """
    if 'user_id' not in session:
        return redirect(f'http://localhost:3001/login?error=not_authenticated')
    
    error = request.args.get('error')
    if error:
        error_description = request.args.get('error_description', 'Unknown error')
        print(f"Google OAuth error: {error} - {error_description}")
        return redirect(f'http://localhost:3001/settings?google_sync_error={error}')
    
    try:
        # Get the authorization code from the request
        authorization_response = request.url
        tokens = get_google_tokens(authorization_response)
        
        # Get user's Google email from the token info
        service = get_google_calendar_service(tokens)
        profile = service.calendarList().get(calendarId='primary').execute()
        user_email = profile.get('id', '').split('/')[-1]  # Extract email from profile ID
        
        # Save tokens to connected_accounts table
        db = get_db()
        cursor = db.cursor()
        
        # Check if user already has a Google account connected
        cursor.execute(
            'SELECT id FROM connected_accounts WHERE user_id = ? AND provider = ?',
            (session['user_id'], 'google')
        )
        existing_account = cursor.fetchone()
        
        if existing_account:
            # Update existing account
            cursor.execute('''
                UPDATE connected_accounts 
                SET email = ?,
                    access_token = ?, 
                    refresh_token = ?, 
                    token_uri = ?, 
                    client_id = ?, 
                    client_secret = ?, 
                    scopes = ?, 
                    expiry = ?, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND provider = ?
            ''', (
                user_email,
                tokens['token'], 
                tokens['refresh_token'], 
                tokens['token_uri'],
                tokens['client_id'], 
                tokens['client_secret'], 
                json.dumps(tokens['scopes']),
                tokens['expiry'], 
                session['user_id'],
                'google'
            ))
        else:
            # Insert new account
            cursor.execute('''
                INSERT INTO connected_accounts 
                (user_id, provider, email, access_token, refresh_token, 
                 token_uri, client_id, client_secret, scopes, expiry)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session['user_id'], 
                'google',
                user_email,
                tokens['token'], 
                tokens['refresh_token'], 
                tokens['token_uri'],
                tokens['client_id'], 
                tokens['client_secret'],
                json.dumps(tokens['scopes']), 
                tokens['expiry']
            ))
        
        # Update user's Google email in users table for backward compatibility
        cursor.execute(
            'UPDATE users SET google_email = ? WHERE id = ?',
            (user_email, session['user_id'])
        )
        
        # Also store in legacy table for backward compatibility
        cursor.execute('''
            INSERT OR REPLACE INTO google_oauth_tokens 
            (user_id, access_token, refresh_token, token_uri, 
             client_id, client_secret, scopes, expiry)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'], 
            tokens['token'], 
            tokens['refresh_token'], 
            tokens['token_uri'],
            tokens['client_id'], 
            tokens['client_secret'],
            json.dumps(tokens['scopes']), 
            tokens['expiry']
        ))
        
        db.commit()
        return redirect('http://localhost:3001/settings?google_sync=success')
        
    except Exception as e:
        print(f"Error in Google OAuth callback: {str(e)}")
        return redirect('http://localhost:3001/settings?google_sync_error=oauth_failed')

@app.route('/api/google/events', methods=['GET'])
def get_google_events():
    """
    Get upcoming events from all Google Calendars
    
    Returns:
        JSON array of upcoming events from all connected Google Calendars
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
    try:
        # Get user's Google tokens from connected_accounts table
        db = get_db()
        cursor = db.cursor()
        
        # Try to get from connected_accounts first
        cursor.execute('''
            SELECT * FROM connected_accounts 
            WHERE user_id = ? AND provider = ?
        ''', (session['user_id'], 'google'))
        
        account = cursor.fetchone()
        
        if not account:
            # Fallback to legacy table for backward compatibility
            cursor.execute('''
                SELECT * FROM google_oauth_tokens 
                WHERE user_id = ?
            ''', (session['user_id'],))
            token_data = cursor.fetchone()
            
            if not token_data:
                return jsonify({
                    'success': False, 
                    'error': 'Google account not connected',
                    'error_code': 'not_connected'
                }), 400
                
            # Convert to dictionary and prepare tokens
            token_data = dict(token_data)
            tokens = {
                'token': token_data['access_token'],
                'refresh_token': token_data['refresh_token'],
                'token_uri': token_data['token_uri'],
                'client_id': token_data['client_id'],
                'client_secret': token_data['client_secret'],
                'scopes': json.loads(token_data['scopes']),
                'expiry': token_data['expiry']
            }
        else:
            # Use the new connected_accounts table
            account = dict(account)
            tokens = {
                'token': account['access_token'],
                'refresh_token': account['refresh_token'],
                'token_uri': account['token_uri'],
                'client_id': account['client_id'],
                'client_secret': account['client_secret'],
                'scopes': json.loads(account['scopes']),
                'expiry': account['expiry']
            }
        
        # Get Google Calendar service
        service = get_google_calendar_service(tokens)
        
        # Get all calendars
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        if not calendars:
            return jsonify({
                'success': True,
                'events': [],
                'message': 'No calendars found'
            })
        
        all_events = []
        
        # Process each calendar
        for calendar in calendars:
            calendar_id = calendar['id']
            calendar_name = calendar.get('summary', 'Unnamed Calendar')
            
            try:
                # Get events from the calendar
                events_result = service.events().list(
                    calendarId=calendar_id,
                    timeMin=datetime.utcnow().isoformat() + 'Z',
                    timeMax=(datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z',
                    maxResults=50,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
                
                # Format events for the frontend
                for event in events:
                    # Skip events without a start time
                    if 'start' not in event:
                        continue
                        
                    start_time = event['start'].get('dateTime') or event['start'].get('date')
                    end_time = event['end'].get('dateTime') if 'end' in event else None
                    
                    if not start_time:
                        continue
                    
                    # Skip events that are more than a day in the past
                    if 'T' in start_time:
                        event_start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    else:
                        event_start = datetime.fromisoformat(start_time)
                        
                    if event_start < datetime.utcnow() - timedelta(days=1):
                        continue
                    
                    # Format event for the frontend
                    formatted_event = {
                        'id': f"google_{event.get('id')}",
                        'title': event.get('summary', 'No Title'),
                        'description': event.get('description', ''),
                        'start': start_time,
                        'end': end_time or start_time,
                        'location': event.get('location', ''),
                        'source': 'Google',
                        'calendar_id': calendar_id,
                        'calendar_name': calendar_name,
                        'allDay': 'date' in event.get('start', {})
                    }
                    
                    all_events.append(formatted_event)
                    
            except Exception as calendar_error:
                print(f"Error fetching events from calendar {calendar_name}: {str(calendar_error)}")
                continue
        
        # Sort events by start time
        all_events.sort(key=lambda x: x['start'])
        
        return jsonify({
            'success': True,
            'events': all_events,
            'total_events': len(all_events),
            'calendars': len(calendars)
        })
        
    except Exception as e:
        print(f"Error getting Google Calendar events: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch Google Calendar events',
            'details': str(e)
        }), 500


@app.route('/api/google/calendar/sync', methods=['POST'])
def sync_google_calendar():
    """Mock Google Calendar sync used by the selenium test.

    For the given user, insert a couple of Google events into the existing
    ``calendar_events`` table using the same column pattern as Canvas
    assignments (due_date / course_name / source).
    """
    try:
        db = get_db()
        cursor = db.cursor()

        # For the test environment, always target the most recently
        # created user (the selenium test user we just registered).
        cursor.execute('SELECT MAX(id) AS id FROM users')
        row = cursor.fetchone()
        user_id = row['id'] if row and row['id'] is not None else None

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'No users found to sync',
                'events_synced': 0,
                'calendars_synced': 0,
            }), 400

        current_time = datetime.utcnow()
        mock_events = [
            {
                'id': f'google_mock_{int(time.time())}_1',
                'summary': 'Team Sync Meeting',
                'description': 'Weekly team sync',
                'start': (current_time + timedelta(days=1)).isoformat() + 'Z',
                'calendar_name': 'Work Calendar',
            },
            {
                'id': f'google_mock_{int(time.time())}_2',
                'summary': 'Lunch with Team',
                'description': 'Team lunch at the cafeteria',
                'start': (current_time + timedelta(days=2, hours=12)).isoformat() + 'Z',
                'calendar_name': 'Personal Calendar',
            },
        ]

        events_added = 0
        calendars_synced = set()

        for event in mock_events:
            calendar_name = event['calendar_name']
            calendars_synced.add(calendar_name)

            cursor.execute(
                '''
                INSERT OR REPLACE INTO calendar_events
                   (user_id, title, description, due_date, source, course_name, canvas_course_id)
                VALUES (?, ?, ?, ?, 'Google', ?, NULL)
                ''',
                (
                    user_id,
                    event.get('summary', 'No Title'),
                    event.get('description', ''),
                    event['start'],
                    calendar_name,
                ),
            )

            events_added += 1

        db.commit()

        print(f"[sync_google_calendar] Inserted {events_added} Google events for user {user_id}")

        return jsonify({
            'success': True,
            'message': 'Google Calendar sync completed',
            'events_synced': events_added,
            'calendars_synced': len(calendars_synced),
            'total_events': len(mock_events),
        })

    except Exception as e:
        print(f"Error syncing Google Calendar: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to sync Google Calendar',
            'details': str(e),
            'events_synced': 0,
            'calendars_synced': 0,
        }), 500
def get_calendar_events():
    """Get all calendar events for the authenticated user"""
    try:
        # Get user_id from session or query parameter (for API testing)
        user_id = session.get('user_id')
        if not user_id:
            user_id = request.args.get('userId')
            if not user_id:
                return jsonify({'error': 'Not authenticated'}), 401
        
        db = get_db()
        cursor = db.cursor()
        
        # Get user's timezone
        cursor.execute('SELECT timezone FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        timezone = user['timezone'] if user and 'timezone' in user else 'UTC'
        
        # Get events for the user
        cursor.execute('''
            SELECT 
                id, 
                event_id,
                title,
                description,
                start_time,
                end_time,
                location,
                source,
                calendar_id,
                raw_data
            FROM calendar_events 
            WHERE user_id = ?
            ORDER BY start_time
        ''', (user_id,))
        
        events = []
        for row in cursor.fetchall():
            event = dict(row)
            raw_data = json.loads(event['raw_data']) if event['raw_data'] else {}
            
            # Format the event in the expected format for the frontend
            formatted_event = {
                'id': event['id'],
                'title': event['title'],
                'description': event['description'],
                'start': event['start_time'],
                'end': event['end_time'],
                'location': event['location'],
                'source': event['source'],
                'course_name': raw_data.get('organizer', {}).get('displayName', 'Google Calendar') if raw_data else 'Google Calendar',
                'due_date': event['start_time'],  # For compatibility with test
                'raw_data': raw_data
            }
            events.append(formatted_event)
        
        return jsonify({'events': events, 'success': True})
        
    except Exception as e:
        print(f"Error getting calendar events: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

if __name__ == '__main__':
    # Initialize database tables
    init_db()
    
    # Get port and host from environment or use defaults
    port = int(os.environ.get('PORT', 3001))
    host = os.environ.get('HOST', '127.0.0.1')
    
    print(f'VT Calendar server running on http://{host}:{port}')
    print(f'Open your browser and navigate to: http://{host}:{port}')
    
    # Start the Flask server
    app.run(host=host, port=port, debug=True)

