with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('''def fetchone(self): return (0,)''', '''def fetchone(self): return (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)''')

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
