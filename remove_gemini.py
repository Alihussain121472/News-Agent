import re
with open('requirements.txt', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'google-generativeai==[0-9\.]+', '', text)
text = "\n".join([line for line in text.split('\n') if line.strip()])

with open('requirements.txt', 'w', encoding='utf-8') as f:
    f.write(text)
