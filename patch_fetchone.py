import re

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Helper function to add at the top
helper_func = '''
def _fetch_val(cursor):
    row = cursor.fetchone()
    if not row: return 0
    if hasattr(row, 'values'): return list(row.values())[0]
    return row[0]
'''

if '_fetch_val' not in content:
    content = content.replace('class DummyDictCursor:', helper_func + '\nclass DummyDictCursor:')

# Replace cursor.fetchone()[0] with _fetch_val(cursor)
content = content.replace('cursor.fetchone()[0]', '_fetch_val(cursor)')

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched database.py")
