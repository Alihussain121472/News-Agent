from ai_news_agent import *
from database import NewsDatabase
from datetime import datetime

logger.info('Forcing news digest to all users...')
db = NewsDatabase()
recipients = get_recipients()
logger.info(f'Found {len(recipients)} recipients.')

news_items = search_ai_news(limit=25)
if news_items:
    db.save_news_batch(news_items)

# Force a new subject so it doesn't get skipped by 'delivered_before'
subject = f'Technology Morning Brief - {datetime.now().strftime("%B %d, %Y")} (Update)'
success_count = 0

for to_email in recipients:
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
        db.log_email_sent(to_email, subject, len(top_news), 'failed', 'Email sending failed')

logger.info(f'Successfully sent to {success_count} users.')
