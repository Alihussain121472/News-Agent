import os

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

helper = '''from datetime import datetime, timedelta

def to_dict(row):
    if row is None: return None
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, datetime):
            d[k] = str(v)
    return d
'''

content = content.replace("from datetime import datetime, timedelta", helper)
content = content.replace("[dict(r)", "[to_dict(r)")
content = content.replace("dict(row)", "to_dict(row)")

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
