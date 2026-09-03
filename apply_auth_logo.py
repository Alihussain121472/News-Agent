import re

def update_auth_pages(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        p = re.compile(r'<div class="w-11 h-11 rounded-2xl bg-gradient-[^>]*>\s*<i class="fas fa-bolt[^>]*></i>\s*</div>')
        text = p.sub('<img src="/static/nova-logo.png" alt="Nova Brief Logo" class="w-11 h-11 rounded-2xl object-cover shadow-xl shadow-blue-500/20 group-hover:scale-105 transition">', text)
        
        # admin login uses fa-shield-alt maybe?
        p2 = re.compile(r'<div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-xl shadow-indigo-500/20 mx-auto">\s*<i class="fas fa-shield-alt[^>]*></i>\s*</div>')
        text = p2.sub('<img src="/static/nova-logo.png" alt="Nova Brief Logo" class="w-12 h-12 rounded-2xl object-cover shadow-xl shadow-indigo-500/20 mx-auto">', text)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        print(f"Error {filepath}: {e}")

update_auth_pages('templates/user_login.html')
update_auth_pages('templates/user_register.html')
update_auth_pages('templates/admin_login.html')
