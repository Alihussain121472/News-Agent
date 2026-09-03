import re

with open('scratch/user_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# The corrupted part starts after <script src="https://cdn.tailwindcss.com">
# and ends before <link rel="stylesheet" href="/static/css/tailwind.css">

pattern = re.compile(r'(<script src="https://cdn\.tailwindcss\.com">).*?(<link rel="stylesheet" href="/static/css/tailwind\.css">)', re.DOTALL)

replacement = r'''\1</script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          fontFamily: { sans: ['Inter', 'sans-serif'] },
        }
      }
    }
  </script>
  <script>
    // Theme logic
    if (localStorage.getItem('color-theme') === 'dark' || (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
  </script>
  \2'''

fixed_text = pattern.sub(replacement, text)

# Also remove the hardcoded style block
style_pattern = re.compile(r'<style>.*?body\{background:linear-gradient.*?\}[\s\S]*?</style>', re.DOTALL)
fixed_text = style_pattern.sub('', fixed_text)

# Fix body tag
fixed_text = fixed_text.replace('<body class="font-sans text-slate-200">', '<body class="font-sans text-neutral-900 dark:text-neutral-100 bg-neutral-50 dark:bg-neutral-950 transition-colors duration-300">')

with open('scratch/user_dashboard_fixed.html', 'w', encoding='utf-8') as f:
    f.write(fixed_text)
