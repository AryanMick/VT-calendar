from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
import sqlite3
import hashlib
import secrets
import os
import requests
from datetime import datetime
import hmac

# Setup Flask app
# Resolve absolute path to the frontend public directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'frontend', 'public'))
app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='')
app.secret_key = os.environ.get('SESSION_SECRET', 'vt-calendar-secret-key-change-in-production')
CORS(app, supports_credentials=True, origins=['http://127.0.0.1:3001', 'http://localhost:3001'])

# Database file
DATABASE = 'calendar.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables if they don't exist"""
    db = get_db()
    cursor = db.cursor()
    
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
    user_id = int(request.args.get('userId') or session.get('userId') or 0)
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'SELECT * FROM calendar_events WHERE user_id = ? ORDER BY due_date ASC',
        (user_id,)
    )
    # Convert rows to dictionaries
    events = [dict(row) for row in cursor.fetchall()]
    db.close()
    
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

