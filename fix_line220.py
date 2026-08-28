with open('web_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("'email': user['email']}", "'email': user['email'] if user else email}")

with open('web_server.py', 'w', encoding='utf-8') as f:
    f.write(content)
