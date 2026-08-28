import os

with open('ai_news_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "password = get_env_value('GMAIL_APP_PASSWORD', 'EMAIL_APP_PASSWORD')",
    "password = get_env_value('GMAIL_APP_PASSWORD', 'EMAIL_APP_PASSWORD', 'EMAIL_PASS')"
)

with open('ai_news_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated ai_news_agent.py")
