// VT Calendar Settings JavaScript
const API_URL = 'http://127.0.0.1:3001/api';

let currentUserId = null;
let userSettings = {};

// Initialize settings page
document.addEventListener('DOMContentLoaded', () => {
    currentUserId = localStorage.getItem('userId');
    
    if (!currentUserId) {
        // Not logged in, redirect to auth
        window.location.href = '/auth.html';
        return;
    }

    setupEventListeners();
    loadSettings();
    loadAccountStatus();
});

// Setup event listeners
function setupEventListeners() {
    // Navigation
    const navBtns = document.querySelectorAll('.nav-btn[data-section]');
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const section = btn.dataset.section;
            showSection(section);
            
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });

    document.getElementById('backToDashboard')?.addEventListener('click', () => {
        window.location.href = '/auth.html';
    });

    // Save buttons
    document.getElementById('saveNotifications')?.addEventListener('click', saveNotificationSettings);
    document.getElementById('savePrivacy')?.addEventListener('click', savePrivacySettings);
    
    // Account actions
    document.getElementById('exportData')?.addEventListener('click', exportData);
    document.getElementById('clearData')?.addEventListener('click', clearAllData);
    document.getElementById('deleteAccount')?.addEventListener('click', deleteAccount);
}

// Show section
function showSection(sectionName) {
    const sections = document.querySelectorAll('.settings-section');
    sections.forEach(section => {
        section.classList.remove('active');
    });
    
    const targetSection = document.getElementById(sectionName);
    if (targetSection) {
        targetSection.classList.add('active');
    }
}

// Load settings
async function loadSettings() {
    try {
        const response = await fetch(`${API_URL}/settings?userId=${currentUserId}`);
        const data = await response.json();
        
        if (data.settings) {
            userSettings = data.settings;
            applySettingsToUI();
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

// Apply settings to UI
function applySettingsToUI() {
    if (!userSettings) return;

    document.getElementById('emailNotifications').checked = userSettings.email_notifications === 1;
    document.getElementById('pushNotifications').checked = userSettings.push_notifications === 1;
    document.getElementById('reminderHours').value = userSettings.reminder_before_hours || 24;
    document.getElementById('reminderMinutes').value = userSettings.reminder_before_minutes || 60;
    document.getElementById('privacyMode').value = userSettings.privacy_mode || 'standard';
    document.getElementById('dataSharing').checked = userSettings.data_sharing === 1;
}

// Save notification settings
async function saveNotificationSettings() {
    const emailNotifications = document.getElementById('emailNotifications').checked;
    const pushNotifications = document.getElementById('pushNotifications').checked;
    const reminderHours = parseInt(document.getElementById('reminderHours').value);
    const reminderMinutes = parseInt(document.getElementById('reminderMinutes').value);

    try {
        const response = await fetch(`${API_URL}/settings`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                userId: currentUserId,
                email_notifications: emailNotifications,
                push_notifications: pushNotifications,
                reminder_before_hours: reminderHours,
                reminder_before_minutes: reminderMinutes,
                privacy_mode: userSettings.privacy_mode || 'standard',
                data_sharing: userSettings.data_sharing === 1
            })
        });

        const data = await response.json();
        
        if (data.success) {
            showNotification('Notification settings saved successfully!', 'success');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        showNotification('Failed to save settings.', 'error');
    }
}

// Save privacy settings
async function savePrivacySettings() {
    const privacyMode = document.getElementById('privacyMode').value;
    const dataSharing = document.getElementById('dataSharing').checked;

    try {
        const response = await fetch(`${API_URL}/settings`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                userId: currentUserId,
                email_notifications: userSettings.email_notifications === 1,
                push_notifications: userSettings.push_notifications === 1,
                reminder_before_hours: userSettings.reminder_before_hours || 24,
                reminder_before_minutes: userSettings.reminder_before_minutes || 60,
                privacy_mode: privacyMode,
                data_sharing: dataSharing
            })
        });

        const data = await response.json();
        
        if (data.success) {
            showNotification('Privacy settings saved successfully!', 'success');
            userSettings.privacy_mode = privacyMode;
            userSettings.data_sharing = dataSharing;
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        showNotification('Failed to save settings.', 'error');
    }
}

// Load account status
function loadAccountStatus() {
    const canvasToken = localStorage.getItem('canvasToken');
    const googleToken = localStorage.getItem('googleToken');
    const msToken = localStorage.getItem('microsoftToken');

    if (canvasToken) {
        document.getElementById('canvasAccountInfo').innerHTML = 
            '<span class="account-status" style="color: var(--vt-success);">✓ Canvas: Connected</span>' +
            '<button class="btn btn-small btn-danger" onclick="disconnectCanvas()">Disconnect</button>';
    }

    if (googleToken) {
        document.getElementById('googleAccountInfo').innerHTML = 
            '<span class="account-status" style="color: var(--vt-success);">✓ Google: Connected</span>' +
            '<button class="btn btn-small btn-danger">Disconnect</button>';
    }

    if (msToken) {
        document.getElementById('microsoftAccountInfo').innerHTML = 
            '<span class="account-status" style="color: var(--vt-success);">✓ Microsoft: Connected</span>' +
            '<button class="btn btn-small btn-danger">Disconnect</button>';
    }
}

// Disconnect Canvas
function disconnectCanvas() {
    if (confirm('Are you sure you want to disconnect your Canvas account?')) {
        localStorage.removeItem('canvasToken');
        showNotification('Canvas account disconnected.', 'info');
        loadAccountStatus();
    }
}

// Export data
async function exportData() {
    try {
        const response = await fetch(`${API_URL}/calendar/events?userId=${currentUserId}`);
        const data = await response.json();
        
        const exportData = {
            exported_at: new Date().toISOString(),
            events: data.events,
            settings: userSettings
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `vt-calendar-export-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        showNotification('Data exported successfully!', 'success');
    } catch (error) {
        console.error('Error exporting data:', error);
        showNotification('Failed to export data.', 'error');
    }
}

// Clear all data
async function clearAllData() {
    if (!confirm('Are you sure you want to clear all calendar data? This will remove all events but keep your account.')) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/calendar/events?userId=${currentUserId}`);
        const data = await response.json();
        
        if (data.events) {
            for (const event of data.events) {
                await fetch(`${API_URL}/calendar/events/${event.id}`, {
                    method: 'DELETE'
                });
            }
        }
        
        showNotification('All calendar data cleared.', 'info');
        setTimeout(() => window.location.reload(), 1000);
    } catch (error) {
        console.error('Error clearing data:', error);
        showNotification('Failed to clear data.', 'error');
    }
}

// Delete account
async function deleteAccount() {
    if (!confirm('Are you absolutely sure you want to delete your account? This action cannot be undone!')) {
        return;
    }

    if (!confirm('This will permanently delete all your data. Are you sure?')) {
        return;
    }

    try {
        // Clear all local data
        localStorage.clear();
        
        showNotification('Account deleted. Redirecting to login...', 'info');
        setTimeout(() => {
            window.location.href = '/auth.html';
        }, 2000);
    } catch (error) {
        console.error('Error deleting account:', error);
        showNotification('Failed to delete account.', 'error');
    }
}

// Notification utility
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

// Add styles for settings page
const settingsStyle = document.createElement('style');
settingsStyle.textContent = `
    .settings-container {
        max-width: 1000px;
        margin: 0 auto;
    }

    .settings-nav {
        display: flex;
        gap: 10px;
        margin-bottom: 30px;
        flex-wrap: wrap;
    }

    .nav-btn {
        padding: 12px 24px;
        background: var(--vt-light);
        border: 2px solid var(--vt-border);
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.3s;
    }

    .nav-btn:hover {
        border-color: var(--vt-maroon);
        background: white;
    }

    .nav-btn.active {
        background: var(--vt-maroon);
        color: white;
        border-color: var(--vt-maroon);
    }

    .settings-section {
        display: none;
        background: white;
        border-radius: 12px;
        padding: 40px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    }

    .settings-section.active {
        display: block;
    }

    .settings-section h2 {
        color: var(--vt-maroon);
        margin-bottom: 10px;
    }

    .section-description {
        color: #666;
        margin-bottom: 30px;
    }

    .settings-card {
        display: flex;
        flex-direction: column;
        gap: 25px;
    }

    .setting-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px;
        background: var(--vt-light);
        border-radius: 8px;
    }

    .setting-info h3 {
        color: var(--vt-dark);
        margin-bottom: 5px;
        font-size: 1.1rem;
    }

    .setting-info p {
        color: #666;
        font-size: 0.9rem;
    }

    .toggle-switch {
        position: relative;
        display: inline-block;
        width: 60px;
        height: 34px;
    }

    .toggle-switch input {
        opacity: 0;
        width: 0;
        height: 0;
    }

    .toggle-slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        transition: .4s;
        border-radius: 34px;
    }

    .toggle-slider:before {
        position: absolute;
        content: "";
        height: 26px;
        width: 26px;
        left: 4px;
        bottom: 4px;
        background-color: white;
        transition: .4s;
        border-radius: 50%;
    }

    input:checked + .toggle-slider {
        background-color: var(--vt-success);
    }

    input:checked + .toggle-slider:before {
        transform: translateX(26px);
    }

    .reminder-controls select,
    .select-input {
        padding: 10px 15px;
        border: 2px solid var(--vt-border);
        border-radius: 6px;
        font-size: 1rem;
        background: white;
        min-width: 200px;
    }

    .info-section {
        background: var(--vt-light);
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
    }

    .info-section ul {
        margin-top: 10px;
        padding-left: 20px;
    }

    .info-section li {
        margin-bottom: 8px;
        color: #666;
    }

    .info-section.warning {
        background: #fff3e0;
        border-left: 4px solid var(--vt-warning);
    }

    .info-section.warning h4 {
        color: var(--vt-warning);
    }

    .connected-account {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px;
        background: var(--vt-light);
        border-radius: 8px;
        margin-bottom: 10px;
    }

    .account-info,
    .account-actions {
        margin-top: 20px;
    }

    .account-actions {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .btn-small {
        padding: 8px 16px;
        font-size: 0.9rem;
    }

    .btn-danger {
        background: var(--vt-danger);
        color: white;
    }

    .btn-danger:hover {
        background: #d32f2f;
    }
`;
document.head.appendChild(settingsStyle);


