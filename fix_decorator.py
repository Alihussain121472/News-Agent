with open('web_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('@login_required', '@user_required')

with open('web_server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed decorator NameError in web_server.py")
