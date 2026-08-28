import os

with open('web_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix login_user_account
login_patch = '''    user_name = email.split('@')[0].title()
    if user:
        user_name = user.get('name') or user_name
        
    session.permanent = True
    session.update({'user_email': user['email'] if user else email, 'user_name': user_name, 'role': 'user'})'''

content = content.replace('''    user_name = user.get('name') or email.split('@')[0].title()
    session.permanent = True
    session.update({'user_email': user['email'], 'user_name': user_name, 'role': 'user'})''', login_patch)

# Also fix the frontend JS so that if d.error exists, it displays it properly instead of "Signing in..."
frontend_patch = '''msg.textContent = d.message || d.error || 'Unexpected error. Please try again.';'''

with open('web_server.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('templates/user_login.html', 'r', encoding='utf-8') as f:
    html = f.read()
    html = html.replace('''msg.textContent = d.message || 'Signing in...';''', frontend_patch)
with open('templates/user_login.html', 'w', encoding='utf-8') as f:
    f.write(html)
