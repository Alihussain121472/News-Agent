import os
import re

with open('web_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Change limit=2 to limit=5 for the chatbot
content = content.replace('articles = db.get_recent_articles(limit=2)', 'articles = db.get_recent_articles(limit=5)')
# Update the chatbot reply text to say "5 news"
content = content.replace('reply = "Here are a few of the top AI and Tech headlines from today:<br><br>"', 'reply = "Here are 5 news of the top AI and Tech headlines from today:<br><br>"')

# Change user dashboard limit to 5
content = content.replace("'articles': db.get_recent_articles(limit=8)", "'articles': db.get_recent_articles(limit=5)")

with open('web_server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated web_server.py")
