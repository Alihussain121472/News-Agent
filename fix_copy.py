import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('Every hour, our AI agent scans', 'Every 24 hours, our AI agent scans')

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
