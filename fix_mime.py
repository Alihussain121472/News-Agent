with open('ai_news_agent.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("MIMEText(html_content, 'html')", "MIMEText(html_content, 'html', 'utf-8')")
text = text.replace("MIMEText(html, 'html')", "MIMEText(html, 'html', 'utf-8')")

with open('ai_news_agent.py', 'w', encoding='utf-8') as f:
    f.write(text)
