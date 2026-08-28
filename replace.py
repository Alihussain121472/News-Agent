import os

def replace_in_file(path, old, new):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

replace_in_file('templates/user_login.html', 'User Sign In ”', 'User Sign In -')
replace_in_file('templates/user_login.html', 'Admin Access †’', 'Admin Access &rarr;')
replace_in_file('templates/user_register.html', 'Create Free Account ”', 'Create Free Account -')
replace_in_file('templates/user_dashboard.html', 'My Dashboard ”', 'My Dashboard -')
replace_in_file('templates/index.html', 'Open My Dashboard </a>', 'Open My Dashboard &rarr;</a>')
replace_in_file('templates/index.html', 'Open Student Dashboard </a>', 'Open Student Dashboard &rarr;</a>')
