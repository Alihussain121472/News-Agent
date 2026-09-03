import re

with open('web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the hourly cron with a daily cron
text = text.replace("scheduler.add_job(\n            _safe_fetch_hourly, 'cron', minute=0,\n            id='hourly_news_fetch'", "scheduler.add_job(\n            _safe_fetch_hourly, 'cron', hour=0, minute=0,\n            id='daily_news_fetch'")

with open('web_server.py', 'w', encoding='utf-8') as f:
    f.write(text)
