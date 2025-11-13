// VT Calendar Application JavaScript
const API_URL = 'http://127.0.0.1:3001/api';

let currentUserId = null;
let authTokens = {
    canvas: null,
    google: null,
    microsoft: null
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkAuthState();
    setupEventListeners();
});

// Check if user is logged in
function checkAuthState() {
    const storedUserId = localStorage.getItem('userId');
    if (storedUserId) {
        currentUserId = storedUserId;
        showDashboard();
        loadCalendarEvents();
    }
}

// Setup event listeners
function setupEventListeners() {
    const loginForm = document.getElementById('loginForm');
    const manualEventForm = document.getElementById('manualEventForm');
    const syncBtn = document.getElementById('syncBtn');
    const connectGoogleBtn = document.getElementById('connectGoogleBtn');
    const connectMicrosoftBtn = document.getElementById('connectMicrosoftBtn');

    loginForm?.addEventListener('submit', handleLogin);
    manualEventForm?.addEventListener('submit', handleManualEventAdd);
    syncBtn?.addEventListener('click', handleSync);
    connectGoogleBtn?.addEventListener('click', handleConnectGoogle);
    connectMicrosoftBtn?.addEventListener('click', handleConnectMicrosoft);
}

// Handle login
async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('canvasEmail').value;
    const password = document.getElementById('canvasPassword').value;

    showNotification('Connecting to Canvas...', 'info');

    try {
        // Simulate Canvas authentication
        // In production, this would use Canvas API OAuth2
        const response = await fetch(`${API_URL}/users`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                canvasUserId: email.split('@')[0]
            })
        });

        const data = await response.json();
        
        if (data.success) {
            currentUserId = data.userId;
            localStorage.setItem('userId', currentUserId);
            authTokens.canvas = 'canvas_token_' + Date.now();
            
            showNotification('Successfully logged in!', 'success');
            showDashboard();
            loadCalendarEvents();
            
            // Enable additional account buttons
            document.getElementById('connectGoogleBtn').disabled = false;
            document.getElementById('connectMicrosoftBtn').disabled = false;
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Login failed. Please try again.', 'error');
    }
}

// Show dashboard
function showDashboard() {
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('dashboardSection').style.display = 'block';
    
    // Update account status
    updateAccountStatus();
}

// Update account status indicators
function updateAccountStatus() {
    const googleStatus = document.getElementById('googleStatus');
    const msStatus = document.getElementById('msStatus');
    
    if (authTokens.google) {
        googleStatus.innerHTML = '<span class="status-icon">✓</span><span>Google Connected</span>';
        googleStatus.querySelector('.status-icon').style.color = 'var(--vt-success)';
    }
    
    if (authTokens.microsoft) {
        msStatus.innerHTML = '<span class="status-icon">✓</span><span>Microsoft Connected</span>';
        msStatus.querySelector('.status-icon').style.color = 'var(--vt-success)';
    }
}

// Load calendar events
async function loadCalendarEvents() {
    if (!currentUserId) return;

    try {
        const response = await fetch(`${API_URL}/calendar/events?userId=${currentUserId}`);
        const data = await response.json();
        
        displayEvents(data.events);
    } catch (error) {
        console.error('Error loading events:', error);
    }
}

// Display events
function displayEvents(events) {
    const eventsList = document.getElementById('eventsList');
    
    if (!events || events.length === 0) {
        eventsList.innerHTML = '<div class="event-item empty">No events found. Sync your calendars or add manual events.</div>';
        return;
    }

    eventsList.innerHTML = events.map(event => `
        <div class="event-item">
            <div class="event-header">
                <div class="event-title">${escapeHtml(event.title)}</div>
                <div class="event-date">${formatDate(event.due_date)}</div>
            </div>
            <div class="event-description">${escapeHtml(event.description || 'No description')}</div>
            <div class="event-source ${event.source.toLowerCase()}">${event.source}</div>
        </div>
    `).join('');
}

// Handle manual event addition
async function handleManualEventAdd(e) {
    e.preventDefault();
    
    const title = document.getElementById('eventTitle').value;
    const description = document.getElementById('eventDescription').value;
    const dueDate = document.getElementById('eventDate').value;

    try {
        const response = await fetch(`${API_URL}/calendar/events`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                userId: currentUserId,
                title: title,
                description: description,
                dueDate: dueDate
            })
        });

        const data = await response.json();
        
        if (data.success) {
            showNotification('Event added successfully!', 'success');
            document.getElementById('manualEventForm').reset();
            loadCalendarEvents();
        }
    } catch (error) {
        console.error('Error adding event:', error);
        showNotification('Failed to add event.', 'error');
    }
}

// Handle sync
async function handleSync() {
    showNotification('Syncing calendars...', 'info');
    
    try {
        // Simulate sync from Canvas
        if (authTokens.canvas) {
            const response = await fetch(`${API_URL}/canvas/assignments?userId=${currentUserId}`, {
                headers: {
                    'Authorization': `Bearer ${authTokens.canvas}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                showNotification(`Synced ${data.count} assignments from Canvas!`, 'success');
            }
        }
        
        // Simulate sync from Google
        if (authTokens.google) {
            const response = await fetch(`${API_URL}/google/calendar?userId=${currentUserId}`, {
                headers: {
                    'Authorization': `Bearer ${authTokens.google}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                showNotification(`Synced ${data.count} events from Google Calendar!`, 'success');
            }
        }
        
        loadCalendarEvents();
    } catch (error) {
        console.error('Sync error:', error);
        showNotification('Sync failed. Please try again.', 'error');
    }
}

// Handle Google Calendar connection
function handleConnectGoogle() {
    showNotification('Connecting to Google Calendar...', 'info');
    
    // Simulate OAuth flow
    setTimeout(() => {
        authTokens.google = 'google_token_' + Date.now();
        localStorage.setItem('googleToken', authTokens.google);
        showNotification('Google Calendar connected!', 'success');
        updateAccountStatus();
    }, 1000);
}

// Handle Microsoft account connection
function handleConnectMicrosoft() {
    showNotification('Connecting to Microsoft account...', 'info');
    
    // Simulate OAuth flow
    setTimeout(() => {
        authTokens.microsoft = 'microsoft_token_' + Date.now();
        localStorage.setItem('microsoftToken', authTokens.microsoft);
        showNotification('Microsoft account connected!', 'success');
        updateAccountStatus();
    }, 1000);
}

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    // Remove existing notification
    const existing = document.querySelector('.notification');
    if (existing) {
        existing.remove();
    }

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add slideOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
        }
        to {
            transform: translateX(400px);
        }
    }
`;
document.head.appendChild(style);

