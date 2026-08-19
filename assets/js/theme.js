/* theme.js — dark/light toggle with no flash of wrong theme.
   Load the INLINE snippet in <head> (see snippets/head.html), and this file before </body>. */
(function () {
  var KEY = 'sw-theme';

  function current() {
    return document.documentElement.getAttribute('data-theme') || 'light';
  }

  function apply(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem(KEY, theme); } catch (e) {}
    document.querySelectorAll('.theme-toggle').forEach(function (btn) {
      btn.textContent = theme === 'light' ? '\u263E' : '\u2600';
      btn.setAttribute('aria-label', theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode');
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    apply(current());
    document.querySelectorAll('.theme-toggle').forEach(function (btn) {
      btn.addEventListener('click', function () {
        apply(current() === 'light' ? 'dark' : 'light');
      });
    });
  });
})();
