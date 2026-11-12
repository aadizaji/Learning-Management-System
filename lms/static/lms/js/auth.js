(function () {
  'use strict';
  const root = document.documentElement;
  const KEY = 'sematec-lms-theme';
  const btn = document.getElementById('auth-theme-toggle');
  const icon = document.getElementById('auth-theme-icon');
  const saved = localStorage.getItem(KEY) || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  function paint(theme) {
    if (theme === 'dark') root.setAttribute('data-theme','dark'); else root.removeAttribute('data-theme');
    if (icon) icon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon-stars';
  }
  paint(saved);
  if(btn) btn.addEventListener('click', function(){const next = root.hasAttribute('data-theme') ? 'light' : 'dark';paint(next);localStorage.setItem(KEY,next);});
  document.querySelectorAll('[data-toggle-password]').forEach(function(button){
    button.addEventListener('click',function(){const field=document.getElementById(button.dataset.togglePassword);if(!field)return;field.type=field.type==='password'?'text':'password';const i=button.querySelector('i');if(i)i.className=field.type==='text'?'bi bi-eye-slash':'bi bi-eye';});
  });
})();
