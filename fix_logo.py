import re

files = [
    'templates/index.html',
    'templates/user_dashboard.html',
    'templates/dashboard.html'
]

for filepath in files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        # Fix the logo icon color inside the rounded box
        # Currently: <div class="w-8 h-8 rounded-lg bg-neutral-900 dark:bg-white flex items-center justify-center">
        #            <i class="fas fa-newspaper text-neutral-900 dark:text-white text-sm"></i>
        #            </div>
        # Need: text-white dark:text-neutral-900 on the icon
        
        text = text.replace('bg-neutral-900 dark:bg-white flex items-center justify-center">\n            <i class="fas fa-newspaper text-neutral-900 dark:text-white text-sm"', 'bg-neutral-900 dark:bg-white flex items-center justify-center">\n            <i class="fas fa-newspaper text-white dark:text-neutral-900 text-sm"')
        text = text.replace('bg-neutral-900 dark:bg-white flex items-center justify-center">\n          <i class="fas fa-newspaper text-neutral-900 dark:text-white text-sm"', 'bg-neutral-900 dark:bg-white flex items-center justify-center">\n          <i class="fas fa-newspaper text-white dark:text-neutral-900 text-sm"')
        
        # Check for footer logo which has a different background color sometimes
        text = text.replace('w-8 h-8 rounded-lg r from-blue-500 to-blue-700 flex items-center justify-center">\n              <i class="fas fa-newspaper text-neutral-900 dark:text-white text-xs"', 'w-8 h-8 rounded-lg bg-gradient-to-r from-blue-500 to-blue-700 flex items-center justify-center">\n              <i class="fas fa-newspaper text-white text-xs"')

        # Check for admin dashboard logo
        text = text.replace('w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">\n          <i class="fas fa-shield-alt text-white text-sm"', 'w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">\n          <i class="fas fa-shield-alt text-white text-sm"')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        print(f"Error on {filepath}: {e}")
