import re
with open('database.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('status="success"', "status='success'")
text = text.replace('role TEXT DEFAULT "user"', "role TEXT DEFAULT 'user'")

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(text)
