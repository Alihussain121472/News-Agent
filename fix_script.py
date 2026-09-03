import re

with open('templates/user_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('<script src="https://cdn.tailwindcss.com">\nfunction toggleTheme()', '<script src="https://cdn.tailwindcss.com"></script>\n<script>\nfunction toggleTheme()')

with open('templates/user_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
