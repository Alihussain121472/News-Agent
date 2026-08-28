import re
with open('gen_articles.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("response = model.generate_content(a['prompt'])\n    html_content = markdown.markdown(response.text)", "content = generate_with_llama(a['prompt'])\n    html_content = markdown.markdown(content)")

with open('gen_articles.py', 'w', encoding='utf-8') as f:
    f.write(text)
