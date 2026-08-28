import re

with open('templates/user_dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Remove statsGrid entirely
html = re.sub(r'<div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6" id="statsGrid"></div>\s*', '', html)

# 2. Change Titles
html = html.replace('<h3 class="font-bold text-white mb-4 flex items-center gap-2"><i class="fas fa-newspaper text-blue-400"></i> Latest Articles</h3>', 
                    '<h3 class="font-bold text-white mb-4 flex items-center gap-2"><i class="fas fa-newspaper text-blue-400"></i> World Top Tech Articles</h3>')
html = html.replace('<h3 class="font-bold text-white mb-4 flex items-center gap-2"><i class="fas fa-graduation-cap text-emerald-400"></i> Open Programs</h3>', 
                    '<h3 class="font-bold text-white mb-4 flex items-center gap-2"><i class="fas fa-graduation-cap text-emerald-400"></i> Applied Programs</h3>')

# 3. Update loadOverview() Javascript
# Remove the old statsGrid injection
html = re.sub(r'document\.getElementById\(\'statsGrid\'\)\.innerHTML = `.*?`;', '', html, flags=re.DOTALL)

# Update no programs message
old_programs_js = r"join\(\'\'\) : '<div class=\"text-slate-500 text-sm text-center py-4\">No programs yet\. Admin will add soon\.</div>';"
new_programs_js = r"join('') : `<div class=\"text-slate-500 text-sm text-center py-6\"><p class=\"mb-3\">You didn't apply in any program yet.</p><a href=\"/#programs\" class=\"inline-block bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-4 py-2 rounded-lg hover:bg-emerald-500/30 transition text-xs font-bold\">Apply to a Program &rarr;</a></div>`;"
html = re.sub(old_programs_js, new_programs_js, html)

# Add "will update hourly" to no articles message
old_articles_js = r"join\(\'\'\) : '<div class=\"text-slate-500 text-sm text-center py-4\">No articles yet\.</div>';"
new_articles_js = r"join('') : '<div class=\"text-slate-500 text-sm text-center py-6\">No articles fetched yet. System updates hourly.</div>';"
html = re.sub(old_articles_js, new_articles_js, html)

with open('templates/user_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
