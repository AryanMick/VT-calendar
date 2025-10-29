// Chrome Extension Popup Script
document.addEventListener('DOMContentLoaded', async () => {
    const eventsContainer = document.getElementById('eventsContainer');
    const openFullBtn = document.getElementById('openFullCalendarBtn');
    
    openFullBtn.addEventListener('click', () => {
        chrome.tabs.create({ url: 'http://localhost:3000' });
    });
    
    // Load events from localStorage or API
    try {
        const userId = localStorage.getItem('userId') || await getFromStorage('userId');
        if (!userId) {
            eventsContainer.innerHTML = '<div class="empty">Please log in to view events</div>';
            return;
        }
        
        const response = await fetch('http://localhost:3000/api/calendar/events?userId=' + userId);
        const data = await response.json();
        
        if (data.events && data.events.length > 0) {
            eventsContainer.innerHTML = data.events.slice(0, 5).map(event => `
                <div class="event-item">
                    <div class="event-title">${escapeHtml(event.title)}</div>
                    <div class="event-date">${formatDate(event.due_date)}</div>
                    <div class="event-source ${event.source.toLowerCase()}">${event.source}</div>
                </div>
            `).join('');
        } else {
            eventsContainer.innerHTML = '<div class="empty">No upcoming events</div>';
        }
    } catch (error) {
        eventsContainer.innerHTML = '<div class="empty">Unable to load events</div>';
    }
});

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
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

function getFromStorage(key) {
    return new Promise(resolve => {
        chrome.storage.local.get([key], result => resolve(result[key]));
    });
}


