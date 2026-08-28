import re

with open('templates/user_dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# I will replace the layout with a Medium-style feed.
# But instead of regexing the whole file, I will rewrite it cleanly.
