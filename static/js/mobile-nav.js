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
    if (window.innerWidth >= 1024 && toggleBtn.getAttribute('aria-expanded') === 'true') {
      setDrawerOpen(false);
    }
  });
});

// Fallback for ad blockers: hide empty ad slots if no ad filled them after 3 seconds
window.addEventListener('load', () => {
  setTimeout(() => {
    document.querySelectorAll('.ad-slot, .ad-slot-widget').forEach((slot) => {
      const ad = slot.querySelector('ins.adsbygoogle');
      if (!ad || ad.dataset.adStatus !== 'filled') {
        slot.style.display = 'none';
      }
    });
  }, 3000);
});
