import re
with open('database.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("e.status=''success''", "e.status='success'")

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(text)
