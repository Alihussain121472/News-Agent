lines = []
with open('database.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "admin_reply = CASE WHEN admin_reply IS NULL" in line:
        print(f"Found on line {i+1}: {line}")
