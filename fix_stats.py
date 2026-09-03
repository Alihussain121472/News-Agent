import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('<div class="text-2xl font-black text-indigo-600 dark:text-indigo-400">24/7</div>\n              <div class="text-xs text-neutral-500 mt-1">Always On</div>', '<div class="text-2xl font-black text-indigo-600 dark:text-indigo-400">24h</div>\n              <div class="text-xs text-neutral-500 mt-1">Updates</div>')

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
