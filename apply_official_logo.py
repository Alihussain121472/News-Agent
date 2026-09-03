import re

def replace_logo(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        # index.html navbar
        p1 = re.compile(r'<div class="w-8 h-8 rounded-lg bg-neutral-900 dark:bg-white flex items-center justify-center">\s*<i class="fas fa-newspaper[^>]*></i>\s*</div>')
        text = p1.sub('<img src="/static/nova-logo.png" alt="Nova Brief Logo" class="w-8 h-8 rounded-lg object-cover">', text)

        # index.html footer
        p2 = re.compile(r'<div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center">\s*<i class="fas fa-newspaper[^>]*></i>\s*</div>')
        text = p2.sub('<img src="/static/nova-logo.png" alt="Nova Brief Logo" class="w-8 h-8 rounded-lg object-cover">', text)

        # user_dashboard.html sidebar
        p3 = re.compile(r'<div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center">\s*<i class="fas fa-newspaper[^>]*></i>\s*</div>')
        text = p3.sub('<img src="/static/nova-logo.png" alt="Nova Brief Logo" class="w-9 h-9 rounded-xl object-cover">', text)

        # dashboard.html admin sidebar
        p4 = re.compile(r'<div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">\s*<i class="fas fa-shield-alt[^>]*></i>\s*</div>')
        text = p4.sub('<img src="/static/nova-logo.png" alt="Nova Brief Logo" class="w-9 h-9 rounded-xl object-cover">', text)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

replace_logo('templates/index.html')
replace_logo('templates/user_dashboard.html')
replace_logo('templates/dashboard.html')

