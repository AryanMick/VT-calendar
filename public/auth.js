// VT Calendar Authentication JavaScript
const API_URL = 'http://localhost:3000/api';

let currentUserId = null;
let requires2FA = false;
let authTokens = {
    canvas: null,
    google: null,
    microsoft: null
};

// Initialize app
let currentDate = new Date();
let allEvents = [];

document.addEventListener('DOMContentLoaded', () => {
    checkAuthState();
    setupEventListeners();
    setupTabSwitching();
    setupCalendarView();
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
    const loginForm = document.getElementById('loginFormContent');
    const registerForm = document.getElementById('registerFormContent');
    const twoFactorForm = document.getElementById('2faFormContent');
    const linkCanvasForm = document.getElementById('linkCanvasForm');
    const manualEventForm = document.getElementById('manualEventForm');
    const skipCanvasBtn = document.getElementById('skipCanvasBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const linkCanvasBtn = document.getElementById('linkCanvasBtn');
    const syncBtn = document.getElementById('syncBtn');
    const logoutHeaderBtn = document.getElementById('logoutHeaderBtn');

    loginForm?.addEventListener('submit', handleLogin);
    registerForm?.addEventListener('submit', handleRegister);
    twoFactorForm?.addEventListener('submit', handle2FAVerify);
    linkCanvasForm?.addEventListener('submit', handleLinkCanvas);
    manualEventForm?.addEventListener('submit', handleManualEventAdd);
    skipCanvasBtn?.addEventListener('click', () => showDashboard());
    logoutBtn?.addEventListener('click', handleLogout);
    linkCanvasBtn?.addEventListener('click', () => showLinkSection());
    syncBtn?.addEventListener('click', handleSync);
    logoutHeaderBtn?.addEventListener('click', handleLogout);
    
    document.getElementById('settingsBtn')?.addEventListener('click', () => {
        window.location.href = '/settings.html';
    });
    
    // Profile menu items
    document.getElementById('profileMenuSettings')?.addEventListener('click', () => {
        window.location.href = '/settings.html';
    });
    
    document.getElementById('profileMenuPrivacy')?.addEventListener('click', () => {
        window.location.href = '/privacy-policy.html';
    });
    
    document.getElementById('profileMenuTerms')?.addEventListener('click', () => {
        window.location.href = '/terms-of-service.html';
    });
    
    document.getElementById('profileMenuHelp')?.addEventListener('click', () => {
        alert('Help & Support:\n\nEmail: ethanl03@vt.edu\nVisit the Settings page for more options.');
    });
    
    document.getElementById('profileMenuLogout')?.addEventListener('click', () => {
        handleLogout();
    });

    // Toggle profile menu on click
    const profileBtn = document.getElementById('profileMenuBtn');
    const profileMenu = document.getElementById('profileMenu');
    profileBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        profileMenu.classList.toggle('show');
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
        if (!profileMenu?.contains(e.target) && e.target !== profileBtn) {
            profileMenu?.classList.remove('show');
        }
    });

    // Floating profile menu wiring
    const fBtn = document.getElementById('floatingProfileBtn');
    const fMenu = document.getElementById('floatingProfileMenu');
    fBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        fMenu.classList.toggle('show');
    });
    document.addEventListener('click', (e) => {
        if (!fMenu?.contains(e.target) && e.target !== fBtn) {
            fMenu?.classList.remove('show');
        }
    });
    document.getElementById('floatingMenuSettings')?.addEventListener('click', () => {
        window.location.href = '/settings.html';
    });
    document.getElementById('floatingMenuPrivacy')?.addEventListener('click', () => {
        window.location.href = '/privacy-policy.html';
    });
    document.getElementById('floatingMenuTerms')?.addEventListener('click', () => {
        window.location.href = '/terms-of-service.html';
    });
    document.getElementById('floatingMenuLogout')?.addEventListener('click', () => {
        handleLogout();
    });

    // Top-left logout button
    document.getElementById('logoutTopBtn')?.addEventListener('click', handleLogout);
    document.getElementById('logoutFloatingBtn')?.addEventListener('click', handleLogout);
}

// Setup tab switching
function setupTabSwitching() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const authForms = document.querySelectorAll('.auth-form');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            
            // Update active tab
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show correct form
            if (tabName === 'login') {
                document.getElementById('loginForm').style.display = 'block';
                document.getElementById('registerForm').style.display = 'none';
            } else {
                document.getElementById('loginForm').style.display = 'none';
                document.getElementById('registerForm').style.display = 'block';
            }
        });
    });
}

// Handle registration
async function handleRegister(e) {
    e.preventDefault();
    
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const canvasId = document.getElementById('registerCanvasId').value;

    if (!email.endsWith('@vt.edu')) {
        showNotification('Must use a Virginia Tech email (@vt.edu)', 'error');
        return;
    }

    showNotification('Creating account...', 'info');

    try {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                password,
                canvasUserId: canvasId
            })
        });

        const data = await response.json();
        
        if (data.success) {
            showNotification('Account created successfully!', 'success');
            // Switch to login
            document.querySelector('.tab-btn[data-tab="login"]').click();
            document.getElementById('loginEmail').value = email;
        } else {
            showNotification(data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showNotification('Registration failed. Please try again.', 'error');
    }
}

// Handle login
async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    if (!email.endsWith('@vt.edu')) {
        showNotification('Must use a Virginia Tech email (@vt.edu)', 'error');
        return;
    }

    showNotification('Logging in...', 'info');

    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                password
            })
        });

        const data = await response.json();
        
        if (data.success) {
            if (data.requires2FA) {
                // Show 2FA form
                requires2FA = true;
                currentUserId = data.userId;
                show2FAForm();
                showNotification('Enter your 2FA code', 'info');
            } else {
                // Direct login
                currentUserId = data.userId;
                localStorage.setItem('userId', currentUserId);
                showNotification('Successfully logged in!', 'success');
                showDashboard();
            }
        } else {
            showNotification(data.error || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Login failed. Please try again.', 'error');
    }
}

// Handle 2FA verification
async function handle2FAVerify(e) {
    e.preventDefault();
    
    const code = document.getElementById('2faCode').value;

    try {
        const response = await fetch(`${API_URL}/auth/verify-2fa`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                userId: currentUserId,
                code
            })
        });

        const data = await response.json();
        
        if (data.success) {
            localStorage.setItem('userId', currentUserId);
            showNotification('2FA verified successfully!', 'success');
            showDashboard();
        } else {
            showNotification(data.error || 'Invalid 2FA code', 'error');
        }
    } catch (error) {
        console.error('2FA error:', error);
        showNotification('Verification failed. Please try again.', 'error');
    }
}

// Handle Canvas linking
async function handleLinkCanvas(e) {
    e.preventDefault();
    
    const canvasToken = document.getElementById('canvasToken').value;

    showNotification('Linking Canvas account...', 'info');

    try {
        const response = await fetch(`${API_URL}/canvas/link`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                userId: currentUserId,
                canvasToken
            })
        });

        const data = await response.json();
        
        if (data.success) {
            authTokens.canvas = canvasToken;
            localStorage.setItem('canvasToken', canvasToken);
            showNotification(`Linked ${data.coursesLinked} Canvas courses!`, 'success');
            updateAccountStatus();
            showDashboard();
            // Wait a bit for events to be stored, then load
            setTimeout(() => loadCalendarEvents(), 500);
        } else {
            showNotification(data.error || 'Failed to link Canvas', 'error');
        }
    } catch (error) {
        console.error('Canvas link error:', error);
        showNotification('Failed to link Canvas. Please check your token.', 'error');
    }
}

// Show 2FA form
function show2FAForm() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('2faForm').style.display = 'block';
}

// Show link section
function showLinkSection() {
    document.getElementById('dashboardSection').style.display = 'none';
    document.getElementById('linkSection').style.display = 'block';
}

// Show dashboard
function showDashboard() {
    document.getElementById('authSection').style.display = 'none';
    document.getElementById('linkSection').style.display = 'none';
    document.getElementById('dashboardSection').style.display = 'block';
    
    updateAccountStatus();
    
    // Update profile menu with user info
    const email = localStorage.getItem('userEmail') || 'user@vt.edu';
    document.getElementById('profileUserName').textContent = email.split('@')[0];
    document.getElementById('profileUserEmail').textContent = email;
    const fName = document.getElementById('floatingProfileUserName');
    const fEmail = document.getElementById('floatingProfileUserEmail');
    if (fName && fEmail) {
        fName.textContent = email.split('@')[0];
        fEmail.textContent = email;
    }
}

// Update account status indicators
function updateAccountStatus() {
    const canvasStatus = document.getElementById('canvasStatus');
    const googleStatus = document.getElementById('googleStatus');
    const msStatus = document.getElementById('msStatus');
    
    // Load tokens from localStorage
    authTokens.canvas = localStorage.getItem('canvasToken');
    
    if (authTokens.canvas) {
        canvasStatus.innerHTML = '<span class="status-icon" style="color: var(--vt-success);">✓</span><span>Canvas Connected</span>';
    } else {
        canvasStatus.innerHTML = '<span class="status-icon">✗</span><span>Canvas Not Connected</span>';
    }
    
    if (authTokens.google) {
        googleStatus.innerHTML = '<span class="status-icon" style="color: var(--vt-success);">✓</span><span>Google Connected</span>';
    }
    
    if (authTokens.microsoft) {
        msStatus.innerHTML = '<span class="status-icon" style="color: var(--vt-success);">✓</span><span>Microsoft Connected</span>';
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
    if (!events || events.length === 0) {
        document.getElementById('eventsList').innerHTML = '<div class="event-item empty">No events found. Link your Canvas account to get started!</div>';
        document.getElementById('dayEvents').innerHTML = '<div class="event-item empty">No events today</div>';
        return;
    }

    // Store events globally for calendar views
    if (typeof setAllEvents === 'function') {
        setAllEvents(events);
    }

    // List view
    const eventsList = document.getElementById('eventsList');
    eventsList.innerHTML = events.map(event => `
        <div class="event-item">
            <div class="event-header">
                <div class="event-title">${escapeHtml(event.title)}</div>
                <div class="event-date">${formatDate(event.due_date)}</div>
            </div>
            <div class="event-description">${escapeHtml(event.description || 'No description')}</div>
            ${event.course_name ? `<div class="event-course">${escapeHtml(event.course_name)}</div>` : ''}
            <div class="event-source ${event.source.toLowerCase()}">${event.source}</div>
        </div>
    `).join('');
    
    // Update calendar views if they exist
    if (document.getElementById('dayView').classList.contains('active')) {
        renderDayView();
    } else if (document.getElementById('weekView').classList.contains('active')) {
        renderWeekView();
    } else if (document.getElementById('monthView').classList.contains('active')) {
        renderMonthView();
    }
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
        
        loadCalendarEvents();
    } catch (error) {
        console.error('Sync error:', error);
        showNotification('Sync failed. Please try again.', 'error');
    }
}

// Handle logout
function handleLogout() {
    localStorage.removeItem('userId');
    localStorage.removeItem('canvasToken');
    currentUserId = null;
    authTokens = { canvas: null, google: null, microsoft: null };
    
    showNotification('Logged out successfully', 'info');
    
    // Reset to login page
    location.reload();
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

// Add CSS for tabs
const tabStyle = document.createElement('style');
tabStyle.textContent = `
    .auth-tabs {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
    }
    
    .tab-btn {
        flex: 1;
        padding: 12px;
        background: var(--vt-light);
        border: 2px solid var(--vt-border);
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .tab-btn.active {
        background: var(--vt-maroon);
        color: white;
        border-color: var(--vt-maroon);
    }
    
    .auth-form h2 {
        color: var(--vt-maroon);
        margin-bottom: 10px;
    }
    
    .help-text {
        text-align: center;
        color: #999;
        font-size: 0.9rem;
        margin-top: 10px;
    }
    
    .canvas-instructions {
        background: var(--vt-light);
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    
    .canvas-instructions h3 {
        color: var(--vt-maroon);
        margin-bottom: 15px;
    }
    
    .canvas-instructions ol {
        padding-left: 20px;
    }
    
    .canvas-instructions li {
        margin-bottom: 10px;
        line-height: 1.6;
    }
    
    .canvas-instructions a {
        color: var(--vt-maroon);
        text-decoration: none;
    }
    
    .canvas-instructions a:hover {
        text-decoration: underline;
    }
    
    .event-course {
        font-size: 0.9rem;
        color: var(--vt-orange);
        font-weight: 600;
        margin-top: 8px;
    }
`;
document.head.appendChild(tabStyle);

