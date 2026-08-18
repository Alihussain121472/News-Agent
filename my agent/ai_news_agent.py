import os
import sys
import json
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any

import requests
import feedparser
from dotenv import load_dotenv
from database import NewsDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_news_agent.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()


def get_env_value(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return ""


def clean_text(value: str, max_length: int = 220) -> str:
    text = (value or '').replace('\n', ' ').strip()
    if len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0] + '...'
    return text


def build_briefing_notes(title: str, summary: str) -> Dict[str, str]:
    title_lower = (title or '').lower()
    summary_lower = (summary or '').lower()

    if any(word in title_lower for word in ['security', 'privacy', 'deepfake', 'misinformation', 'risk', 'attack', 'vulnerability']):
        why_important = 'This raises a real safety or trust issue that could affect how people use AI in everyday life.'
    elif any(word in title_lower for word in ['regulation', 'policy', 'government', 'law', 'europe', 'eua', 'ai act']):
        why_important = 'This could change the rules around AI adoption, accountability, and how businesses operate.'
    elif any(word in title_lower for word in ['openai', 'google', 'meta', 'microsoft', 'anthropic', 'gemini', 'chatgpt']):
        why_important = 'A major company action often signals where the market and consumer behavior are shifting next.'
    elif any(word in title_lower for word in ['health', 'medical', 'drug', 'science', 'research']):
        why_important = 'This could affect healthcare, research speed, and the quality of decisions in critical areas.'
    else:
        why_important = 'This matters because it shows how quickly AI is moving from experiment to real-world influence.'

    if any(word in title_lower for word in ['job', 'work', 'labor', 'productivity', 'automation', 'assistant']):
        future_change = 'It could change how work gets done, which tasks are automated, and where human value still matters most.'
    elif any(word in title_lower for word in ['education', 'student', 'school', 'learning', 'teacher']):
        future_change = 'It could reshape learning, teaching, and how people build skills in the next few years.'
    elif any(word in title_lower for word in ['security', 'privacy', 'deepfake', 'fraud', 'misinformation']):
        future_change = 'It could make digital trust harder to maintain unless safeguards and public awareness improve quickly.'
    elif any(word in title_lower for word in ['energy', 'chip', 'compute', 'data center', 'infrastructure']):
        future_change = 'It could alter how companies invest in hardware, power, and digital infrastructure around AI.'
    else:
        future_change = 'It could influence consumer habits, business decisions, and the speed at which AI becomes part of daily life.'

    if any(word in summary_lower for word in ['risk', 'danger', 'harm', 'attack', 'fraud', 'misinformation', 'bias']):
        why_care = 'Because the downside is not theoretical; it can affect trust, safety, and the decisions people make online.'
    elif any(word in title_lower for word in ['chip', 'model', 'cost', 'latency', 'compute']):
        why_care = 'Because this often signals the next wave of AI adoption, pricing pressure, and accessibility for everyone.'
    elif any(word in title_lower for word in ['regulation', 'policy', 'law']):
        why_care = 'Because rules shape what AI can do, how fast it spreads, and how much control people retain.'
    else:
        why_care = 'Because what looks like a niche update today can become a normal part of life faster than expected.'

    return {
        'why_important': why_important,
        'future_change': future_change,
        'why_care': why_care,
    }


def fetch_news_from_rss(limit: int = 5) -> List[Dict[str, Any]]:
    """Fallback RSS source for AI news when NewsAPI is unavailable or rejected."""
    rss_url = 'https://news.google.com/rss/search?q=artificial+intelligence+OR+machine+learning+OR+generative+AI+OR+LLM+OR+AI+policy+OR+AI+safety&hl=en-US&gl=US&ceid=US:en'

    try:
        logger.info('Fetching AI news from Google News RSS fallback...')
        feed = feedparser.parse(rss_url)
        entries = feed.get('entries', [])
        logger.info(f'Retrieved {len(entries)} articles from RSS fallback')

        news_items: List[Dict[str, Any]] = []
        for entry in entries[:limit]:
            title = entry.get('title') or 'AI news update'
            summary = entry.get('summary') or entry.get('description') or 'No summary available.'
            briefing = build_briefing_notes(title, summary)

            news_items.append({
                'title': title,
                'summary': clean_text(summary, 220),
                'source': (entry.get('source', {}) or {}).get('title', 'Google News') if isinstance(entry.get('source', {}), dict) else 'Google News',
                'url': entry.get('link', '#'),
                'published': entry.get('published', 'Recent'),
                'why_important': briefing['why_important'],
                'future_change': briefing['future_change'],
                'why_care': briefing['why_care'],
            })

        return news_items
    except Exception as exc:
        logger.error(f'Error fetching RSS AI news: {exc}')
        return []


def search_ai_news(limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch the latest AI news from NewsAPI, with an RSS fallback if the API key is rejected."""
    api_key = get_env_value('NEWSAPI_KEY', 'NEWS_API_KEY')

    if not api_key or api_key.lower() in {'your_newsapi_key_here', 'placeholder'}:
        logger.warning('NEWSAPI_KEY is missing or still a placeholder. Using RSS fallback.')
        return fetch_news_from_rss(limit)

    query = 'artificial intelligence OR machine learning OR generative AI OR ChatGPT OR LLM OR AI policy OR AI safety'
    url = 'https://newsapi.org/v2/everything'
    params = {
        'q': query,
        'sortBy': 'publishedAt',
        'language': 'en',
        'pageSize': limit,
        'apiKey': api_key
    }

    try:
        logger.info('Fetching AI news from NewsAPI...')
        response = requests.get(url, params=params, timeout=15)

        if response.status_code == 401:
            logger.warning('NewsAPI rejected the configured key. Falling back to Google News RSS.')
            return fetch_news_from_rss(limit)

        response.raise_for_status()
        data = response.json()

        if data.get('status') != 'ok':
            logger.error(f'NewsAPI error: {data.get("message", "Unknown error")}')
            return fetch_news_from_rss(limit)

        articles = data.get('articles', [])
        logger.info(f'Retrieved {len(articles)} articles from NewsAPI')

        news_items: List[Dict[str, Any]] = []
        for article in articles[:limit]:
            title = article.get('title') or 'AI news update'
            summary = article.get('description') or article.get('content') or 'No summary available.'
            briefing = build_briefing_notes(title, summary)

            news_items.append({
                'title': title,
                'summary': clean_text(summary, 220),
                'source': article.get('source', {}).get('name', 'Unknown source'),
                'url': article.get('url', '#'),
                'published': article.get('publishedAt', 'Recent'),
                'why_important': briefing['why_important'],
                'future_change': briefing['future_change'],
                'why_care': briefing['why_care'],
            })

        return news_items

    except requests.RequestException as exc:
        logger.error(f'Error fetching AI news: {exc}')
        return fetch_news_from_rss(limit)
    except json.JSONDecodeError as exc:
        logger.error(f'Error parsing NewsAPI response: {exc}')
        return fetch_news_from_rss(limit)


def format_welcome_email(subscriber_email: str) -> str:
    """Generate a welcome email for newly subscribed portal users."""
    today_label = datetime.now().strftime('%A, %B %d, %Y')
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #f4f7ff; color: #1f2937; padding: 24px;">
        <div style="max-width: 680px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 28px; box-shadow: 0 12px 30px rgba(31, 41, 55, 0.08);">
            <div style="background: linear-gradient(135deg, #111827 0%, #2563eb 100%); color: white; padding: 22px; border-radius: 12px; margin-bottom: 18px;">
                <h1 style="margin: 0 0 8px; font-size: 30px;">Welcome to Nova Brief</h1>
                <p style="margin: 0; font-size: 14px; opacity: 0.9;">{today_label}</p>
            </div>

            <p style="font-size: 16px; line-height: 1.7; margin: 0 0 18px;">
                Hello,
            </p>
            <p style="font-size: 16px; line-height: 1.7; margin: 0 0 18px;">
                Thanks for signing up for our AI news brief. You are now subscribed to receive a daily summary of the most important AI, technology, and global business stories.
            </p>
            <div style="background: #eef4ff; border-left: 5px solid #2563eb; border-radius: 10px; padding: 16px; margin: 18px 0; font-size: 14px; line-height: 1.7; color: #334155;">
                <strong>Subscriber email:</strong> {subscriber_email}<br>
                <strong>Delivery:</strong> Daily AI brief in your inbox<br>
                <strong>Next update:</strong> Expect the next digest soon.
            </div>
            <p style="font-size: 16px; line-height: 1.7; margin: 0 0 18px;">
                We’ll keep the briefing short, useful, and easy to scan so you can stay informed without the noise.
            </p>
            <p style="font-size: 16px; line-height: 1.7; margin: 0;">
                Best,<br>
                <strong>Nova Brief Team</strong>
            </p>
        </div>
    </body>
    </html>
    """


def format_news_email(news_items: List[Dict[str, Any]]) -> str:
    """Create the morning briefing email with 5 AI digest items."""
    today_label = datetime.now().strftime('%A, %B %d, %Y')

    if not news_items:
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #f5f7fb; color: #1f2937; padding: 20px;">
            <div style="max-width: 700px; margin: 0 auto; background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.08);">
                <h2 style="margin: 0 0 8px; color: #111827;">AI Morning Brief</h2>
                <p style="margin: 0 0 20px; color: #6b7280;">{today_label}</p>
                <div style="padding: 18px; background: #fff3cd; border-left: 5px solid #f59e0b; border-radius: 8px; color: #7c4a00;">
                    No AI news could be fetched right now. Please check your NewsAPI key and connectivity.
                </div>
            </div>
        </body>
        </html>
        """

    items_html = []
    for index, item in enumerate(news_items, 1):
        items_html.append(
            f"""
            <div style="margin: 18px 0; padding: 18px; background: #f8fafc; border-left: 5px solid #2563eb; border-radius: 8px;">
                <div style="font-size: 15px; font-weight: 700; color: #111827; margin-bottom: 8px;">{index}. {item['title']}</div>
                <div style="font-size: 12px; color: #64748b; margin-bottom: 10px;">{item['source']} • {item['published']}</div>
                <div style="font-size: 14px; color: #334155; margin-bottom: 12px;">
                    <strong>Summary:</strong> {item['summary']}
                </div>
                <div style="font-size: 13px; color: #334155; margin-bottom: 8px;">
                    <strong>Why it matters:</strong> {item['why_important']}
                </div>
                <div style="font-size: 13px; color: #334155; margin-bottom: 8px;">
                    <strong>What could change:</strong> {item['future_change']}
                </div>
                <div style="font-size: 13px; color: #334155; margin-bottom: 8px;">
                    <strong>Why you should care:</strong> {item['why_care']}
                </div>
                <a href="{item['url']}" style="color: #2563eb; text-decoration: none; font-size: 12px; font-weight: 600;">Read the article →</a>
            </div>
            """
        )

    items_block = '\n'.join(items_html)
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #eef4ff; color: #1f2937; padding: 20px;">
        <div style="max-width: 760px; margin: 0 auto; background: #ffffff; border-radius: 14px; padding: 24px; box-shadow: 0 12px 28px rgba(27, 56, 97, 0.10);">
            <div style="background: linear-gradient(135deg, #111827 0%, #2563eb 100%); color: white; padding: 22px; border-radius: 10px; margin-bottom: 18px;">
                <h1 style="margin: 0 0 6px; font-size: 30px;">AI Morning Brief</h1>
                <p style="margin: 0; font-size: 14px; opacity: 0.9;">{today_label}</p>
            </div>
            <div style="font-size: 14px; color: #475569; margin-bottom: 20px; line-height: 1.6;">
                Here are 5 AI developments to pay attention to this morning. Each one is brief, important, and tied to what it could mean for the future or daily life.
            </div>
            {items_block}
            <div style="margin-top: 22px; padding-top: 18px; border-top: 1px solid #e5e7eb; font-size: 13px; color: #475569; line-height: 1.6;">
                <strong>Big picture:</strong> AI is increasingly moving from novelty to infrastructure, so the most important stories are the ones that reshape trust, work, and everyday decisions.
            </div>
        </div>
    </body>
    </html>
    """
    return html


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    from_email = get_env_value('GMAIL_USER', 'EMAIL_USER')
    password = get_env_value('GMAIL_APP_PASSWORD', 'EMAIL_APP_PASSWORD')

    if not from_email or not password:
        logger.error('Gmail credentials missing. Add GMAIL_USER and GMAIL_APP_PASSWORD or EMAIL_USER and EMAIL_APP_PASSWORD to .env.')
        return False

    message = MIMEMultipart('alternative')
    message['Subject'] = subject
    message['From'] = from_email
    message['To'] = to_email

    message.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(from_email, password)
            server.send_message(message)
        logger.info(f'Email sent successfully to {to_email}')
        return True
    except Exception as exc:  # pragma: no cover - runtime mail failure
        logger.error(f'Failed to send email: {exc}')
        return False


def send_welcome_email(to_email: str) -> bool:
    """Send a welcome email to a newly registered portal subscriber."""
    subject = 'Welcome to Nova Brief'
    html_content = format_welcome_email(to_email)
    return send_email(to_email, subject, html_content)


def send_contact_notification_email(name: str, email: str, subject: str, message: str) -> bool:
    """Send an admin notification email when a contact form is submitted."""
    admin_email = get_env_value('ADMIN_EMAIL', 'GMAIL_USER', 'EMAIL_USER')
    if not admin_email:
        logger.warning('No admin email configured for contact notifications.')
        return False

    today_label = datetime.now().strftime('%A, %B %d, %Y %H:%M')
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #f4f7ff; color: #1f2937; padding: 24px;">
        <div style="max-width: 680px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 28px; box-shadow: 0 12px 30px rgba(31,41,55,0.08);">
            <div style="background: linear-gradient(135deg, #111827 0%, #2563eb 100%); color: white; padding: 18px 22px; border-radius: 12px; margin-bottom: 18px;">
                <h2 style="margin:0 0 4px;">Nova Brief — Contact Form</h2>
                <p style="margin:0; font-size:13px; opacity:0.85;">{today_label}</p>
            </div>
            <table style="width:100%; border-collapse:collapse; font-size:15px;">
                <tr><td style="padding:8px 0; color:#64748b; width:110px;">From</td><td style="font-weight:600;">{name}</td></tr>
                <tr><td style="padding:8px 0; color:#64748b;">Email</td><td><a href="mailto:{email}" style="color:#2563eb;">{email}</a></td></tr>
                <tr><td style="padding:8px 0; color:#64748b;">Subject</td><td style="font-weight:600;">{subject}</td></tr>
            </table>
            <div style="background:#f8fafc; border-left:4px solid #2563eb; border-radius:8px; padding:16px; margin-top:18px; font-size:14px; line-height:1.7; color:#334155;">
                {message}
            </div>
        </div>
    </body>
    </html>
    """
    return send_email(admin_email, f'[Nova Brief Contact] {subject}', html_content)


def get_recipients() -> List[str]:
    """Get list of recipient emails from registered users database and recipients.json"""
    db = NewsDatabase()

    # Get all registered users from database
    registered_users = db.get_all_active_users()

    # Also get recipients from recipients.json for backward compatibility
    try:
        with open('recipients.json', 'r') as f:
            data = json.load(f)
            json_recipients = data.get('recipients', [])
    except (FileNotFoundError, json.JSONDecodeError):
        json_recipients = []

    # Combine both sources and remove duplicates
    all_recipients = list(set(registered_users + json_recipients))

    # Fallback to .env if no recipients found
    if not all_recipients:
        default_email = get_env_value('RECIPIENT_EMAIL', 'GMAIL_USER', 'EMAIL_USER')
        if default_email:
            all_recipients = [default_email]

    return all_recipients


def run_news_digest() -> bool:
    logger.info('=' * 60)
    logger.info('Starting AI morning briefing workflow...')
    logger.info('=' * 60)

    db = NewsDatabase()
    today_key = datetime.now().strftime('%Y-%m-%d')

    if db.has_daily_digest_run(today_key):
        logger.info(f'Digest already sent for {today_key}. Skipping duplicate daily send.')
        db.log_agent_event('digest_skipped', f'Digest already sent for {today_key}; duplicate send prevented.')
        return False

    db.log_agent_event('digest_start', 'Starting news digest workflow')

    recipients = get_recipients()
    if not recipients:
        logger.error('No recipients configured. Add emails to recipients.json or RECIPIENT_EMAIL to .env.')
        db.log_agent_event('error', 'No recipient emails configured')
        return False

    logger.info(f'Sending to {len(recipients)} recipient(s): {", ".join(recipients)}')

    news_items = search_ai_news(limit=5)

    if news_items:
        db.save_news_batch(news_items)
        logger.info(f'Saved {len(news_items)} articles to database')

    html_content = format_news_email(news_items)
    subject = f'AI Morning Brief - {datetime.now().strftime("%B %d, %Y")}'

    success_count = 0
    failed_recipients = []

    for to_email in recipients:
        success = send_email(to_email, subject, html_content)
        if success:
            success_count += 1
            db.log_email_sent(to_email, subject, len(news_items), 'success')
            db.update_user_email_sent(to_email)
        else:
            failed_recipients.append(to_email)
            db.log_email_sent(to_email, subject, len(news_items), 'failed', 'Email sending failed')

    db.record_daily_digest_run(len(recipients), success_count, len(news_items), 'success' if success_count > 0 else 'failed')

    if success_count > 0:
        logger.info(f'Sent digest with {len(news_items)} AI stories to {success_count}/{len(recipients)} recipients.')
        db.log_agent_event('email_sent', f'Successfully sent {len(news_items)} articles to {success_count} recipient(s)')
        if failed_recipients:
            logger.warning(f'Failed to send to: {", ".join(failed_recipients)}')
            db.log_agent_event('error', f'Failed to send to {len(failed_recipients)} recipient(s)')
    else:
        logger.warning('Digest was not sent to any recipients.')
        db.log_agent_event('error', 'Failed to send email to all recipients')

    deleted = db.cleanup_old_articles(months=3)
    if deleted > 0:
        logger.info(f'Cleaned up {deleted} articles older than 3 months')

    logger.info('=' * 60)
    return success_count > 0


def start_scheduler() -> bool:
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        logger.error('APScheduler is not installed. Run: pip install -r requirements.txt')
        return False

    scheduler = BackgroundScheduler()
    scheduler.add_job(run_news_digest, 'cron', hour=8, minute=0, id='ai_morning_brief')
    logger.info('Scheduler started. AI brief will be sent daily at 8:00 AM.')
    scheduler.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        logger.info('Scheduler shutting down...')
        scheduler.shutdown()
        sys.exit(0)

    return True


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description='AI Morning Brief Agent')
    parser.add_argument('--run-now', action='store_true', help='Send the AI morning brief immediately')
    parser.add_argument('--schedule', action='store_true', help='Start the daily 8:00 AM scheduler')
    parser.add_argument('--test-email', action='store_true', help='Send a test email')
    parser.add_argument('--preview', action='store_true', help='Print the 5-item briefing in the terminal without sending email')
    args = parser.parse_args()

    if args.preview:
        items = search_ai_news(limit=5)
        if not items:
            logger.warning('No news items were returned. Check the NewsAPI key and internet connection.')
            return
        for i, item in enumerate(items, 1):
            print(f"\n{i}. {item['title']}")
            print(f"Summary: {item['summary']}")
            print(f"Why it matters: {item['why_important']}")
            print(f"What could change: {item['future_change']}")
            print(f"Why you should care: {item['why_care']}")
        return

    if args.run_now:
        run_news_digest()
        return

    if args.test_email:
        to_email = get_env_value('RECIPIENT_EMAIL', 'GMAIL_USER', 'EMAIL_USER')
        if not to_email:
            logger.error('RECIPIENT_EMAIL is not configured.')
            return
        test_html = """
        <html><body style="font-family: Arial; padding: 20px;">
        <h2>✅ AI Morning Brief Test Email</h2>
        <p>This confirms your agent is configured and ready to send the daily AI briefing.</p>
        <p><strong>Status:</strong> The email pipeline is working.</p>
        <p>The morning digest is scheduled for 8:00 AM daily.</p>
        </body></html>
        """
        send_email(to_email, 'AI Morning Brief - Test Email', test_html)
        return

    if args.schedule:
        start_scheduler()
        return

    logger.info('Running AI morning brief once without scheduling...')
    run_news_digest()


if __name__ == '__main__':
    main()