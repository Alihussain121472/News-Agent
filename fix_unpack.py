import os

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the unpacking in create_or_update_user_account
content = content.replace('user_id, existing_name, existing_hash = existing', 'user_id, existing_name, existing_hash = existing[:3] if len(existing) >= 3 else (0, None, None)')

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
