/* Apply before first paint: light by default, dark only when explicitly chosen. */
(function () {
  'use strict';
  const key = 'color-theme';
  const root = document.documentElement;
  function storedTheme() {
    try { return localStorage.getItem(key) === 'dark' ? 'dark' : 'light'; }
    catch (_) { return 'light'; }
  }
  function updateControls() {
    const dark = root.classList.contains('dark');
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.setAttribute('aria-pressed', String(dark));
      button.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
      button.title = dark ? 'Switch to light mode' : 'Switch to dark mode';
      const label = button.querySelector('[data-theme-label]');
      if (label) label.textContent = dark ? 'Light mode' : 'Dark mode';
    });
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = dark ? '#080f1c' : '#f5f7fb';
  }
  function apply(theme, persist) {
    const next = theme === 'dark' ? 'dark' : 'light';
    root.classList.toggle('dark', next === 'dark');
    root.dataset.theme = next;
    root.style.colorScheme = next;
    if (persist) {
      try { localStorage.setItem(key, next); } catch (_) { /* Selection still works in this tab. */ }
    }
    updateControls();
  }
  function toggle() { apply(root.classList.contains('dark') ? 'light' : 'dark', true); }
  apply(storedTheme(), false);
  document.addEventListener('DOMContentLoaded', updateControls);
  document.addEventListener('click', event => {
    if (event.target.closest && event.target.closest('[data-theme-toggle]')) toggle();
  });
  window.addEventListener('storage', event => {
    if (event.key === key || event.key === null) apply(storedTheme(), false);
  });
  window.NovaTheme = Object.freeze({ toggle, apply: theme => apply(theme, true) });
  window.toggleTheme = toggle;
}());
