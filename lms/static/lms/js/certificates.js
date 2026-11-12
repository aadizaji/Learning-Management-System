/* One live canvas for both languages. Drafts do not need to pass save validation. */
(() => {
  'use strict';
  const form = document.getElementById('certificate-form');
  if (!form) return;

  const student = document.getElementById('id_student');
  const register = document.getElementById('id_register');
  const preview = document.getElementById('certificate-preview-image');
  const empty = document.getElementById('certificate-preview-empty');
  const notice = document.getElementById('certificate-preview-message');
  const hint = document.getElementById('course-chooser-hint');
  const languageButtons = [...document.querySelectorAll('.cert-lang')];
  let language = 'en';
  let timer;
  let pending;
  let activeImageUrl;
  let courseRequestId = 0;
  let previewSequence = 0;

  function announce(message) { if (notice) notice.textContent = message; }

  function schedulePreview() {
    window.clearTimeout(timer);
    previewSequence += 1;
    if (pending) pending.abort();
    const sequence = previewSequence;
    timer = window.setTimeout(async () => {
      const controller = new AbortController();
      pending = controller;
      const requestedLanguage = language;
      const data = new FormData(form);
      data.set('language', requestedLanguage);
      announce(requestedLanguage === 'fa' ? 'در حال به‌روزرسانی پیش‌نمایش…' : 'Updating live preview…');
      try {
        const response = await fetch(form.dataset.previewUrl, {
          method: 'POST', body: data, credentials: 'same-origin',
          signal: controller.signal,
          headers: { 'Accept': 'image/png, application/json' }
        });
        if (controller.signal.aborted || sequence !== previewSequence) return;
        const contentType = response.headers.get('content-type') || '';
        if (!response.ok || !contentType.includes('image/png')) {
          const payload = contentType.includes('application/json')
            ? await response.json().catch(() => ({})) : {};
          if (response.redirected) throw new Error('Please sign in before previewing certificates.');
          const fields = payload.fields ? Object.values(payload.fields).flat().join(' ') : '';
          throw new Error(fields || payload.error || 'Could not render the preview.');
        }
        const blob = await response.blob();
        if (controller.signal.aborted || sequence !== previewSequence) return;
        const imageUrl = URL.createObjectURL(blob);
        const oldUrl = activeImageUrl;
        activeImageUrl = imageUrl;
        preview.onload = () => { if (oldUrl) URL.revokeObjectURL(oldUrl); };
        preview.src = imageUrl;
        preview.hidden = false;
        if (empty) empty.hidden = true;
        announce(requestedLanguage === 'fa'
          ? 'پیش‌نمایش فارسی زنده است؛ برای دانلود نسخه نهایی، ابتدا ذخیره کنید.'
          : 'Live English preview. Save to download the official certificate.');
      } catch (error) {
        if (error.name === 'AbortError' || sequence !== previewSequence) return;
        // Keep last successful preview visible while correcting invalid fields.
        announce(error.message || 'Preview unavailable.');
        if (!activeImageUrl && empty) empty.hidden = false;
      } finally {
        if (pending === controller) pending = null;
      }
    }, 300);
  }

  async function loadStudentCourses() {
    if (!student || !register || form.querySelector('[name=certificate_id]')) return;
    const requestId = ++courseRequestId;
    register.replaceChildren(new Option('Loading registered courses…', ''));
    register.disabled = true;
    if (hint) hint.textContent = 'Loading registered courses…';
    schedulePreview();
    if (!student.value) {
      register.replaceChildren(new Option('Select a student first', ''));
      register.disabled = false;
      if (hint) hint.textContent = 'Choose a student to see their registered courses.';
      schedulePreview();
      return;
    }
    try {
      const url = `${form.dataset.coursesUrl}?student_id=${encodeURIComponent(student.value)}`;
      const response = await fetch(url, {credentials: 'same-origin'});
      if (!response.ok) throw new Error('Unable to load courses for this student.');
      const data = await response.json();
      if (requestId !== courseRequestId) return;
      register.replaceChildren(new Option('Select a registered course', ''));
      for (const item of data.courses || []) {
        let title = `${item.title} · ${item.status}`;
        if (item.issued_id) title += ` · Already issued (${item.serial})`;
        if (item.dropped) title += ' · Not eligible';
        const opt = new Option(title, String(item.id));
        opt.disabled = Boolean(item.issued_id || item.dropped);
        register.add(opt);
      }
      if (hint) hint.textContent = data.courses.length
        ? 'Select a course registered for this student.'
        : 'This student has no registered courses.';
    } catch (error) {
      if (requestId !== courseRequestId) return;
      register.replaceChildren(new Option('Could not load courses', ''));
      if (hint) hint.textContent = error.message;
    } finally {
      if (requestId === courseRequestId) register.disabled = false;
      schedulePreview();
    }
  }

  if (student) student.addEventListener('change', loadStudentCourses);
  form.addEventListener('input', schedulePreview);
  form.addEventListener('change', schedulePreview);
  for (const button of languageButtons) {
    button.addEventListener('click', () => {
      language = button.dataset.language;
      for (const item of languageButtons) {
        const active = item === button;
        item.classList.toggle('active', active);
        item.setAttribute('aria-pressed', String(active));
      }
      schedulePreview();
    });
  }
  window.addEventListener('beforeunload', () => {
    window.clearTimeout(timer);
    if (pending) pending.abort();
    if (activeImageUrl) URL.revokeObjectURL(activeImageUrl);
  });
  // Render the draft template immediately, then update for every change.
  schedulePreview();
})();
