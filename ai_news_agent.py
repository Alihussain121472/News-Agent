import os, sys, json, logging, smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any

import requests, feedparser
from dotenv import load_dotenv
from database import NewsDatabase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
load_dotenv()


def get_env_value(*names: str) -> str:
    for n in names:
        v = os.getenv(n)
        if v and v.strip():
            return v.strip()
    return ""


def clean_text(value: str, max_length: int = 220) -> str:
    text = (value or '').replace('\n', ' ').strip()
    if len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0] + '...'
    return text


def build_briefing_notes(title: str, summary: str) -> Dict[str, str]:
    tl = (title or '').lower()
    sl = (summary or '').lower()
    if any(w in tl for w in ['security', 'privacy', 'deepfake', 'misinformation', 'risk', 'attack', 'vulnerability']):
        wi = 'This raises a real safety or trust issue that could affect how people use AI in everyday life.'
    elif any(w in tl for w in ['regulation', 'policy', 'government', 'law', 'europe', 'ai act']):
        wi = 'This could change the rules around AI adoption, accountability, and how businesses operate.'
    elif any(w in tl for w in ['openai', 'google', 'meta', 'microsoft', 'anthropic', 'gemini', 'chatgpt']):
        wi = 'A major company action often signals where the market and consumer behavior are shifting next.'
    elif any(w in tl for w in ['health', 'medical', 'drug', 'science', 'research']):
        wi = 'This could affect healthcare, research speed, and the quality of decisions in critical areas.'
    else:
        wi = 'This matters because it shows how quickly AI is moving from experiment to real-world influence.'

    if any(w in tl for w in ['job', 'work', 'labor', 'productivity', 'automation', 'assistant']):
        fc = 'It could change how work gets done, which tasks are automated, and where human value still matters most.'
    elif any(w in tl for w in ['education', 'student', 'school', 'learning', 'teacher']):
        fc = 'It could reshape learning, teaching, and how people build skills in the next few years.'
    elif any(w in tl for w in ['security', 'privacy', 'deepfake', 'fraud']):
        fc = 'It could make digital trust harder to maintain unless safeguards and public awareness improve quickly.'
    elif any(w in tl for w in ['energy', 'chip', 'compute', 'data center', 'infrastructure']):
        fc = 'It could alter how companies invest in hardware, power, and digital infrastructure around AI.'
    else:
        fc = 'It could influence consumer habits, business decisions, and the speed at which AI becomes part of daily life.'

    if any(w in sl for w in ['risk', 'danger', 'harm', 'attack', 'fraud', 'misinformation', 'bias']):
        wc = 'Because the downside is not theoretical; it can affect trust, safety, and the decisions people make online.'
    elif any(w in tl for w in ['chip', 'model', 'cost', 'latency', 'compute']):
        wc = 'Because this often signals the next wave of AI adoption, pricing pressure, and accessibility for everyone.'
    elif any(w in tl for w in ['regulation', 'policy', 'law']):
        wc = 'Because rules shape what AI can do, how fast it spreads, and how much control people retain.'
    else:
        wc = 'Because what looks like a niche update today can become a normal part of life faster than expected.'

    return {'why_important': wi, 'future_change': fc, 'why_care': wc}


# Fetch latest AI news articles from Google News RSS feed as a backup source.
def fetch_news_from_rss(limit: int = 5) -> List[Dict[str, Any]]:
    rss_url = 'https://news.google.com/rss/search?q=artificial+intelligence+OR+machine+learning+OR+generative+AI+OR+LLM+OR+AI+policy+OR+AI+safety&hl=en-US&gl=US&ceid=US:en'
    try:
        feed = feedparser.parse(rss_url)
        entries = feed.get('entries', [])
        items = []
        for entry in entries[:limit]:
            title = entry.get('title') or 'AI news update'
            summary = entry.get('summary') or entry.get('description') or 'No summary available.'
            b = build_briefing_notes(title, summary)
            items.append({
                'title': title,
                'summary': clean_text(summary, 220),
                'source': (entry.get('source') or {}).get('title', 'Google News') if isinstance(entry.get('source'), dict) else 'Google News',
                'url': entry.get('link', '#'),
                'published': entry.get('published', 'Recent'),
                **b
            })
        return items
    except Exception as e:
        logger.error(f'RSS error: {e}')
        return []


# Search for AI news using NewsAPI. If it fails, fallback to RSS feed.
def search_ai_news(limit: int = 5) -> List[Dict[str, Any]]:
    api_key = get_env_value('NEWSAPI_KEY', 'NEWS_API_KEY')
    if not api_key or api_key.lower() in {'your_newsapi_key_here', 'placeholder'}:
        return fetch_news_from_rss(limit)
    try:
        resp = requests.get('https://newsapi.org/v2/everything', params={
            'q': 'artificial intelligence OR machine learning OR generative AI OR ChatGPT OR LLM OR AI policy OR AI safety',
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': limit,
            'apiKey': api_key
        }, timeout=15)
        if resp.status_code == 401:
            return fetch_news_from_rss(limit)
        resp.raise_for_status()
        data = resp.json()
        if data.get('status') != 'ok':
            return fetch_news_from_rss(limit)
        items = []
        for a in data.get('articles', [])[:limit]:
            title = a.get('title') or 'AI news update'
            summary = a.get('description') or a.get('content') or 'No summary available.'
            b = build_briefing_notes(title, summary)
            items.append({
                'title': title,
                'summary': clean_text(summary, 220),
                'source': a.get('source', {}).get('name', 'Unknown'),
                'url': a.get('url', '#'),
                'published': a.get('publishedAt', 'Recent'),
                **b
            })
        return items
    except Exception:
        return fetch_news_from_rss(limit)


import concurrent.futures

EMAIL_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='email_worker')


# A high-speed function to send emails using Gmail SMTP (Port 587 STARTTLS primary, Port 465 SSL fallback).
def send_email(to_email: str, subject: str, html_content: str) -> bool:
    from_email = get_env_value('GMAIL_USER', 'EMAIL_USER')
    password = get_env_value('GMAIL_APP_PASSWORD', 'EMAIL_APP_PASSWORD', 'EMAIL_PASS')
    if not from_email or not password:
        logger.error('Gmail credentials missing in environment.')
        return False

    clean_pwd = password.replace(' ', '').replace('-', '').strip()
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"Nova Brief <{from_email}>"
    msg['To'] = to_email
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    # Try Port 465 SSL first (implicit SSL has lower latency and is less likely to be blocked)
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=5) as s:
            s.login(from_email, clean_pwd)
            s.send_message(msg)
        logger.info(f'Email delivered instantly to {to_email} via SSL (port 465)')
        return True
    except Exception as e1:
        logger.warning(f'SSL 465 failed ({e1}), falling back to STARTTLS port 587...')
        try:
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=5) as s:
                s.ehlo()
                s.starttls()
                s.ehlo()
                s.login(from_email, clean_pwd)
                s.send_message(msg)
            logger.info(f'Email delivered to {to_email} via STARTTLS (port 587)')
            return True
        except Exception as e2:
            logger.error(f'Email delivery failed to {to_email}: SSL: {e1} | TLS: {e2}')
            return False


def dispatch_email_async(to_email: str, subject: str, html_content: str):
    """Submits email send task to the dedicated worker pool for 0ms web latency."""
    return EMAIL_EXECUTOR.submit(send_email, to_email, subject, html_content)


def format_welcome_email(subscriber_email: str, name: str = None) -> str:
    today = datetime.now().strftime('%A, %B %d, %Y')
    greeting = f"Hello {name}," if name else "Hello,"
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background-color:#f6f9fc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#333333;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f6f9fc;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="100%" style="max-width:600px;background-color:#ffffff;border:1px solid #e6ebf1;border-radius:8px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.05);">
          <tr>
            <td style="padding:40px;text-align:left;">
              <h1 style="margin:0 0 16px 0;font-size:24px;font-weight:600;color:#111827;">Welcome to Nova Brief</h1>
              <p style="margin:0 0 24px 0;font-size:16px;color:#4b5563;line-height:1.6;">{greeting}<br><br>Your account has been successfully verified and activated. You are now subscribed to receive our enterprise-grade daily AI intelligence briefings and elite student program alerts.</p>
              
              <div style="background-color:#f3f4f6;border-radius:6px;padding:24px;margin-bottom:24px;">
                <h2 style="margin:0 0 16px 0;font-size:14px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.05em;">What to Expect</h2>
                <div style="margin-bottom:16px;font-size:14px;color:#4b5563;line-height:1.5;">
                  <strong style="color:#111827;">Daily AI Briefing (8:00 AM)</strong><br>
                  The top 5 AI industry developments summarized with actionable analysis on market impact.
                </div>
                <div style="margin-bottom:16px;font-size:14px;color:#4b5563;line-height:1.5;">
                  <strong style="color:#111827;">Early Program Alerts</strong><br>
                  Advance notifications for Google, Microsoft, AWS, and Meta student programs with direct application links.
                </div>
                <div style="font-size:14px;color:#4b5563;line-height:1.5;">
                  <strong style="color:#111827;">Intelligence Dashboard</strong><br>
                  Access your personal portal to track applications, monitor activity, and search global tech news.
                </div>
              </div>
              
              <div style="text-align:center;margin:32px 0;">
                <a href="https://novabrief-web.onrender.com/user/dashboard" style="background-color:#0f172a;color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:6px;font-size:16px;font-weight:600;display:inline-block;">Access Dashboard</a>
              </div>
            </td>
          </tr>
          <tr>
            <td style="background-color:#f9fafb;border-top:1px solid #e5e7eb;padding:24px;text-align:center;font-size:12px;color:#6b7280;">
              <p style="margin:0 0 8px 0;">Nova Brief &bull; Professional AI Intelligence</p>
              <p style="margin:0;"><a href="https://novabrief-web.onrender.com" style="color:#3b82f6;text-decoration:none;">Platform</a> &bull; <a href="https://novabrief-web.onrender.com/privacy" style="color:#6b7280;text-decoration:none;">Privacy Policy</a> &bull; <a href="https://novabrief-web.onrender.com/terms" style="color:#6b7280;text-decoration:none;">Terms of Service</a></p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_welcome_email(to_email: str, name: str = None) -> bool:
    return send_email(to_email, 'Welcome to Nova Brief ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Daily AI & Student Program Alerts', format_welcome_email(to_email, name))


def format_program_welcome_email(subscriber_email: str, name: str = None, program_title: str = None) -> str:
    greeting = f"Hello {name}," if name else "Hello,"
    prog_text = f"specifically for <strong>{program_title}</strong> and other elite programs" if program_title else "for elite student programs"
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background-color:#f6f9fc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#333333;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f6f9fc;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="100%" style="max-width:600px;background-color:#ffffff;border:1px solid #e6ebf1;border-radius:8px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.05);">
          <tr>
            <td style="padding:40px;text-align:left;">
              <h1 style="margin:0 0 16px 0;font-size:24px;font-weight:600;color:#111827;">Alert Registration Confirmed</h1>
              <p style="margin:0 0 24px 0;font-size:16px;color:#4b5563;line-height:1.6;">{greeting}<br><br>Your alert configuration has been successfully provisioned {prog_text}. You will now receive priority notifications before these applications officially open to the public.</p>
              
              <div style="background-color:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:16px;margin-bottom:24px;color:#166534;font-size:14px;line-height:1.5;">
                <strong>Status: Active</strong><br>Your email ({subscriber_email}) is secured in our priority notification queue.
              </div>
              
              <div style="text-align:center;margin:32px 0;">
                <a href="https://novabrief-web.onrender.com/user/dashboard" style="background-color:#059669;color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:6px;font-size:16px;font-weight:600;display:inline-block;">View Program Dashboard</a>
              </div>
            </td>
          </tr>
          <tr>
            <td style="background-color:#f9fafb;border-top:1px solid #e5e7eb;padding:24px;text-align:center;font-size:12px;color:#6b7280;">
              <p style="margin:0 0 8px 0;">Nova Brief &bull; Elite Program Alerts</p>
              <p style="margin:0;"><a href="https://novabrief-web.onrender.com" style="color:#3b82f6;text-decoration:none;">Platform</a> &bull; <a href="https://novabrief-web.onrender.com/privacy" style="color:#6b7280;text-decoration:none;">Privacy Policy</a> &bull; <a href="https://novabrief-web.onrender.com/terms" style="color:#6b7280;text-decoration:none;">Terms of Service</a></p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_program_welcome_email(to_email: str, name: str = None, program_title: str = None) -> bool:
    subject = f"ÃƒÂ°Ã…Â¸Ã…Â½Ã¢â‚¬Å“ Welcome to Student Program Alerts ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Nova Brief" if not program_title else f"ÃƒÂ°Ã…Â¸Ã…Â½Ã¢â‚¬Å“ Program Alert Confirmation: {program_title}"
    return send_email(to_email, subject, format_program_welcome_email(to_email, name, program_title))


def send_login_email(to_email: str) -> bool:
    return True


def format_news_email(news_items: List[Dict[str, Any]]) -> str:
    today = datetime.now().strftime('%A, %B %d, %Y')
    if not news_items:
        return f"""<!DOCTYPE html><html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f6f9fc;padding:40px 20px;"><div style="max-width:600px;margin:0 auto;background:#fff;border:1px solid #e6ebf1;border-radius:8px;padding:32px;"><h2 style="margin:0 0 16px;font-size:20px;color:#111827;">AI Intelligence Briefing &bull; {today}</h2><div style="padding:16px;background:#fef3c7;border-radius:6px;color:#92400e;font-size:14px;">No significant AI developments detected in the current cycle.</div></div></body></html>"""

    items_html = ''.join(f"""
    <div style="margin-bottom:32px;padding-bottom:32px;border-bottom:1px solid #e5e7eb;">
      <div style="font-size:18px;font-weight:600;color:#111827;margin-bottom:8px;line-height:1.4;">{i}. {item['title']}</div>
      <div style="font-size:12px;color:#6b7280;margin-bottom:16px;text-transform:uppercase;letter-spacing:0.05em;">{item['source']} &bull; {item['published']}</div>
      <div style="font-size:15px;color:#374151;margin-bottom:12px;line-height:1.6;"><strong>Executive Summary:</strong> {item['summary']}</div>
      <div style="font-size:14px;color:#4b5563;margin-bottom:12px;line-height:1.5;"><strong>Market Impact:</strong> {item['why_important']}</div>
      <div style="font-size:14px;color:#4b5563;margin-bottom:16px;line-height:1.5;"><strong>Strategic Outlook:</strong> {item['future_change']}</div>
      <a href="{item['url']}" style="display:inline-block;color:#3b82f6;font-size:14px;font-weight:600;text-decoration:none;">Read Full Report &rarr;</a>
    </div>""" for i, item in enumerate(news_items, 1))

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background-color:#f6f9fc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#333333;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f6f9fc;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="100%" style="max-width:640px;background-color:#ffffff;border:1px solid #e6ebf1;border-radius:8px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.05);">
          <tr>
            <td style="padding:40px;text-align:left;">
              <div style="font-size:12px;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">Nova Brief Intelligence</div>
              <h1 style="margin:0 0 8px 0;font-size:28px;font-weight:700;color:#111827;letter-spacing:-0.02em;">AI Market Briefing</h1>
              <p style="margin:0 0 32px 0;font-size:15px;color:#6b7280;">{today}</p>
              
              {items_html}
              
              <div style="margin-top:8px;font-size:14px;color:#6b7280;line-height:1.5;text-align:center;">
                <strong>Strategic Overview:</strong> Artificial intelligence continues to transition from conceptual frameworks to core enterprise infrastructure. Remain informed to maintain strategic advantage.
              </div>
            </td>
          </tr>
          <tr>
            <td style="background-color:#f9fafb;border-top:1px solid #e5e7eb;padding:24px;text-align:center;font-size:12px;color:#9ca3af;">
              <p style="margin:0 0 8px 0;">Nova Brief &bull; Proprietary Intelligence Feed</p>
              <p style="margin:0;"><a href="https://novabrief-web.onrender.com" style="color:#6b7280;text-decoration:underline;">Dashboard</a> &bull; <a href="https://novabrief-web.onrender.com/privacy" style="color:#6b7280;text-decoration:underline;">Privacy</a></p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    items_html = ''.join(f"""
    <div style="margin:18px 0;padding:18px;background:#f8fafc;border-left:5px solid #2563eb;border-radius:8px;">
      <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:8px;">{i}. {item['title']}</div>
      <div style="font-size:12px;color:#64748b;margin-bottom:10px;">{item['source']} ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢ {item['published']}</div>
      <div style="font-size:14px;color:#334155;margin-bottom:8px;"><strong>Summary:</strong> {item['summary']}</div>
      <div style="font-size:13px;color:#334155;margin-bottom:6px;"><strong>Why it matters:</strong> {item['why_important']}</div>
      <div style="font-size:13px;color:#334155;margin-bottom:6px;"><strong>What could change:</strong> {item['future_change']}</div>
      <div style="font-size:13px;color:#334155;margin-bottom:8px;"><strong>Why you should care:</strong> {item['why_care']}</div>
      <a href="{item['url']}" style="color:#2563eb;font-size:12px;font-weight:600;text-decoration:none;">Read article ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢</a>
    </div>""" for i, item in enumerate(news_items, 1))

    return f"""<html><body style="font-family:Arial,sans-serif;background:#eef4ff;color:#1f2937;padding:20px;">
<div style="max-width:760px;margin:0 auto;background:#fff;border-radius:14px;padding:24px;box-shadow:0 12px 28px rgba(27,56,97,.10);">
  <div style="background:linear-gradient(135deg,#111827,#2563eb);color:#fff;padding:22px;border-radius:10px;margin-bottom:18px;">
    <h1 style="margin:0 0 6px;font-size:28px;">AI Morning Brief</h1>
    <p style="margin:0;font-size:14px;opacity:.9;">{today}</p>
  </div>
  <div style="font-size:14px;color:#475569;margin-bottom:20px;line-height:1.6;">
    Here are today's most important AI developments ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â each one brief, important, and tied to what it could mean for the future.
  </div>
  {items_html}
  <div style="margin-top:22px;padding-top:18px;border-top:1px solid #e5e7eb;font-size:13px;color:#475569;">
    <strong>Big picture:</strong> AI is increasingly moving from novelty to infrastructure. Stay informed. Stay ahead.
  </div>
</div></body></html>"""


def format_program_email(program: Dict[str, Any]) -> str:
    """Format student program notification email with direct registration link."""
    today = datetime.now().strftime('%A, %B %d, %Y')
    deadline_text = f"<strong>Application Deadline:</strong> {program.get('deadline', 'Refer to official portal')}<br>" if program.get('deadline') else ''
    launch_text = f"<strong>Launch Date:</strong> {program.get('launch_date', 'Imminent')}<br>" if program.get('launch_date') else ''

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background-color:#f6f9fc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#333333;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f6f9fc;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="100%" style="max-width:600px;background-color:#ffffff;border:1px solid #e6ebf1;border-radius:8px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.05);">
          <tr>
            <td style="padding:40px;text-align:left;">
              <div style="font-size:12px;font-weight:700;color:#059669;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">Priority Application Alert</div>
              <h1 style="margin:0 0 8px 0;font-size:24px;font-weight:600;color:#111827;">{program.get('title', 'New Program')}</h1>
              <p style="margin:0 0 24px 0;font-size:15px;color:#6b7280;">Offered by <strong>{program.get('company', 'Corporate Partner')}</strong></p>
              
              <div style="background-color:#f9fafb;border-radius:6px;padding:24px;margin-bottom:24px;font-size:15px;color:#374151;line-height:1.6;border:1px solid #e5e7eb;">
                {launch_text}
                {deadline_text}
                <div style="margin-top:16px;"><strong>Program Details:</strong><br>{program.get('description', 'A new elite opportunity has opened for students. Review the official portal for comprehensive details.')}</div>
              </div>
              
              <div style="text-align:center;margin:32px 0;">
                <a href="{program.get('registration_url', 'https://novabrief-web.onrender.com')}" style="background-color:#059669;color:#ffffff;text-decoration:none;padding:14px 32px;border-radius:6px;font-size:16px;font-weight:600;display:inline-block;">Access Official Application</a>
              </div>
            </td>
          </tr>
          <tr>
            <td style="background-color:#f9fafb;border-top:1px solid #e5e7eb;padding:24px;text-align:center;font-size:12px;color:#6b7280;">
              <p style="margin:0 0 8px 0;">Nova Brief &bull; Career Intelligence</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_contact_notification_email(name: str, email: str, subject: str, message: str) -> bool:
    admin_email = get_env_value('ADMIN_EMAIL', 'GMAIL_USER', 'EMAIL_USER')
    if not admin_email:
        return False
    today = datetime.now().strftime('%A, %B %d, %Y %H:%M')
    html = f"""<html><body style="font-family:Arial,sans-serif;background:#f4f7ff;padding:24px;">
<div style="max-width:680px;margin:0 auto;background:#fff;border-radius:16px;padding:28px;">
  <div style="background:linear-gradient(135deg,#111827,#2563eb);color:#fff;padding:18px 22px;border-radius:12px;margin-bottom:18px;">
    <h2 style="margin:0 0 4px;">Nova Brief ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Contact Form</h2><p style="margin:0;font-size:13px;opacity:.85;">{today}</p>
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
        logger.info('No programs to notify about today.')
        return 0

    subscribers = db.get_program_subscribers()
    if not subscribers:
        logger.info('No program subscribers found.')
        return 0

    sent_count = 0
    for program in programs:
        subject = f"🎓 New Program Alert: {program['title']} by {program['company']}"
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
        if default:
            all_recipients = [default]
    return all_recipients


# The main agent function. It finds news, formats it, and emails all subscribers.

def fetch_latest_news_hourly() -> int:
    logger.info('Starting hourly news fetch...')
    db = NewsDatabase()
    news_items = search_ai_news(limit=5)
    if news_items:
        db.save_news_batch(news_items)
        db.log_agent_event('hourly_fetch', f'Fetched and saved {len(news_items)} new articles')
        return len(news_items)
    return 0
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
        db.log_agent_event('error', 'No recipient emails configured')
        return False

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


# The entry point of our script. It checks if we should run now or start the scheduler.
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
        run_news_digest()
        return

    if args.test_email:
        to = get_env_value('RECIPIENT_EMAIL', 'GMAIL_USER', 'EMAIL_USER')
        if to:
            send_email(to, 'Nova Brief - Test Email', '<html><body><h2>🚀 Test Email</h2><p>Your Nova Brief agent is working correctly.</p></body></html>')
        return

    if args.schedule:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            scheduler = BackgroundScheduler()
            scheduler.add_job(run_news_digest, 'cron', hour=8, minute=0, id='ai_morning_brief')
            scheduler.add_job(send_program_notifications, 'cron', hour=9, minute=0, id='program_notifications')
            scheduler.add_job(generate_daily_seo_blog, 'cron', hour=10, minute=0, id='auto_blog_agent')
            scheduler.start()
            logger.info('Scheduler started. Daily brief 8AM, Programs 9AM, Auto-Blog 10AM.')
            try:
                while True:
                    pass
            except KeyboardInterrupt:
                scheduler.shutdown()
                sys.exit(0)
        except ImportError:
            logger.error('APScheduler not installed.')
        return

    run_news_digest()


import random
import psycopg2
import psycopg2.extras
import os
import re

def generate_daily_seo_blog():
    db = NewsDatabase()
    topics = [
        "The Ultimate Guide to AI Automation for Students",
        "Top 10 Free Google Certifications to Boost Your Tech Career",
        "How Generative AI is Changing the Software Engineering Landscape",
        "Why Every College Student Needs to Learn Python in 2026",
        "Maximizing Productivity: How to Use AI Tools to Study Faster"
    ]
    
    title = random.choice(topics)
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    
    # Generate SEO optimized HTML content
    content = f'''
    <p class="mb-4">The tech industry is evolving faster than ever. <strong>{title}</strong> is a topic that is dominating discussions across Silicon Valley and university campuses alike.</p>
    <h2 class="text-2xl font-bold mt-6 mb-3 text-slate-800">Why This Matters Now</h2>
    <p class="mb-4">Recent data shows that individuals who leverage these modern tools are 40% more productive than their peers. Whether you are trying to land a prestigious internship or build your own startup, understanding this is critical to your long-term success.</p>
    <h2 class="text-2xl font-bold mt-6 mb-3 text-slate-800">Actionable Steps to Get Started</h2>
    <ul class="list-disc pl-5 mb-4 space-y-2">
        <li><strong>Research:</strong> Spend at least 30 minutes a day reading up on the latest industry trends.</li>
        <li><strong>Apply:</strong> Use tools like Nova Brief to track essential news and updates.</li>
        <li><strong>Certify:</strong> Look for free online certifications to prove your knowledge to employers.</li>
    </ul>
    <p>By staying ahead of the curve, you guarantee yourself a place in the future of work. Don't wait until the industry passes you byâ€”start building your skills today.</p>
    '''
    
    meta_desc = f"Learn about {title}. Discover how students and professionals are leveraging technology for massive career growth."
    
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()
        
        # Check if slug exists to prevent duplicates
        cursor.execute("SELECT id FROM blog_posts WHERE slug=%s", (slug,))
        if cursor.fetchone():
            conn.close()
            return
            
        cursor.execute('''INSERT INTO blog_posts (title, slug, content, meta_description)
                          VALUES (%s, %s, %s, %s)''', (title, slug, content, meta_desc))
        conn.commit()
        conn.close()
        logger.info(f"Auto-Blogging Agent published new SEO article: {title}")
    except Exception as e:
        logger.error(f"Auto-blogging failed: {e}")


if __name__ == '__main__':
    main()


def send_password_reset_email(email: str, token: str) -> None:
    reset_url = f"https://novabrief-web.onrender.com/user/reset-password/{token}"
    subject = "Reset Your Password - Nova Brief"
    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background-color:#f6f9fc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#333333;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f6f9fc;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="100%" style="max-width:600px;background-color:#ffffff;border:1px solid #e6ebf1;border-radius:8px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.05);">
          <tr>
            <td style="padding:40px;text-align:left;">
              <h1 style="margin:0 0 16px 0;font-size:24px;font-weight:600;color:#111827;">Password Reset Request</h1>
              <p style="margin:0 0 24px 0;font-size:16px;color:#4b5563;line-height:1.6;">We received a request to reset the password for your Nova Brief account associated with {email}.</p>
              <p style="margin:0 0 24px 0;font-size:16px;color:#4b5563;line-height:1.6;">Click the button below to securely set a new password. This link will expire in 1 hour.</p>
              
              <div style="text-align:center;margin:32px 0;">
                <a href="{reset_url}" style="background-color:#0f172a;color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:6px;font-size:16px;font-weight:600;display:inline-block;">Reset Password</a>
              </div>
              
              <p style="margin:0;font-size:14px;color:#6b7280;line-height:1.5;">If you did not request a password reset, please ignore this email or contact support if you have concerns.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    send_email(email, subject, html_content)
    reset_link = f'https://novabrief-web.onrender.com/user/reset-password/{token}'
    subject = "Password Reset Request - Nova Brief"
    html = f'''
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h2>Reset Your Password</h2>
        <p>We received a request to reset your password for your Nova Brief account.</p>
        <p>Click the link below to set a new password. This link will expire in 1 hour.</p>
        <p><a href="{reset_link}" style="display:inline-block; padding:10px 20px; background-color:#2563eb; color:#fff; text-decoration:none; border-radius:5px;">Reset Password</a></p>
        <p>If you didn't request this, you can safely ignore this email.</p>
      </body>
    </html>
    '''
    try:
        msg = MIMEMultipart()
        msg['From'] = f"Nova Brief <{sender_email}>"
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
    except Exception as e:
        logger.error(f'Failed to send password reset to {email}: {e}')

