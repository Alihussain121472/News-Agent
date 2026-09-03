import re

with open('scratch/user_dashboard_fixed.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace hardcoded dark classes with responsive ones
# 1. Sidebar
text = text.replace('bg-gradient-to-br from-[#0a0f1e] to-[#0f172a]', 'bg-white dark:bg-[#0a0f1e]')
text = text.replace('border-slate-800', 'border-neutral-200 dark:border-slate-800')
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

# 3. Add Theme Toggle Button to header
header_pattern = r'(<a href="/" class=".*?Home</a>)'
theme_button = r'<button onclick="toggleTheme()" class="p-2 text-neutral-500 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-slate-800 rounded-lg transition"><i class="fas fa-moon dark:hidden"></i><i class="fas fa-sun hidden dark:inline"></i></button>'
text = re.sub(header_pattern, theme_button + r'\n          \1', text)

# 4. Also need to add toggleTheme function to the script section
script_func = r'''
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
'''
text = text.replace('</script>', script_func, 1)

with open('scratch/user_dashboard_fixed2.html', 'w', encoding='utf-8') as f:
    f.write(text)
