import re

files = ['templates/dashboard.html', 'templates/user_login.html', 'templates/user_register.html']

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Colors
    text = text.replace('bg-gradient-to-br from-[#0a0f1e] to-[#0f172a]', 'bg-white dark:bg-[#0a0f1e]')
    text = text.replace('border-slate-800', 'border-neutral-200 dark:border-slate-800')
    text = text.replace('border-white/10', 'border-neutral-200 dark:border-white/10')
    text = text.replace('text-white', 'text-neutral-900 dark:text-white')
    text = text.replace('text-slate-500', 'text-neutral-500 dark:text-slate-500')
    text = text.replace('text-slate-400', 'text-neutral-500 dark:text-slate-400')
    text = text.replace('text-slate-300', 'text-neutral-600 dark:text-slate-300')
    text = text.replace('text-slate-200', 'text-neutral-700 dark:text-slate-200')
    text = text.replace('bg-slate-800', 'bg-neutral-100 dark:bg-slate-800')
    text = text.replace('bg-slate-900', 'bg-white dark:bg-slate-900')

    # 2. Glass cards
    text = text.replace('class="glass', 'class="bg-white dark:bg-slate-900/70 backdrop-blur-md shadow-sm border border-neutral-200 dark:border-slate-700/50')
    text = re.sub(r'class="([^"]*?)glass([^"]*?)"', r'class="\1bg-white dark:bg-slate-900/70 backdrop-blur-md shadow-sm border border-neutral-200 dark:border-slate-700/50\2"', text)
    
    # Body replacement
    text = text.replace('<body class="font-sans text-slate-200">', '<body class="font-sans text-neutral-900 dark:text-neutral-100 bg-neutral-50 dark:bg-neutral-950 transition-colors duration-300">')
    text = text.replace('<body class="font-sans text-neutral-900 dark:text-neutral-100 bg-neutral-900 flex items-center justify-center min-h-screen relative overflow-hidden">', '<body class="font-sans text-neutral-900 dark:text-neutral-100 bg-neutral-50 dark:bg-neutral-950 flex items-center justify-center min-h-screen relative overflow-hidden transition-colors duration-300">')
    
    # 3. Insert tailwind config and theme toggle script in head if not present
    if 'tailwind.config' not in text:
        script_inj = r'''
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: { extend: { fontFamily: { sans: ['Inter', 'sans-serif'] } } }
    }
  </script>
  <script>
    if (localStorage.getItem('color-theme') === 'dark' || (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
    function toggleTheme() {
        const htmlEl = document.documentElement;
        htmlEl.classList.toggle('dark');
        if (htmlEl.classList.contains('dark')) {
            localStorage.setItem('color-theme', 'dark');
        } else {
            localStorage.setItem('color-theme', 'light');
        }
    }
  </script>
</head>'''
        text = text.replace('</head>', script_inj)

    # Remove hardcoded styles
    style_pattern = re.compile(r'<style>.*?body\{background:linear-gradient.*?\}[\s\S]*?</style>', re.DOTALL)
    text = style_pattern.sub('', text)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
