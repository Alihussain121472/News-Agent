import re
with open('render.yaml', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('buildCommand: pip install -r requirements.txt', 'buildCommand: pip install --disable-pip-version-check -r requirements.txt')

with open('render.yaml', 'w', encoding='utf-8') as f:
    f.write(text)
