
  document.addEventListener('DOMContentLoaded', async () => {
    try {
      const res = await fetch('/analytics/api/unread-count');
      const data = await res.json();
      if (data.count > 0) {
        const badge = document.getElementById('inbox-badge');
        badge.textContent = data.count > 9 ? '9+' : data.count;
        badge.classList.remove('hidden');
      }
    } catch (e) {}
  });


