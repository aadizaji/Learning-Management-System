(function(){
  'use strict';
  // Read-only date labels: the Gregorian ISO value remains the source of truth.
  // In a Persian interface, display its Jalali equivalent without touching forms.
  if (document.documentElement.lang.toLowerCase().startsWith('fa')) {
    const formatter = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      year: 'numeric', month: 'long', day: 'numeric'
    });
    document.querySelectorAll('time.js-localized-date[datetime]').forEach(function(node) {
      const iso = node.getAttribute('datetime');
      if (!/^\d{4}-\d{2}-\d{2}$/.test(iso || '')) return;
      const parts = iso.split('-').map(Number);
      const date = new Date(parts[0], parts[1] - 1, parts[2], 12);
      if (!Number.isNaN(date.getTime()) && date.getFullYear() === parts[0] &&
          date.getMonth() === parts[1] - 1 && date.getDate() === parts[2]) {
        node.textContent = formatter.format(date);
      }
    });
  }
  document.addEventListener('click',function(event){
    document.querySelectorAll('details.account-menu[open]').forEach(function(menu){if(!menu.contains(event.target)) menu.open=false;});
  });
  document.addEventListener('keydown',function(event){
    if(event.key==='Escape')document.querySelectorAll('details.account-menu[open]').forEach(function(menu){menu.open=false;});
  });
})();
