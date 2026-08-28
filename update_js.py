import re
with open('templates/user_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

old_js = """    const arts = (overviewData.articles||[]).slice(0,5);
    document.getElementById('overviewArticles').innerHTML = arts.length ? arts.map(a=>`
      <div class="bg-dark-800/60 rounded-xl p-3 border border-slate-700/50 hover:border-blue-500/30 transition">
        <div class="text-sm font-semibold text-white leading-snug mb-1">${a.title||'Untitled'}</div>
        <div class="text-xs text-slate-500">${a.source||''} &middot; ${relTime(a.fetched_at)}</div>
      </div>`).join('') : '<div class=\\"text-slate-500 text-sm text-center py-6\\">Intelligence feed pending. System synchronizes globally every hour.</div>';"""

new_js = """    const arts = (overviewData.articles||[]).slice(0,5);
    document.getElementById('overviewArticles').innerHTML = arts.length ? arts.map(a=>`
      <a href="${a.url && a.url !== '#' ? a.url : 'javascript:switchTab(\\\'articles\\\')'}" target="${a.url && a.url !== '#' ? '_blank' : '_self'}" class="block bg-dark-800/60 rounded-xl p-3 border border-slate-700/50 hover:border-blue-500/50 transition cursor-pointer">
        <div class="text-sm font-semibold text-white leading-snug mb-1">${a.title||'Untitled'}</div>
        <div class="text-xs text-slate-500">${a.source||''} &middot; ${relTime(a.fetched_at)}</div>
      </a>`).join('') : '<div class=\\"text-slate-500 text-sm text-center py-6\\">Intelligence feed pending. System synchronizes globally every hour.</div>';"""

text = text.replace(old_js, new_js)

with open('templates/user_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
