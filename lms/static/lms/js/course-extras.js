/* Grouped toman prices and dynamic ordered syllabus rows. */
(() => {
    'use strict';
    const price=document.querySelector('.js-price-input');
    if(price) {
        const normalize=v=>v.replace(/[۰-۹٠-٩]/g,d=>String('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩'.indexOf(d)%10)).replace(/[^0-9]/g,'');
        const format=()=>{
            const raw=normalize(price.value);
            const cursor=price.selectionStart || price.value.length;
            const before=normalize(price.value.slice(0,cursor)).length;
            price.value=raw.replace(/\B(?=(\d{3})+(?!\d))/g,',');
            let position=0, count=0;
            for(;position<price.value.length && count<before;position++) if(/[0-9]/.test(price.value[position]))count++;
            price.setSelectionRange(position,position);
        };
        price.addEventListener('input',format); format();
    }
    const add=document.getElementById('add-course-topic');
    const rows=document.getElementById('course-topics');
    const total=document.getElementById('id_topics-TOTAL_FORMS');
    const template=document.getElementById('empty-course-topic');
    if(!add || !rows || !total || !template)return;
    function renumber() {
        let index=0;
        rows.querySelectorAll('[data-topic-row]').forEach(row=>{
            const del=row.querySelector('input[name$="-DELETE"]');
            const deleted=Boolean(del?.checked);
            row.classList.toggle('is-deleted',deleted);
            if(!deleted){index++;const label=row.querySelector('.topic-number'); if(label)label.textContent=String(index);}
        });
    }
    add.addEventListener('click',()=>{
        const index=Number(total.value); if(!Number.isInteger(index)||index>=100)return;
        const wrapper=document.createElement('div');wrapper.innerHTML=template.innerHTML.trim().replaceAll('__prefix__',String(index));
        const row=wrapper.firstElementChild; if(!row)return;
        rows.append(row);total.value=String(index+1);renumber();
        row.querySelector('input[name$="-title"]')?.focus();
    });
    rows.addEventListener('change',e=>{if(e.target.matches('input[name$="-DELETE"]'))renumber();});
    renumber();
})();
