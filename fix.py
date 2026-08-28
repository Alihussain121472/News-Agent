import re
with open('web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("is_logged_in=is_user)", "is_logged_in=is_user, is_admin=(session.get('role') == 'admin'))")

with open('web_server.py', 'w', encoding='utf-8') as f:
    f.write(text)
