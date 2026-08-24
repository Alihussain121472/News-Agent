import os, sys, json, logging, smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any

import requests, feedparser
from dotenv import load_dotenv
from database import NewsDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('ai_news_agent.log', encoding='utf-8'), logging.StreamHandler()])
logger = logging.getLogger(__name__)
load_dotenv()


def get_env_value(*names: str) -> str:
    for n in names:
        v = os.getenv(n)
        if v and v.strip(): return v.strip()
    return ""


def clean_text(value: str, max_length: int = 220) -> str:
    text = (value or '').replace('\n', ' ').strip()
    if len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0] + '...'
    return text


def build_briefing_notes(title: str, summary: str) -> Dict[str, str]:
    tl = (title or '').lower(); sl = (summary or '').lower()
    if any(w in tl for w in ['security','privacy','deepfake','misinformation','risk','attack','vulnerability']):
        wi = 'This raises a real safety or trust issue that could affect how people use AI in everyday life.'
    elif any(w in tl for w in ['regulation','policy','government','law','europe','ai act']):
        wi = 'This could change the rules around AI adoption, accountability, and how businesses operate.'
    elif any(w in tl for w in ['openai','google','meta','microsoft','anthropic','gemini','chatgpt']):
        wi = 'A major company action often signals where the market and consumer behavior are shifting next.'
    elif any(w in tl for w in ['health','medical','drug','science','research']):
        wi = 'This could affect healthcare, research speed, and the quality of decisions in critical areas.'
    else:
        wi = 'This matters because it shows how quickly AI is moving from experiment to real-world influence.'

    if any(w in tl for w in ['job','work','labor','productivity','automation','assistant']):
        fc = 'It could change how work gets done, which tasks are automated, and where human value still matters most.'
    elif any(w in tl for w in ['education','student','school','learning','teacher']):
        fc = 'It could reshape learning, teaching, and how people build skills in the next few years.'
    elif any(w in tl for w in ['security','privacy','deepfake','fraud']):
        fc = 'It could make digital trust harder to maintain unless safeguards and public awareness improve quickly.'
    elif any(w in tl for w in ['energy','chip','compute','data center','infrastructure']):
        fc = 'It could alter how companies invest in hardware, power, and digital infrastructure around AI.'
    else:
        fc = 'It could influence consumer habits, business decisions, and the speed at which AI becomes part of daily life.'

    if any(w in sl for w in ['risk','danger','harm','attack','fraud','misinformation','bias']):
        wc = 'Because the downside is not theoretical; it can affect trust, safety, and the decisions people make online.'
    elif any(w in tl for w in ['chip','model','cost','latency','compute']):
        wc = 'Because this often signals the next wave of AI adoption, pricing pressure, and accessibility for everyone.'
    elif any(w in tl for w in ['regulation','policy','law']):
        wc = 'Because rules shape what AI can do, how fast it spreads, and how much control people retain.'
    else:
        wc = 'Because what looks like a niche update today can become a normal part of life faster than expected.'

    return {'why_important': wi, 'future_change': fc, 'why_care': wc}


def fetch_news_from_rss(limit: int = 5) -> List[Dict[str, Any]]:
    rss_url = 'https://news.google.com/rss/search?q=artificial+intelligence+OR+machine+learning+OR+generative+AI+OR+LLM+OR+AI+policy+OR+AI+safety&hl=en-US&gl=US&ceid=US:en'
    try:
        feed = feedparser.parse(rss_url); entries = feed.get('entries', [])
        items = []
        for entry in entries[:limit]:
            title = entry.get('title') or 'AI news update'
            summary = entry.get('summary') or entry.get('description') or 'No summary available.'
            b = build_briefing_notes(title, summary)
            items.append({'title': title, 'summary': clean_text(summary, 220),
                'source': (entry.get('source') or {}).get('title', 'Google News') if isinstance(entry.get('source'), dict) else 'Google News',
                'url': entry.get('link', '#'), 'published': entry.get('published', 'Recent'), **b})
        return items
    except Exception as e:
        logger.error(f'RSS error: {e}'); return []


def search_ai_news(limit: int = 5) -> List[Dict[str, Any]]:
    api_key = get_env_value('NEWSAPI_KEY', 'NEWS_API_KEY')
    if not api_key or api_key.lower() in {'your_newsapi_key_here', 'placeholder'}:
        return fetch_news_from_rss(limit)
    try:
        resp = requests.get('https://newsapi.org/v2/everything', params={
            'q': 'artificial intelligence OR machine learning OR generative AI OR ChatGPT OR LLM OR AI policy OR AI safety',
            'sortBy': 'publishedAt', 'language': 'en', 'pageSize': limit, 'apiKey': api_key}, timeout=15)
        if resp.status_code == 401: return fetch_news_from_rss(limit)
        resp.raise_for_status(); data = resp.json()
        if data.get('status') != 'ok': return fetch_news_from_rss(limit)
        items = []
        for a in data.get('articles', [])[:limit]:
            title = a.get('title') or 'AI news update'
            summary = a.get('description') or a.get('content') or 'No summary available.'
            b = build_briefing_notes(title, summary)
            items.append({'title': title, 'summary': clean_text(summary, 220),
                'source': a.get('source', {}).get('name', 'Unknown'), 'url': a.get('url', '#'),
                'published': a.get('publishedAt', 'Recent'), **b})
        return items
    except Exception:
        return fetch_news_from_rss(limit)


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    from_email = get_env_value('GMAIL_USER', 'EMAIL_USER')
    password = get_env_value('GMAIL_APP_PASSWORD', 'EMAIL_APP_PASSWORD')
    if not from_email or not password:
        logger.error('Gmail credentials missing.'); return False
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject; msg['From'] = from_email; msg['To'] = to_email
    msg.attach(MIMEText(html_content, 'html'))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(from_email, password); s.send_message(msg)
        logger.info(f'Email sent to {to_email}'); return True
    except Exception as e:
        logger.error(f'Email failed: {e}'); return False


def format_welcome_email(subscriber_email: str) -> str:
    today = datetime.now().strftime('%A, %B %d, %Y')
    return f"""<html><body style="font-family:Arial,sans-serif;background:#f4f7ff;color:#1f2937;padding:24px;">
<div style="max-width:680px;margin:0 auto;background:#fff;border-radius:16px;padding:28px;box-shadow:0 12px 30px rgba(31,41,55,.08);">
  <div style="background:linear-gradient(135deg,#111827,#2563eb);color:#fff;padding:22px;border-radius:12px;margin-bottom:18px;">
    <h1 style="margin:0 0 8px;font-size:28px;">Welcome to Nova Brief</h1>
    <p style="margin:0;font-size:13px;opacity:.9;">{today}</p>
  </div>
  <p style="font-size:16px;line-height:1.7;">Hello,</p>
  <p style="font-size:16px;line-height:1.7;">You are now subscribed to receive daily AI news <strong>and</strong> early alerts about student programs from Google, Microsoft, Amazon, NASA and more â€” including direct registration links.</p>
  <div style="background:#eef4ff;border-left:5px solid #2563eb;border-radius:10px;padding:16px;margin:18px 0;font-size:14px;line-height:1.7;color:#334155;">
    <strong>Email:</strong> {subscriber_email}<br>
    <strong>Daily AI Brief:</strong> Every morning at 8 AM<br>
    <strong>Program Alerts:</strong> Sent before programs launch so you can prepare
  </div>
  <p style="font-size:16px;line-height:1.7;margin:0;">Best,<br><strong>Nova Brief Team</strong></p>
</div></body></html>"""


def format_news_email(news_items: List[Dict[str, Any]]) -> str:
    today = datetime.now().strftime('%A, %B %d, %Y')
    if not news_items:
        return f"""<html><body style="font-family:Arial,sans-serif;background:#f5f7fb;padding:20px;">
<div style="max-width:700px;margin:0 auto;background:#fff;border-radius:12px;padding:24px;">
  <h2>AI Morning Brief â€” {today}</h2>
  <div style="padding:18px;background:#fff3cd;border-left:5px solid #f59e0b;border-radius:8px;color:#7c4a00;">
    No AI news could be fetched right now.
  </div></div></body></html>"""

    items_html = ''.join(f"""
    <div style="margin:18px 0;padding:18px;background:#f8fafc;border-left:5px solid #2563eb;border-radius:8px;">
      <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:8px;">{i}. {item['title']}</div>
      <div style="font-size:12px;color:#64748b;margin-bottom:10px;">{item['source']} â€¢ {item['published']}</div>
      <div style="font-size:14px;color:#334155;margin-bottom:8px;"><strong>Summary:</strong> {item['summary']}</div>
      <div style="font-size:13px;color:#334155;margin-bottom:6px;"><strong>Why it matters:</strong> {item['why_important']}</div>
      <div style="font-size:13px;color:#334155;margin-bottom:6px;"><strong>What could change:</strong> {item['future_change']}</div>
      <div style="font-size:13px;color:#334155;margin-bottom:8px;"><strong>Why you should care:</strong> {item['why_care']}</div>
      <a href="{item['url']}" style="color:#2563eb;font-size:12px;font-weight:600;text-decoration:none;">Read article â†’</a>
    </div>""" for i, item in enumerate(news_items, 1))

    return f"""<html><body style="font-family:Arial,sans-serif;background:#eef4ff;color:#1f2937;padding:20px;">
<div style="max-width:760px;margin:0 auto;background:#fff;border-radius:14px;padding:24px;box-shadow:0 12px 28px rgba(27,56,97,.10);">
  <div style="background:linear-gradient(135deg,#111827,#2563eb);color:#fff;padding:22px;border-radius:10px;margin-bottom:18px;">
    <h1 style="margin:0 0 6px;font-size:28px;">AI Morning Brief</h1>
    <p style="margin:0;font-size:14px;opacity:.9;">{today}</p>
  </div>
  <div style="font-size:14px;color:#475569;margin-bottom:20px;line-height:1.6;">
    Here are today's most important AI developments â€” each one brief, important, and tied to what it could mean for the future.
  </div>
  {items_html}
  <div style="margin-top:22px;padding-top:18px;border-top:1px solid #e5e7eb;font-size:13px;color:#475569;">
    <strong>Big picture:</strong> AI is increasingly moving from novelty to infrastructure. Stay informed. Stay ahead.
  </div>
</div></body></html>"""


def format_program_email(program: Dict[str, Any]) -> str:
    """Format student program notification email with direct registration link."""
    today = datetime.now().strftime('%A, %B %d, %Y')
    deadline_text = f"<strong>Deadline:</strong> {program.get('deadline', 'Check website')}<br>" if program.get('deadline') else ''
    launch_text = f"<strong>Launch Date:</strong> {program.get('launch_date', 'Soon')}<br>" if program.get('launch_date') else ''

    return f"""<html><body style="font-family:Arial,sans-serif;background:#f0fdf4;color:#1f2937;padding:24px;">
<div style="max-width:680px;margin:0 auto;background:#fff;border-radius:16px;padding:28px;box-shadow:0 12px 30px rgba(0,0,0,.08);">
  <div style="background:linear-gradient(135deg,#065f46,#10b981);color:#fff;padding:22px;border-radius:12px;margin-bottom:18px;">
    <div style="font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;opacity:.85;margin-bottom:6px;">ðŸŽ“ Student Program Alert</div>
    <h1 style="margin:0 0 8px;font-size:26px;">{program.get('title', 'New Program')}</h1>
    <p style="margin:0;font-size:14px;opacity:.9;">by <strong>{program.get('company', 'Company')}</strong> â€¢ {today}</p>
  </div>
  <p style="font-size:16px;line-height:1.7;margin:0 0 16px;">A new opportunity has opened for students. Here's everything you need to know:</p>
  <div style="background:#f0fdf4;border-left:5px solid #10b981;border-radius:10px;padding:16px;margin:0 0 20px;font-size:14px;line-height:1.8;color:#134e4a;">
    {deadline_text}
    {launch_text}
    <strong>Category:</strong> {program.get('category', 'Program').title()}<br>
    <strong>Offered by:</strong> {program.get('company', 'Company')}
  </div>
  <p style="font-size:15px;line-height:1.7;color:#334155;">{program.get('description', 'Check the registration link for full details.')}</p>
  <div style="text-align:center;margin:28px 0;">
    <a href="{program.get('registration_url', '#')}"
       style="display:inline-block;background:linear-gradient(135deg,#065f46,#10b981);color:#fff;
              padding:16px 36px;border-radius:12px;font-size:16px;font-weight:700;text-decoration:none;
              box-shadow:0 8px 20px rgba(16,185,129,.35);">
      ðŸš€ Register Now â†’
    </a>
  </div>
  <p style="font-size:13px;color:#6b7280;text-align:center;margin-top:20px;">
    You receive these alerts because you are subscribed to Nova Brief.<br>
    This email was sent to you before the program launches so you have time to prepare.
  </p>
</div></body></html>"""


def send_welcome_email(to_email: str) -> bool:
    return send_email(to_email, 'Welcome to Nova Brief â€” Daily AI & Student Program Alerts', format_welcome_email(to_email))

def format_login_email(subscriber_email: str) -> str:
    now = datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')
    return f"\"<html><body style="font-family:Arial,sans-serif;background:#f4f7ff;color:#1f2937;padding:24px;">
<div style="max-width:680px;margin:0 auto;background:#fff;border-radius:16px;padding:28px;box-shadow:0 12px 30px rgba(31,41,55,.08);">
  <div style="background:linear-gradient(135deg,#111827,#2563eb);color:#fff;padding:22px;border-radius:12px;margin-bottom:18px;">
    <h1 style="margin:0 0 8px;font-size:24px;">New Login Alert</h1>
  </div>
  <p style="font-size:16px;line-height:1.7;">Hello,</p>
  <p style="font-size:16px;line-height:1.7;">We noticed a new login to your Nova Brief account.</p>
  <div style="background:#eef4ff;border-left:5px solid #2563eb;border-radius:10px;padding:16px;margin:18px 0;font-size:14px;line-height:1.7;color:#334155;">
    <strong>Account:</strong> {subscriber_email}<br>
    <strong>Time:</strong> {now}
  </div>
  <p style="font-size:14px;color:#6b7280;">If this was you, you can safely ignore this email. If you did not log in, please reset your password immediately.</p>
</div></body></html>"\"

def send_login_email(to_email: str) -> bool:
    return send_email(to_email, 'Security Alert: New login to Nova Brief', format_login_email(to_email))


def send_contact_notification_email(name: str, email: str, subject: str, message: str) -> bool:
    admin_email = get_env_value('ADMIN_EMAIL', 'GMAIL_USER', 'EMAIL_USER')
    if not admin_email: return False
    today = datetime.now().strftime('%A, %B %d, %Y %H:%M')
    html = f"""<html><body style="font-family:Arial,sans-serif;background:#f4f7ff;padding:24px;">
<div style="max-width:680px;margin:0 auto;background:#fff;border-radius:16px;padding:28px;">
  <div style="background:linear-gradient(135deg,#111827,#2563eb);color:#fff;padding:18px 22px;border-radius:12px;margin-bottom:18px;">
    <h2 style="margin:0 0 4px;">Nova Brief â€” Contact Form</h2><p style="margin:0;font-size:13px;opacity:.85;">{today}</p>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:15px;">
    <tr><td style="padding:8px 0;color:#64748b;width:110px;">From</td><td style="font-weight:600;">{name}</td></tr>
    <tr><td style="padding:8px 0;color:#64748b;">Email</td><td><a href="mailto:{email}" style="color:#2563eb;">{email}</a></td></tr>
    <tr><td style="padding:8px 0;color:#64748b;">Subject</td><td style="font-weight:600;">{subject}</td></tr>
  </table>
  <div style="background:#f8fafc;border-left:4px solid #2563eb;border-radius:8px;padding:16px;margin-top:18px;font-size:14px;line-height:1.7;color:#334155;">{message}</div>
</div></body></html>"""
    return send_email(admin_email, f'[Nova Brief Contact] {subject}', html)


def send_program_notifications() -> int:
    """Check for programs that need notifications and send them to all subscribers."""
    db = NewsDatabase()
    programs = db.get_programs_to_notify()
    if not programs:
        logger.info('No programs to notify about today.'); return 0

    subscribers = db.get_program_subscribers()
    if not subscribers:
        logger.info('No program subscribers found.'); return 0

    sent_count = 0
    for program in programs:
        subject = f"ðŸŽ“ New Program Alert: {program['title']} by {program['company']}"
        html = format_program_email(program)
        for email in subscribers:
            if send_email(email, subject, html):
                sent_count += 1
                db.log_user_activity(email, 'program_notification_sent', program['title'])
        db.mark_program_notified(program['id'])
        logger.info(f"Notified {len(subscribers)} users about: {program['title']}")

    return sent_count


def get_recipients() -> List[str]:
    db = NewsDatabase()
    registered_users = db.get_all_active_users()
    try:
        with open('recipients.json', 'r') as f:
            json_recipients = json.load(f).get('recipients', [])
    except (FileNotFoundError, json.JSONDecodeError):
        json_recipients = []
    all_recipients = list(set(registered_users + json_recipients))
    if not all_recipients:
        default = get_env_value('RECIPIENT_EMAIL', 'GMAIL_USER', 'EMAIL_USER')
        if default: all_recipients = [default]
    return all_recipients


def run_news_digest() -> bool:
    logger.info('=' * 60)
    logger.info('Starting AI morning briefing...')
    db = NewsDatabase()
    today_key = datetime.now().strftime('%Y-%m-%d')

    if db.has_daily_digest_run(today_key):
        logger.info(f'Digest already sent for {today_key}. Skipping.')
        return False

    db.log_agent_event('digest_start', 'Starting news digest workflow')
    recipients = get_recipients()
    if not recipients:
        db.log_agent_event('error', 'No recipient emails configured'); return False

    news_items = search_ai_news(limit=5)
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
            db.log_email_sent(to_email, subject, len(news_items), 'failed', 'Email sending failed')

    db.record_daily_digest_run(len(recipients), success_count, len(news_items),
                                'success' if success_count > 0 else 'failed')

    # Also check and send program notifications
    try:
        program_emails_sent = send_program_notifications()
        if program_emails_sent > 0:
            db.log_agent_event('program_notifications', f'Sent {program_emails_sent} program notification emails')
    except Exception as e:
        logger.error(f'Program notification error: {e}')

    db.cleanup_old_articles(months=3)
    db.log_agent_event('email_sent', f'Sent to {success_count}/{len(recipients)} recipients')
    logger.info('=' * 60)
    return success_count > 0


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description='Nova Brief Agent')
    parser.add_argument('--run-now', action='store_true')
    parser.add_argument('--schedule', action='store_true')
    parser.add_argument('--test-email', action='store_true')
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--check-programs', action='store_true')
    args = parser.parse_args()

    if args.preview:
        items = search_ai_news(limit=5)
        for i, item in enumerate(items, 1):
            print(f"\n{i}. {item['title']}\nSummary: {item['summary']}")
        return

    if args.check_programs:
        sent = send_program_notifications()
        print(f'Sent {sent} program notification emails.')
        return

    if args.run_now:
        run_news_digest(); return

    if args.test_email:
        to = get_env_value('RECIPIENT_EMAIL', 'GMAIL_USER', 'EMAIL_USER')
        if to:
            send_email(to, 'Nova Brief - Test Email', '<html><body><h2>âœ… Test Email</h2><p>Your Nova Brief agent is working correctly.</p></body></html>')
        return

    if args.schedule:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            scheduler = BackgroundScheduler()
            scheduler.add_job(run_news_digest, 'cron', hour=8, minute=0, id='ai_morning_brief')
            scheduler.add_job(send_program_notifications, 'cron', hour=9, minute=0, id='program_notifications')
            scheduler.start()
            logger.info('Scheduler started. Daily brief at 8:00 AM, program checks at 9:00 AM.')
            try:
                while True: pass
            except KeyboardInterrupt:
                scheduler.shutdown(); sys.exit(0)
        except ImportError:
            logger.error('APScheduler not installed.')
        return

    run_news_digest()


if __name__ == '__main__':
    main()

