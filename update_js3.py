import re

with open('templates/user_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's find exactly what's there
parts = text.split("document.getElementById('overviewArticles').innerHTML = arts.length ? arts.map(a=>`")
if len(parts) > 1:
    before = parts[0]
    rest = parts[1]
    
    parts2 = rest.split("`).join('') :", 1)
    if len(parts2) > 1:
        after = parts2[1]
        
        new_mid = """
      <a href="${a.url && a.url !== '#' ? a.url : 'javascript:switchTab(\\'articles\\')'}" target="${a.url && a.url !== '#' ? '_blank' : '_self'}" class="block bg-dark-800/60 rounded-xl p-3 border border-slate-700/50 hover:border-blue-500/50 transition cursor-pointer">
        <div class="text-sm font-semibold text-white leading-snug mb-1">${a.title||'Untitled'}</div>
        <div class="text-xs text-slate-500">${a.source||''} &middot; ${relTime(a.fetched_at)}</div>
      </a>"""
        
        text = before + "document.getElementById('overviewArticles').innerHTML = arts.length ? arts.map(a=>`" + new_mid + "`).join('') :" + after

with open('templates/user_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
