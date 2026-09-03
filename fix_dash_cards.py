import re

with open('templates/user_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Make sure cards have hover-card class
text = text.replace('class="bg-white dark:bg-slate-900/70 backdrop-blur-md shadow-sm border border-neutral-200 dark:border-slate-700/50', 'class="hover-card bg-white dark:bg-slate-900/70 backdrop-blur-md border border-neutral-200 dark:border-slate-700/50')

# Also in the dynamically injected JS inside user_dashboard.html
text = text.replace("class=\"bg-white dark:bg-slate-900/70 backdrop-blur-md shadow-sm border border-neutral-200", "class=\"hover-card bg-white dark:bg-slate-900/70 backdrop-blur-md border border-neutral-200")

with open('templates/user_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
