import os
import re

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix SQLite date('now') to PostgreSQL CURRENT_DATE
content = content.replace("date('now')", "CURRENT_DATE")
content = content.replace("CURRENT_DATE, '+' || notify_before_days || ' days'", "CURRENT_DATE + (notify_before_days || ' days')::interval")
content = content.replace("strftime('%Y-%m-%d', 'now')", "CURRENT_DATE")
content = content.replace("strftime('%Y-%m', 'now')", "TO_CHAR(CURRENT_DATE, 'YYYY-MM')")

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed PostgreSQL date functions")
