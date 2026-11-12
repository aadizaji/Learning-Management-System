/* Add weekly schedule rows without altering the Django formset contract. */
(() => {
    'use strict';
    const addButton = document.getElementById('add-schedule-slot');
    const container = document.getElementById('schedule-slots');
    const total = document.getElementById('id_schedules-TOTAL_FORMS');
    const template = document.getElementById('empty-schedule-slot');
    if (!addButton || !container || !total || !template) return;

    const startDate = document.getElementById('id_start_date');
    // Project weekday: Saturday=0; JavaScript: Sunday=0.
    function startWeekday() {
        if (!startDate?.value || !/^\d{4}-\d{2}-\d{2}$/.test(startDate.value)) return null;
        const [year, month, day] = startDate.value.split('-').map(Number);
        const test = new Date(year, month - 1, day, 12);
        return (test.getDay() + 1) % 7;
    }
    function suggestStartWeekday() {
        if (container.dataset.newCourse !== 'true') return;
        const day = startWeekday(); if (day === null) return;
        const rows = [...container.querySelectorAll('[data-schedule-slot]')];
        const selects = rows.map(row => row.querySelector('select[name$="-weekday"]')).filter(Boolean);
        // Preserve choices explicitly made by the user. Suggest only when none are selected.
        if (selects.some(select => select.value === String(day))) return;
        const target = selects.find(select => !select.value || select.dataset.autoWeekday === 'yes');
        if (target) { target.value = String(day); target.dataset.autoWeekday = 'yes'; }
    }
    function syncDeleted() {
        container.querySelectorAll('[data-schedule-slot]').forEach(row => {
            const checkbox = row.querySelector('input[name$="-DELETE"]');
            row.classList.toggle('is-deleted', !!checkbox && checkbox.checked);
        });
    }

    function syncInstructorOptions() {
        const assigned = document.getElementById('id_instructors');
        if (!assigned) return;
        const selected = new Set(Array.from(assigned.selectedOptions, option => option.value));
        container.querySelectorAll('select[name$="-instructor"]').forEach(select => {
            Array.from(select.options).forEach(option => {
                if (option.value) option.disabled = !selected.has(option.value);
            });
            if (select.value && !selected.has(select.value)) select.value = '';
        });
    }

    addButton.addEventListener('click', () => {
        const number = Number(total.value);
        if (!Number.isInteger(number) || number >= 30) return;
        const wrap = document.createElement('div');
        wrap.innerHTML = template.innerHTML.trim().replaceAll('__prefix__', String(number));
        const row = wrap.firstElementChild;
        if (!row) return;
        container.append(row);
        total.value = String(number + 1);
        syncInstructorOptions();
        const weekday = row.querySelector('select[name$="-weekday"]');
        if (weekday) weekday.focus();
        suggestStartWeekday();
    });
    container.addEventListener('change', event => {
        if (event.target.matches('input[name$="-DELETE"]')) syncDeleted();
    });
    container.addEventListener('change', event => {
        if (event.target.matches('select[name$="-weekday"]') && event.isTrusted) {
            event.target.dataset.autoWeekday = 'no';
        }
    });
    if (startDate) startDate.addEventListener('change', suggestStartWeekday);
    const instructorList = document.getElementById('id_instructors');
    if (instructorList) instructorList.addEventListener('change', syncInstructorOptions);
    syncDeleted();
    syncInstructorOptions();
    suggestStartWeekday();
})();
