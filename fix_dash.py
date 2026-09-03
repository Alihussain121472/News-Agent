import re

with open('templates/user_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('w-8 h-8 rounded-lg r from-blue-500 to-blue-700', 'w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700')
text = text.replace('w-8 h-8 rounded-xl r from-blue-500 to-emerald-500', 'w-8 h-8 rounded-xl bg-gradient-to-br from-blue-500 to-emerald-500')
text = text.replace('class="fas fa-newspaper text-neutral-900 dark:text-white text-xs"', 'class="fas fa-newspaper text-white text-xs"')

with open('templates/user_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
