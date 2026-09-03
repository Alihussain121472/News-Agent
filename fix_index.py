import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix typos and add hover-card class
text = text.replace('hover:-tranneutral-y-1', 'hover-card')
text = text.replace('bg-white dark:bg-neutral-900/50 shadow-sm backdrop-blur-md border border-neutral-700/50 rounded-xl p-7 transition-all duration-200 hover:-tranneutral-y-1 hover:border-neutral-600', 'hover-card bg-white dark:bg-neutral-900/50 backdrop-blur-md border border-neutral-200 dark:border-neutral-700/50 rounded-xl p-7')

# Add hover-card to feature cards
text = text.replace('class="block bg-white dark:bg-neutral-900/50 shadow-sm backdrop-blur-md border border-neutral-700/50 rounded-xl p-7 transition-all duration-200', 'class="block hover-card bg-white dark:bg-neutral-900/50 backdrop-blur-md border border-neutral-200 dark:border-neutral-700/50 rounded-xl p-7')

# Add hover-card to program cards
text = text.replace('class="bg-white dark:bg-neutral-900/40 rounded-2xl border border-neutral-700/50 overflow-hidden flex flex-col"', 'class="hover-card bg-white dark:bg-neutral-900/40 rounded-2xl border border-neutral-200 dark:border-neutral-700/50 overflow-hidden flex flex-col"')

# Let's change standard links to gradient-link where appropriate, e.g., the top navbar links
text = text.replace('class="text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition text-sm font-medium"', 'class="text-neutral-600 dark:text-neutral-300 hover:text-blue-500 dark:hover:text-blue-400 transition text-sm font-medium"')

text = text.replace('class="hover:text-indigo-600 dark:text-indigo-400 transition"', 'class="hover:text-blue-500 dark:hover:text-blue-400 transition"')

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
