import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Make Nova Brief logo text use gradient-link
text = text.replace('<span class="text-lg font-bold text-neutral-900 dark:text-white tracking-tight">Nova Brief</span>', '<span class="text-lg font-bold text-neutral-900 dark:text-white tracking-tight hover:gradient-link">Nova Brief</span>')
text = text.replace('<span class="font-bold text-neutral-900 dark:text-white">Nova Brief</span>', '<span class="font-bold text-neutral-900 dark:text-white hover:gradient-link">Nova Brief</span>')

# Make the big CTA link use gradient link
text = text.replace('<h2 class="text-4xl font-black text-neutral-900 dark:text-white mb-4">Join <span class="text-indigo-600 dark:text-indigo-400">Nova Brief</span></h2>', '<h2 class="text-4xl font-black text-neutral-900 dark:text-white mb-4">Join <span class="gradient-link">Nova Brief</span></h2>')

# Make some other text gradient-link
text = text.replace('href="#features" class="text-neutral-600 dark:text-neutral-300 hover:text-blue-500 dark:hover:text-blue-400', 'href="#features" class="text-neutral-600 dark:text-neutral-300 hover:gradient-link')
text = text.replace('href="#programs" class="text-neutral-600 dark:text-neutral-300 hover:text-blue-500 dark:hover:text-blue-400', 'href="#programs" class="text-neutral-600 dark:text-neutral-300 hover:gradient-link')

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
