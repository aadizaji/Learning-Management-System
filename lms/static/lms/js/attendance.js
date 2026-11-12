(() => {
    'use strict';
    const chooser = document.getElementById('attendance-select-form');
    if (chooser) {
        const course = document.getElementById('attendance-course');
        const session = document.getElementById('attendance-session');
        course?.addEventListener('change', () => {
            // An old session ID cannot be reused with the newly selected course.
            if (session) session.value = '';
            chooser.requestSubmit();
        });
        session?.addEventListener('change', () => chooser.requestSubmit());
    }
    const isPersian = document.documentElement.lang.toLowerCase().startsWith('fa');
    const formatter = new Intl.DateTimeFormat(isPersian ? 'fa-IR-u-ca-persian' : 'en-US',
        {year:'numeric',month:'long',day:'numeric',weekday:'long'});
    const formatDate = iso => {
        if (!/^\d{4}-\d{2}-\d{2}$/.test(iso)) return iso;
        const [year,month,day]=iso.split('-').map(Number);
        return formatter.format(new Date(year,month-1,day,12));
    };
    document.querySelectorAll('[data-local-date]').forEach(node => {
        node.textContent = formatDate(node.dataset.localDate);
    });
    document.querySelectorAll('#attendance-session option[data-date-iso]').forEach(option => {
        const room = option.dataset.room ? ` · ${isPersian ? 'کلاس' : 'Room'} ${option.dataset.room}` : '';
        option.textContent = `${formatDate(option.dataset.dateIso)} · ${option.dataset.time} · ${option.dataset.instructor}${room} (${option.dataset.status})`;
    });
    const entry = document.getElementById('attendance-entry');
    if (!entry) return;
    function refresh() {
        let present = 0, absent = 0, unmarked = 0;
        entry.querySelectorAll('.att-status-options').forEach(group => {
            const checked = group.querySelector('input:checked');
            if (checked?.value === 'P') present++;
            else if (checked?.value === 'A') absent++;
            else unmarked++;
        });
        document.getElementById('att-present').textContent = String(present);
        document.getElementById('att-absent').textContent = String(absent);
        document.getElementById('att-unmarked').textContent = String(unmarked);
    }
    entry.addEventListener('change', refresh);
    refresh();
})();
