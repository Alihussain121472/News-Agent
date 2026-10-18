import re

with open('web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_config = """    SESSION_COOKIE_SECURE=IS_PRODUCTION,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_DOMAIN='.novabrief.tech' if IS_PRODUCTION else None,
    SESSION_REFRESH_EACH_REQUEST=True,"""

new_config = """    SESSION_COOKIE_SECURE=IS_PRODUCTION,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_REFRESH_EACH_REQUEST=True,"""

if old_config in text:
    text = text.replace(old_config, new_config)
    with open('web_server.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Fixed SESSION_COOKIE_DOMAIN.")
else:
    print("Could not find the old config.")
