/* Date inputs remain Gregorian ISO values for Django. Persian users select Jalali
   dates in a locale-aware picker; no changes to model DateFields or form names. */
(() => {
    'use strict';
    const fa = document.documentElement.lang.toLowerCase().startsWith('fa');
    const toEnglish = text => String(text).replace(/[۰-۹٠-٩]/g, digit => {
        const chars = '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩';
        return String(chars.indexOf(digit) % 10);
    });
    const faNumbers = value => String(value).replace(/[0-9]/g, d => '۰۱۲۳۴۵۶۷۸۹'[Number(d)]);
    const persian = new Intl.DateTimeFormat('en-US-u-ca-persian-nu-latn', {year:'numeric', month:'numeric', day:'numeric'});
    const persianMonth = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {year:'numeric', month:'long'});
    const dayNames = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج'];
    const addDays = (d, count) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + count, 12);
    const fromISO = value => {
        const [y, m, d] = String(value).split('-').map(Number);
        return y && m && d ? new Date(y, m-1, d, 12) : new Date();
    };
    const toISO = d => [d.getFullYear(), String(d.getMonth()+1).padStart(2,'0'), String(d.getDate()).padStart(2,'0')].join('-');
    function persianParts(d) {
        const parts = Object.fromEntries(persian.formatToParts(d)
            .filter(v => ['year','month','day'].includes(v.type))
            .map(v => [v.type, Number(toEnglish(v.value))]));
        return parts;
    }
    const firstOfMonth = date => addDays(date, 1 - persianParts(date).day);
    function nextMonth(date) {
        const first = firstOfMonth(date), current = persianParts(first);
        let candidate = addDays(first, 28);
        while (persianParts(candidate).month === current.month && persianParts(candidate).year === current.year) {
            candidate = addDays(candidate, 1);
        }
        return candidate;
    }
    const prevMonth = date => firstOfMonth(addDays(firstOfMonth(date), -1));
    const readableFa = date => {
        const parts = persianParts(date);
        return faNumbers(`${parts.year}/${String(parts.month).padStart(2,'0')}/${String(parts.day).padStart(2,'0')}`);
    };

    document.querySelectorAll('input.js-date-input[type="date"]').forEach(input => {
        const shell = document.createElement('div'); shell.className = 'date-input-shell';
        input.parentNode.insertBefore(shell, input); shell.append(input);
        if (!fa) {
            const placeholder = document.createElement('span'); placeholder.className = 'date-input-placeholder';
            placeholder.textContent = 'YYYY-MM-DD'; placeholder.setAttribute('aria-hidden', 'true');
            const trigger = document.createElement('button'); trigger.type = 'button'; trigger.className = 'date-input-trigger';
            trigger.setAttribute('aria-label', 'Open Gregorian calendar'); trigger.innerHTML = '<i class="bi bi-calendar3"></i>';
            shell.append(placeholder, trigger);
            const update = () => shell.classList.toggle('has-value', Boolean(input.value));
            function openPicker() { input.focus(); if (typeof input.showPicker === 'function') try { input.showPicker(); } catch (_) {} }
            trigger.addEventListener('click', openPicker);
            input.addEventListener('change', update); input.addEventListener('input', update);
            input.addEventListener('click', openPicker); update();
            return;
        }
        // Keep the original input's name/id/value; hidden type submits ISO unchanged.
        input.type = 'hidden';
        const visible = document.createElement('input'); visible.type='text'; visible.className='jalali-display';
        visible.readOnly = true; visible.dir = 'ltr'; visible.placeholder = '۱۴۰۵/۰۸/۳۰';
        visible.setAttribute('aria-label', 'انتخاب تاریخ شمسی');
        const trigger = document.createElement('button'); trigger.type='button'; trigger.className='date-input-trigger';
        trigger.innerHTML = '<i class="bi bi-calendar3" aria-hidden="true"></i>'; trigger.setAttribute('aria-label', 'باز کردن تقویم شمسی');
        shell.append(visible, trigger);
        const panel = document.createElement('div'); panel.className='jalali-picker'; panel.hidden=true;
        panel.setAttribute('role','dialog'); panel.setAttribute('aria-label','تقویم شمسی');
        const header = document.createElement('div'); header.className='jalali-picker-header';
        const next = document.createElement('button'); next.type='button'; next.textContent='‹'; next.setAttribute('aria-label','ماه بعد');
        const title = document.createElement('strong');
        const prev = document.createElement('button'); prev.type='button'; prev.textContent='›'; prev.setAttribute('aria-label','ماه قبل');
        header.append(next,title,prev);
        const grid = document.createElement('div'); grid.className='jalali-calendar-grid';
        const foot = document.createElement('div'); foot.className='jalali-picker-foot';
        const todayButton=document.createElement('button'); todayButton.type='button'; todayButton.textContent='امروز';
        const closeButton=document.createElement('button'); closeButton.type='button'; closeButton.textContent='بستن';
        foot.append(todayButton,closeButton); panel.append(header,grid,foot); shell.append(panel);
        let viewDate = firstOfMonth(input.value ? fromISO(input.value) : new Date());
        function updateText() { visible.value = input.value ? readableFa(fromISO(input.value)) : ''; }
        function choose(date) {
            input.value=toISO(date); updateText(); panel.hidden=true;
            input.dispatchEvent(new Event('input', {bubbles:true}));
            input.dispatchEvent(new Event('change', {bubbles:true}));
        }
        function render() {
            const start = firstOfMonth(viewDate), end = nextMonth(start);
            title.textContent=persianMonth.format(start); grid.replaceChildren();
            dayNames.forEach(n=>{const el=document.createElement('span'); el.className='jalali-weekday';el.textContent=n; grid.append(el);});
            const offset=(start.getDay()+1)%7;
            for(let i=0;i<offset;i++){const empty=document.createElement('span');grid.append(empty);}
            for(let day=start;day<end;day=addDays(day,1)) {
                const button=document.createElement('button'); button.type='button'; button.textContent=faNumbers(persianParts(day).day);
                const key=toISO(day); button.className='jalali-day';
                if(input.value===key) button.classList.add('selected');
                if(key===toISO(new Date())) button.classList.add('today');
                button.setAttribute('aria-label',readableFa(day));
                button.addEventListener('click',()=>choose(day)); grid.append(button);
            }
        }
        const open = () => { viewDate=firstOfMonth(input.value?fromISO(input.value):new Date()); render(); panel.hidden=false; };
        visible.addEventListener('click',open); visible.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' ') {event.preventDefault();open();}});
        trigger.addEventListener('click',()=>panel.hidden?open():panel.hidden=true);
        next.addEventListener('click',()=>{viewDate=nextMonth(viewDate);render();});
        prev.addEventListener('click',()=>{viewDate=prevMonth(viewDate);render();});
        todayButton.addEventListener('click',()=>choose(new Date())); closeButton.addEventListener('click',()=>panel.hidden=true);
        document.addEventListener('pointerdown',event=>{if(!shell.contains(event.target)) panel.hidden=true;});
        document.addEventListener('keydown',event=>{if(event.key==='Escape')panel.hidden=true;});
        input.addEventListener('change', updateText); updateText();
    });
})();
