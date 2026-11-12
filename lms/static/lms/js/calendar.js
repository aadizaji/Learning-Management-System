/* Calendar powered by saved ClassSession rows, not guessed weekly repetitions.
   English Gregorian and Persian Jalali display share the same saved Gregorian sessions. */
(() => {
    'use strict';
    const dataNode = document.getElementById('academic-calendar-data');
    const grid = document.getElementById('calendar-grid');
    if (!dataNode || !grid) return;

    const sessions = JSON.parse(dataNode.textContent);
    const canMark = grid.dataset.canMark === 'true';
    const attendanceBase = grid.dataset.attendanceUrl;
    const isPersian = document.documentElement.lang.toLowerCase().startsWith('fa');
    const locale = isPersian ? 'fa-IR-u-ca-persian' : 'en-US';
    const monthFormatter = new Intl.DateTimeFormat(locale, {month: 'long', year: 'numeric'});
    const dayFormatter = new Intl.DateTimeFormat(locale, {weekday: 'long', month: 'long', day: 'numeric', year: 'numeric'});
    const shortMonthFormatter = new Intl.DateTimeFormat(locale, {month: 'short'});
    const dayNumberFormatter = new Intl.DateTimeFormat(locale, {day: 'numeric'});
    const persianPartsFormatter = new Intl.DateTimeFormat('en-US-u-ca-persian', {year: 'numeric', month: 'numeric', day: 'numeric'});
    const messages = isPersian ? {
        noClasses: 'کلاسی برای این روز ثبت نشده', anotherDay: 'روز دیگری را انتخاب کنید یا فیلترها را تغییر دهید.',
        noUpcoming: 'کلاس آینده‌ای وجود ندارد', tryDate: 'روز دیگری را انتخاب کنید.',
        reason: 'دلیل', attendance: 'حضور و غیاب', cancelled: 'لغوشده', more: 'مورد بیشتر', classes: 'کلاس'
    } : {
        noClasses: 'No classes scheduled', anotherDay: 'Select another day or change your filters.',
        noUpcoming: 'No upcoming classes', tryDate: 'Try another date or add sessions for your courses.',
        reason: 'Reason', attendance: 'Open attendance', cancelled: 'Cancelled', more: 'more', classes: 'class(es)'
    };
    const palette = ['#6258e8', '#009f95', '#d68b12', '#dd5367', '#348bd6'];
    const statusColors = {S: null, C: '#159b82', X: '#d94b61'};
    const els = {
        title: document.getElementById('calendar-month-title'),
        search: document.getElementById('calendar-search'),
        category: document.getElementById('calendar-category'),
        instructor: document.getElementById('calendar-instructor'),
        selectedDate: document.getElementById('selected-day-date'),
        selectedEvents: document.getElementById('selected-day-events'),
        upcoming: document.getElementById('calendar-upcoming'),
        stats: {
            courses: document.getElementById('stat-courses'),
            schedules: document.getElementById('stat-schedules'),
            instructors: document.getElementById('stat-instructors'),
            sessions: document.getElementById('stat-sessions'),
        },
    };

    function atNoon(d) { return new Date(d.getFullYear(), d.getMonth(), d.getDate(), 12); }
    function addDays(d, n) { const r = atNoon(d); r.setDate(r.getDate() + n); return r; }
    function persianParts(d) {
        const parts = Object.fromEntries(persianPartsFormatter.formatToParts(d)
            .filter(p => p.type === 'year' || p.type === 'month' || p.type === 'day')
            .map(p => [p.type, Number(p.value.replace(/[۰-۹]/g, c => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(c))))]));
        return parts;
    }
    function firstOfMonth(d) {
        if (!isPersian) return new Date(d.getFullYear(), d.getMonth(), 1, 12);
        const day = persianParts(d).day;
        return addDays(d, 1-day);
    }
    function nextMonth(d) {
        if (!isPersian) return new Date(d.getFullYear(), d.getMonth()+1, 1, 12);
        const first = firstOfMonth(d);
        const ym = persianParts(first);
        let cursor = addDays(first, 28);
        while (persianParts(cursor).month === ym.month && persianParts(cursor).year === ym.year) cursor = addDays(cursor,1);
        return cursor;
    }
    function previousMonth(d) {
        return isPersian ? firstOfMonth(addDays(firstOfMonth(d),-1)) : new Date(d.getFullYear(), d.getMonth()-1, 1, 12);
    }
    function iso(d) { return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; }
    function parseDate(value) { const [y, m, d] = value.split('-').map(Number); return new Date(y, m - 1, d, 12); }
    function weekOffset(d) { return isPersian ? (d.getDay() + 1) % 7 : (d.getDay() + 6) % 7; }
    function sessionColor(s) { return statusColors[s.status] || palette[Number(s.course_id) % palette.length]; }
    function element(tag, css = '', content) {
        const e = document.createElement(tag);
        if (css) e.className = css;
        if (content !== undefined) e.textContent = content;
        return e;
    }
    function emptyState(title, description) {
        const e = element('div', 'calendar-empty');
        e.append(element('i', 'bi bi-calendar2-x'), element('strong', '', title), element('span', '', description));
        return e;
    }
    function filteredSessions() {
        const search = els.search.value.trim().toLocaleLowerCase(locale);
        return sessions.filter(s =>
            (!els.category.value || String(s.category_id) === els.category.value) &&
            (!els.instructor.value || String(s.instructor_id) === els.instructor.value) &&
            (!search || `${s.course_title} ${s.instructor_name} ${s.category_name} ${s.classroom || ""}`.toLocaleLowerCase(locale).includes(search))
        );
    }
    function groupedByDate(filtered) {
        const map = new Map();
        for (const s of filtered) {
            if (!map.has(s.date)) map.set(s.date, []);
            map.get(s.date).push(s);
        }
        for (const day of map.values()) day.sort((a, b) => a.start_time.localeCompare(b.start_time) || a.course_title.localeCompare(b.course_title));
        return map;
    }
    function attendanceLink(s) {
        const url = new URL(attendanceBase, window.location.origin);
        url.searchParams.set('course', String(s.course_id));
        url.searchParams.set('session', String(s.id));
        return url.pathname + url.search;
    }

    if (isPersian) {
        const weekdays = document.querySelector('.calendar-weekdays');
        if (weekdays) weekdays.replaceChildren(...['شنبه','یکشنبه','دوشنبه','سه‌شنبه','چهارشنبه','پنجشنبه','جمعه'].map(day => element('span','',day)));
        const dateSystem = document.querySelector('.calendar-date-system');
        if (dateSystem) dateSystem.textContent = 'تقویم شمسی';
    }
    const today = atNoon(new Date());
    const chosenCourse = new URLSearchParams(window.location.search).get('course');
    const focusSet = chosenCourse ? sessions.filter(s => String(s.course_id) === chosenCourse) : sessions;
    const orderedDates = focusSet.map(s => s.date).sort();
    const firstUpcoming = orderedDates.find(d => d >= iso(today));
    const focus = chosenCourse ? (orderedDates[0] || iso(today)) : (firstUpcoming || orderedDates[orderedDates.length - 1] || iso(today));
    let selectedDate = parseDate(focus);
    let monthStart = firstOfMonth(selectedDate);

    function renderGrid(byDay) {
        const monthEnd = nextMonth(monthStart);
        els.title.textContent = monthFormatter.format(monthStart);
        const offset = weekOffset(monthStart);
        const daysInMonth = Math.round((monthEnd - monthStart) / 86400000);
        const count = Math.max(35, Math.ceil((offset + daysInMonth) / 7) * 7);
        const start = addDays(monthStart, -offset);
        const fragment = document.createDocumentFragment();
        for (let index = 0; index < count; index++) {
            const date = addDays(start, index);
            const key = iso(date);
            const visibleMonth = date >= monthStart && date < monthEnd;
            const list = byDay.get(key) || [];
            const button = element('button', 'calendar-day' + (visibleMonth ? '' : ' outside'));
            button.type = 'button';
            button.setAttribute('role', 'gridcell');
            button.setAttribute('aria-label', `${dayFormatter.format(date)}, ${list.length} ${messages.classes}`);
            if (key === iso(selectedDate)) { button.classList.add('selected'); button.setAttribute('aria-selected', 'true'); }
            if (key === iso(today)) button.classList.add('today');
            const number = element('span', 'calendar-date-number-wrap');
            number.append(element('span', 'calendar-date-number', dayNumberFormatter.format(date)));
            if (key === iso(today)) number.append(element('span', 'calendar-today-marker'));
            button.append(number);
            list.slice(0, 2).forEach(s => {
                const chip = element('span', 'calendar-chip', `${s.start_time} ${s.course_title}${s.status === 'X' ? ` (${messages.cancelled})` : ''}`);
                chip.style.setProperty('--chip-color', sessionColor(s));
                chip.title = `${s.course_title} · ${s.instructor_name} · ${s.status_display}`;
                if (s.status === 'X') chip.classList.add('session-cancelled-chip');
                button.append(chip);
            });
            if (list.length > 2) button.append(element('span', 'calendar-chip-more', `+${list.length - 2} ${messages.more}`));
            button.addEventListener('click', () => { selectedDate = date; if (!visibleMonth) monthStart = firstOfMonth(date); render(); });
            fragment.append(button);
        }
        grid.replaceChildren(fragment);
        return monthEnd;
    }
    function renderDay(byDay) {
        els.selectedDate.textContent = dayFormatter.format(selectedDate);
        const list = byDay.get(iso(selectedDate)) || [];
        if (!list.length) {
            els.selectedEvents.replaceChildren(emptyState(messages.noClasses, messages.anotherDay));
            return;
        }
        const fragment = document.createDocumentFragment();
        for (const s of list) {
            const card = element('article', 'calendar-event-card');
            card.style.setProperty('--event-color', sessionColor(s));
            const time = element('div', 'calendar-event-time');
            time.append(element('i', 'bi bi-clock'), element('span', '', `${s.start_time} – ${s.end_time}`));
            const person = element('div', 'calendar-event-meta');
            person.append(element('i', 'bi bi-person'), element('span', '', s.instructor_name));
            const category = element('div', 'calendar-event-meta');
            category.append(element('i', 'bi bi-tag'), element('span', '', s.category_name));
            const room = s.classroom ? element('div', 'calendar-event-room', `${isPersian ? 'کلاس' : 'Room'} ${s.classroom}`) : null;
            const state = element('div', `calendar-event-status status-${s.status.toLowerCase()}`, s.status_display);
            card.append(time, element('div', 'calendar-event-title', s.course_title), person, category);
            if (room) card.append(room);
            card.append(state);
            if (s.status === 'X' && s.cancellation_reason) card.append(element('div', 'calendar-cancel-reason', `${messages.reason}: ${s.cancellation_reason}`));
            if (canMark) {
                const link = element('a', 'calendar-attendance-link', messages.attendance);
                link.href = attendanceLink(s);
                card.append(link);
            }
            fragment.append(card);
        }
        els.selectedEvents.replaceChildren(fragment);
    }
    function renderUpcoming(filtered) {
        const selectedKey = iso(selectedDate);
        const upcoming = filtered.filter(s => s.date >= selectedKey && s.status !== 'X').slice(0, 5);
        if (!upcoming.length) {
            els.upcoming.replaceChildren(emptyState(messages.noUpcoming, messages.tryDate));
            return;
        }
        const fragment = document.createDocumentFragment();
        for (const s of upcoming) {
            const date = parseDate(s.date);
            const row = element('div', 'calendar-upcoming-item');
            const dateBox = element('div', 'calendar-upcoming-date');
            dateBox.append(element('strong', '', dayNumberFormatter.format(date)), element('span', '', shortMonthFormatter.format(date)));
            const detail = element('div', 'calendar-upcoming-detail');
            detail.append(element('strong', '', s.course_title), element('span', '', `${s.start_time}–${s.end_time} · ${s.instructor_name}${s.classroom ? ' · ' + (isPersian ? 'کلاس ' : 'Room ') + s.classroom : ''} · ${s.status_display}`));
            row.append(dateBox, detail);
            fragment.append(row);
        }
        els.upcoming.replaceChildren(fragment);
    }
    function renderStats(filtered, monthEnd) {
        els.stats.courses.textContent = String(new Set(filtered.map(s => s.course_id)).size);
        els.stats.instructors.textContent = String(new Set(filtered.map(s => s.instructor_id)).size);
        els.stats.sessions.textContent = String(filtered.filter(s => parseDate(s.date) >= monthStart && parseDate(s.date) < monthEnd).length);
        els.stats.schedules.textContent = String(new Set(filtered.map(s => s.schedule_id)).size);
    }
    function render() {
        const filtered = filteredSessions();
        const grouped = groupedByDate(filtered);
        const monthEnd = renderGrid(grouped);
        renderDay(grouped);
        renderUpcoming(filtered);
        renderStats(filtered, monthEnd);
    }
    document.getElementById('calendar-previous').addEventListener('click', () => { monthStart = previousMonth(monthStart); selectedDate = monthStart; render(); });
    document.getElementById('calendar-next').addEventListener('click', () => { monthStart = nextMonth(monthStart); selectedDate = monthStart; render(); });
    document.getElementById('calendar-today').addEventListener('click', () => { selectedDate = today; monthStart = firstOfMonth(today); render(); });
    document.getElementById('calendar-clear').addEventListener('click', () => { els.search.value = ''; els.category.value = ''; els.instructor.value = ''; render(); });
    [els.search, els.category, els.instructor].forEach(field => field.addEventListener('input', render));
    render();
})();
