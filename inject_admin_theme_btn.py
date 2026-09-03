import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

theme_btn = r'<button onclick="toggleTheme()" class="bg-white dark:bg-slate-900/70 backdrop-blur-md shadow-sm border border-neutral-200 dark:border-slate-700/50 hover:bg-white/10 text-xs text-neutral-600 dark:text-slate-300 px-3 py-2 rounded-lg transition"><i class="fas fa-moon dark:hidden"></i><i class="fas fa-sun hidden dark:inline"></i></button>'

text = text.replace('<a href="/" class="bg-white', theme_btn + '\n          <a href="/" class="bg-white')
text = text.replace('bg-black/40', 'bg-white/90 dark:bg-black/40')

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
