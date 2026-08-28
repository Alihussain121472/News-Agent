import os
import re

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken helper function
fixed_helper = '''def to_dict(row):
    if row is None: return None
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, datetime):
            d[k] = str(v)
    return d'''

content = re.sub(r'def to_to_dict\(row\):.*?(?=    class NewsDatabase)', fixed_helper + '\n\n', content, flags=re.DOTALL)
content = content.replace("def to_to_dict(row):", "def to_dict(row):")
content = content.replace("d = to_dict(row)", "d = dict(row)")
content = content.replace("to_to_dict", "to_dict")

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed to_dict in database.py")
