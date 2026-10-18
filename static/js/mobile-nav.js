/**
 * Accessible Mobile Navigation Drawer Controller
 * Handles toggling, ARIA state updates, escape key closing, and outside click dismiss.
 */
document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.querySelector('[data-nav-toggle]');
  const drawer = document.getElementById('mobileNavDrawer');

  if (!toggleBtn || !drawer) return;

  function setDrawerOpen(isOpen) {
    toggleBtn.setAttribute('aria-expanded', String(isOpen));
    drawer.classList.toggle('is-open', isOpen);
    if (isOpen) {
      const firstLink = drawer.querySelector('a');
      if (firstLink) firstLink.focus();
    }
  }

  toggleBtn.addEventListener('click', (event) => {
    event.stopPropagation();
    const currentlyOpen = toggleBtn.getAttribute('aria-expanded') === 'true';
    setDrawerOpen(!currentlyOpen);
  });

  // Dismiss on click outside
  document.addEventListener('click', (event) => {
    if (!drawer.contains(event.target) && !toggleBtn.contains(event.target)) {
      setDrawerOpen(false);
    }
  });

  // Dismiss on Escape key
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && toggleBtn.getAttribute('aria-expanded') === 'true') {
      setDrawerOpen(false);
      toggleBtn.focus();
    }
  });

  // Reset if window resized into desktop breakpoint
  window.addEventListener('resize', () => {
    if (window.innerWidth >= 768 && toggleBtn.getAttribute('aria-expanded') === 'true') {
      setDrawerOpen(false);
    }
  });
});
