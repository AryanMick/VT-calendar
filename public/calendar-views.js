// Calendar Views JavaScript
function setupCalendarView() {
    const viewBtns = document.querySelectorAll('.view-btn');
    const prevWeek = document.getElementById('prevWeek');
    const nextWeek = document.getElementById('nextWeek');
    const prevMonth = document.getElementById('prevMonth');
    const nextMonth = document.getElementById('nextMonth');

    // View switcher
    viewBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            
            // Update button states
            viewBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show selected view
            const views = document.querySelectorAll('.events-view');
            views.forEach(v => v.classList.remove('active'));
            document.getElementById(view + 'View').classList.add('active');
            
            // Load view data
            if (view === 'day') renderDayView();
            else if (view === 'week') renderWeekView();
            else if (view === 'month') renderMonthView();
        });
    });

    // Week navigation
    prevWeek?.addEventListener('click', () => {
        currentDate.setDate(currentDate.getDate() - 7);
        renderWeekView();
    });

    nextWeek?.addEventListener('click', () => {
        currentDate.setDate(currentDate.getDate() + 7);
        renderWeekView();
    });

    // Month navigation
    prevMonth?.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderMonthView();
    });

    nextMonth?.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderMonthView();
    });
}

// Render day view
function renderDayView() {
    const dayDate = document.getElementById('dayDate');
    const dayEvents = document.getElementById('dayEvents');
    
    const date = new Date(currentDate);
    const dateStr = date.toLocaleDateString('en-US', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    });
    
    dayDate.textContent = dateStr;
    
    // Filter events for this day
    const dayStart = new Date(date);
    dayStart.setHours(0, 0, 0, 0);
    const dayEnd = new Date(date);
    dayEnd.setHours(23, 59, 59, 999);
    
    const dayEventsList = allEvents.filter(event => {
        const eventDate = new Date(event.due_date);
        return eventDate >= dayStart && eventDate <= dayEnd;
    });
    
    dayEvents.innerHTML = dayEventsList.map(event => `
        <div class="calendar-event">
            <div class="calendar-event-time">${formatTime(event.due_date)}</div>
            <div class="calendar-event-title">${escapeHtml(event.title)}</div>
            <div class="calendar-event-description">${escapeHtml(event.description || 'No description')}</div>
            <div class="event-source ${event.source.toLowerCase()}">${event.source}</div>
        </div>
    `).join('');
}

// Render week view
function renderWeekView() {
    const weekRange = document.getElementById('weekRange');
    const weekDays = document.getElementById('weekDays');
    
    const startOfWeek = getStartOfWeek(currentDate);
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(endOfWeek.getDate() + 6);
    
    weekRange.textContent = `${startOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${endOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
    
    weekDays.innerHTML = '';
    
    for (let i = 0; i < 7; i++) {
        const day = new Date(startOfWeek);
        day.setDate(day.getDate() + i);
        const dayName = day.toLocaleDateString('en-US', { weekday: 'short' });
        const dayNum = day.getDate();
        
        const dayEvents = allEvents.filter(event => {
            const eventDate = new Date(event.due_date);
            return eventDate.toDateString() === day.toDateString();
        });
        
        const dayDiv = document.createElement('div');
        dayDiv.className = 'week-day' + (new Date().toDateString() === day.toDateString() ? ' today' : '');
        dayDiv.innerHTML = `
            <div class="week-day-header">
                <div class="week-day-name">${dayName}</div>
                <div class="week-day-number">${dayNum}</div>
            </div>
            <div class="week-day-events">
                ${dayEvents.slice(0, 3).map(event => `
                    <div class="week-event">
                        ${escapeHtml(event.title)}
                    </div>
                `).join('')}
                ${dayEvents.length > 3 ? `<div class="week-event">+${dayEvents.length - 3} more</div>` : ''}
            </div>
        `;
        weekDays.appendChild(dayDiv);
    }
}

// Render month view
function renderMonthView() {
    const monthTitle = document.getElementById('monthTitle');
    const monthCalendar = document.getElementById('monthCalendar');
    
    monthTitle.textContent = currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startOfWeek = getStartOfWeek(firstDay);
    
    monthCalendar.innerHTML = '';
    
    // Day headers
    ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].forEach(day => {
        const header = document.createElement('div');
        header.className = 'month-day-header';
        header.textContent = day;
        monthCalendar.appendChild(header);
    });
    
    // Calendar days
    for (let i = 0; i < 42; i++) {
        const date = new Date(startOfWeek);
        date.setDate(startOfWeek.getDate() + i);
        
        const isToday = date.toDateString() === new Date().toDateString();
        const isCurrentMonth = date.getMonth() === month;
        
        const dayEvents = allEvents.filter(event => {
            const eventDate = new Date(event.due_date);
            return eventDate.toDateString() === date.toDateString();
        });
        
        const dayDiv = document.createElement('div');
        dayDiv.className = 'month-day' + (isToday ? ' today' : '') + (!isCurrentMonth ? ' other-month' : '');
        dayDiv.innerHTML = `
            <div class="month-day-number">${date.getDate()}</div>
            <div class="month-day-events">
                ${dayEvents.slice(0, 2).map(event => `
                    <div class="month-event ${event.source.toLowerCase()}">
                        ${escapeHtml(event.title.substring(0, 20))}
                    </div>
                `).join('')}
            </div>
        `;
        monthCalendar.appendChild(dayDiv);
    }
}

// Utility functions
function getStartOfWeek(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day;
    return new Date(d.setDate(diff));
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Update all events global when loading
function setAllEvents(events) {
    allEvents = events;
}


