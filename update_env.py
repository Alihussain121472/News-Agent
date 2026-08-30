"""Safely update DATABASE_URL without storing credentials in source code."""
import os
import re

database_url = os.environ.get('NEW_DATABASE_URL', '').strip()
if not database_url:
    raise SystemExit('Set NEW_DATABASE_URL before running this helper.')

with open('.env', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'^DATABASE_URL=.*$', f'DATABASE_URL={database_url}', content, flags=re.MULTILINE)
with open('.env', 'w', encoding='utf-8') as f:
    f.write(content)
