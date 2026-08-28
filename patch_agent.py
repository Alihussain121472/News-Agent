import os
import re

with open('ai_news_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_digest = '''    news_items = search_ai_news(limit=5)
    if news_items:
        db.save_news_batch(news_items)

    html = format_news_email(news_items)
    subject = f'AI Morning Brief - {datetime.now().strftime("%B %d, %Y")}'
    success_count = 0

    for to_email in recipients:
        if send_email(to_email, subject, html):
            success_count += 1
            db.log_email_sent(to_email, subject, len(news_items), 'success')
            db.update_user_email_sent(to_email)
        else:
            db.log_email_sent(to_email, subject, len(news_items), 'failed', 'Email sending failed')'''

new_digest = '''    news_items = search_ai_news(limit=25)
    if news_items:
        db.save_news_batch(news_items)

    subject = f'AI Morning Brief - {datetime.now().strftime("%B %d, %Y")}'
    success_count = 0

    for to_email in recipients:
        # Personalize for this user
        prefs = db.get_user_preferences(to_email)
        pref_keywords = (prefs.get('companies', '') + ' ' + prefs.get('fields', '')).lower().split()
        
        user_news = news_items[:]
        if pref_keywords:
            def score(a):
                s = 0
                text = (a.get('title', '') + ' ' + a.get('summary', '')).lower()
                for k in pref_keywords:
                    if len(k) > 2 and k in text:
                        s += 1
                return s
            user_news.sort(key=score, reverse=True)
            
        top_news = user_news[:5]
        html = format_news_email(top_news)
        
        if send_email(to_email, subject, html):
            success_count += 1
            db.log_email_sent(to_email, subject, len(top_news), 'success')
            db.update_user_email_sent(to_email)
        else:
            db.log_email_sent(to_email, subject, len(top_news), 'failed', 'Email sending failed')'''

content = content.replace(old_digest, new_digest)

# Add cleanup call
if 'db.cleanup_saved_articles(days=30)' not in content:
    content = content.replace('db.cleanup_old_articles(months=3)', 'db.cleanup_old_articles(months=3)\n    try:\n        db.cleanup_saved_articles(days=30)\n    except Exception: pass')

with open('ai_news_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated ai_news_agent.py with personalized sorting and memory cleanup")
