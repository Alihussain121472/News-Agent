import re

with open('templates/admin_login.html', 'r', encoding='utf-8') as f:
    text = f.read()

p = re.compile(r'<div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-2xl shadow-indigo-500/30 mb-4">\s*<i class="fas fa-shield-alt text-white text-2xl"></i>\s*</div>')
text = p.sub('<img src="/static/nova-logo.png" alt="Nova Brief Admin Logo" class="inline-flex items-center justify-center w-16 h-16 rounded-2xl object-cover shadow-2xl shadow-indigo-500/30 mb-4">', text)

with open('templates/admin_login.html', 'w', encoding='utf-8') as f:
    f.write(text)
