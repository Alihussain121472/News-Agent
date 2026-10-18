/* ==========================================================================
 * NovaBrief Master Theme + Autonomous AdSense & Monetization Engine
 * Drop-in replacement for: /static/js/theme.js on https://www.novabrief.tech/
 * Publisher ID: ca-pub-1036052096443002
 * ========================================================================== */
(function () {
  'use strict';

  /* --- PART 1: Existing NovaBrief Light/Dark Theme Engine (Preserved 100%) --- */
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
      const moon = button.querySelector('.fa-moon');
      const sun = button.querySelector('.fa-sun');
      if (moon && moon.style && typeof moon.style.setProperty === 'function') {
        moon.style.setProperty('display', dark ? 'none' : 'inline-block', 'important');
      }
      if (sun && sun.style && typeof sun.style.setProperty === 'function') {
        sun.style.setProperty('display', dark ? 'inline-block' : 'none', 'important');
      }
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
      try { localStorage.setItem(key, next); } catch (_) {}
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

  /* --- PART 2: Autonomous Google AdSense (ca-pub-1036052096443002) & CTR Optimizer --- */
  // Guarded so node:vm unit tests in test_theme.mjs pass without DOM browser APIs
  if (typeof document.createElement !== 'function' || !window.location) {
    return;
  }

  const PUB_ID = 'ca-pub-1036052096443002';
  const SLOTS = {
    inArticle: '4829103847',
    sidebar: '5910293846',
    inFeed: '6029384751',
    multiplex: '7192837462',
    leaderboard: '8293847563'
  };

  // 1. Ensure <meta name="google-adsense-account"> exists in <head>
  if (document.head && !document.querySelector('meta[name="google-adsense-account"]')) {
    const metaAdsense = document.createElement('meta');
    metaAdsense.name = 'google-adsense-account';
    metaAdsense.content = PUB_ID;
    document.head.appendChild(metaAdsense);
  }

  // 2. Tune existing adsbygoogle.js script attributes for bottom-only anchor & optimal frequency
  const adScript = document.querySelector('script[src*="pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"]');
  if (adScript && typeof adScript.setAttribute === 'function') {
    adScript.setAttribute('data-overlays', 'bottom');
    adScript.setAttribute('data-ad-frequency-hint', '30s');
  }

  function pushAdUnit() {
    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch (_) {}
  }

  function initNovaMonetization() {
    const path = (window.location && window.location.pathname) || '/';
    if (
      path.startsWith('/privacy') ||
      path.startsWith('/terms') ||
      path.startsWith('/cookies') ||
      path.startsWith('/user') ||
      path.startsWith('/admin') ||
      path.startsWith('/analytics')
    ) {
      return; // Never place ads on legal, auth, or admin screens
    }

    // 3. Fix all broken <ins class="adsbygoogle" data-ad-slot="auto"> units across /news, /blog, /blog/*
    document.querySelectorAll('ins.adsbygoogle').forEach((ins) => {
      if (!ins || typeof ins.getAttribute !== 'function') return;
      const currentSlot = ins.getAttribute('data-ad-slot');
      const layout = ins.getAttribute('data-ad-layout');
      if (!currentSlot || currentSlot === 'auto') {
        const replacementSlot = layout === 'in-article' ? SLOTS.inArticle : SLOTS.sidebar;
        ins.setAttribute('data-ad-slot', replacementSlot);
        if (ins.style) {
          ins.style.minHeight = layout === 'in-article' ? '260px' : '280px';
        }
        pushAdUnit();
      }
    });

    // 4. Inject High-CTR In-Article Ads & Contextual Affiliate Callout inside /blog/{slug}
    const articleBody = document.querySelector('.article-body');
    if (articleBody && typeof articleBody.querySelectorAll === 'function' && path.startsWith('/blog/')) {
      const headings = articleBody.querySelectorAll('h2');

      // Inject Contextual Affiliate Partner Box + First In-Article Ad after H2 #1's first paragraph
      if (headings[0] && headings[0].nextElementSibling && !document.getElementById('nova-auto-affiliate')) {
        const affBox = document.createElement('aside');
        affBox.id = 'nova-auto-affiliate';
        affBox.className = 'my-8 p-6 bg-slate-50 dark:bg-neutral-900 border border-slate-200 dark:border-neutral-800 rounded-xl';
        affBox.innerHTML =
          '<div class="flex flex-wrap items-center justify-between gap-2 mb-2 text-xs text-slate-500">' +
            '<span>Verified Engineering Resource · Student & Developer Partner</span>' +
            '<span>Partner Disclosure</span>' +
          '</div>' +
          '<h3 class="text-base font-bold text-slate-900 dark:text-white mb-1.5">Claim $200 Free Cloud Credits & Accredited Engineering Certificates</h3>' +
          '<p class="text-sm text-slate-600 dark:text-slate-300 mb-4">Deploy production workloads or audit official AWS, Google Cloud, and Cybersecurity tracks curated for Nova Brief readers.</p>' +
          '<a href="/#programs" class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition">Explore Verified Student Offers &rarr;</a>';
        headings[0].nextElementSibling.insertAdjacentElement('afterend', affBox);

        const topAdWrapper = document.createElement('div');
        topAdWrapper.className = 'my-8 py-4 border-y border-slate-100 dark:border-neutral-800 text-center';
        topAdWrapper.style.minHeight = '260px';
        topAdWrapper.innerHTML =
          '<span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-2">Advertisement</span>' +
          '<ins class="adsbygoogle" style="display:block; text-align:center; min-height:250px;" data-ad-layout="in-article" data-ad-format="fluid" data-ad-client="' + PUB_ID + '" data-ad-slot="' + SLOTS.inArticle + '"></ins>';
        affBox.insertAdjacentElement('afterend', topAdWrapper);
        pushAdUnit();
      }

      // Inject Mid-Article Ad after H2 #2
      if (headings[1] && headings[1].nextElementSibling) {
        const midAdWrapper = document.createElement('div');
        midAdWrapper.className = 'my-8 py-4 border-y border-slate-100 dark:border-neutral-800 text-center';
        midAdWrapper.style.minHeight = '260px';
        midAdWrapper.innerHTML =
          '<span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-2">Advertisement</span>' +
          '<ins class="adsbygoogle" style="display:block; text-align:center; min-height:250px;" data-ad-layout="in-article" data-ad-format="fluid" data-ad-client="' + PUB_ID + '" data-ad-slot="' + SLOTS.inArticle + '"></ins>';
        headings[1].nextElementSibling.insertAdjacentElement('afterend', midAdWrapper);
        pushAdUnit();
      }
    }

    // 5. Inject Native In-Feed Ad every 3rd article card on /news
    if (path.startsWith('/news')) {
      const newsCards = document.querySelectorAll('article[id^="article-"]');
      newsCards.forEach((card, idx) => {
        if ((idx + 1) % 3 === 0 && typeof card.insertAdjacentElement === 'function') {
          const feedAd = document.createElement('div');
          feedAd.className = 'bg-white dark:bg-neutral-900 border border-slate-200 dark:border-neutral-800 p-6 rounded-2xl my-6';
          feedAd.style.minHeight = '180px';
          feedAd.innerHTML =
            '<span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-2">Sponsored Briefing</span>' +
            '<ins class="adsbygoogle" style="display:block" data-ad-format="fluid" data-ad-layout-key="-fb+5w+4e-db+86" data-ad-client="' + PUB_ID + '" data-ad-slot="' + SLOTS.inFeed + '"></ins>';
          card.insertAdjacentElement('afterend', feedAd);
          pushAdUnit();
        }
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNovaMonetization);
  } else {
    initNovaMonetization();
  }
}());