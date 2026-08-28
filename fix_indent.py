with open('database.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with open('database.py', 'w', encoding='utf-8') as f:
    for line in lines:
        if line.startswith('                cursor.execute(') and 'user_preferences' in line:
            f.write(line.replace('                cursor.execute(', '        cursor.execute('))
        else:
            f.write(line)
