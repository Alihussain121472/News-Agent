import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Remove the script block from the bottom
bottom_script = r'''    // Check local storage or system preference
    if (localStorage.getItem('color-theme') === 'dark' || (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        htmlEl.classList.add('dark');
    } else {
        htmlEl.classList.remove('dark');
    }'''

text = text.replace(bottom_script, '')

# Inject it into the head
head_script = r'''
  <script>
    if (localStorage.getItem('color-theme') === 'dark' || (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
  </script>
</head>'''

text = text.replace('</head>', head_script)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
