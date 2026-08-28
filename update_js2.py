import re

with open('templates/user_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the inner div of overviewArticles map
old_pattern = r'<div class="bg-dark-800/60 rounded-xl p-3 border border-slate-700/50 hover:border-blue-500/30 transition">\s*<div class="text-sm font-semibold text-white leading-snug mb-1">\${a\.title\|\|\'Untitled\'}</div>\s*<div class="text-xs text-slate-500">\${a\.source\|\|''} &middot; \${relTime\(a\.fetched_at\)}</div>\s*</div>'

new_pattern = r'''<a href="${a.url && a.url !== '#' ? a.url : 'javascript:switchTab(\\\'articles\\\')'}" target="${a.url && a.url !== '#' ? '_blank' : '_self'}" class="block bg-dark-800/60 rounded-xl p-3 border border-slate-700/50 hover:border-blue-500/50 transition cursor-pointer">
        <div class="text-sm font-semibold text-white leading-snug mb-1">${a.title||'Untitled'}</div>
        <div class="text-xs text-slate-500">${a.source||''} &middot; ${relTime(a.fetched_at)}</div>
      </a>'''

text = re.sub(old_pattern, new_pattern, text)

with open('templates/user_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
