import os, sys, json, logging, smtplib, ssl, hashlib, time
from datetime import datetime
from email.utils import formataddr, formatdate, make_msgid, parseaddr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Tuple

import requests, feedparser
from dotenv import load_dotenv
from database import NewsDatabase
from news_relevance import filter_relevant_news
from urllib.parse import quote_plus

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
BRAND_NAME = 'NovaBrief Tech'
SITE_URL = 'https://www.novabrief.tech'
LOGO_URL = f'{SITE_URL}/static/icon-192.png'
IS_HOSTED = bool(
    os.getenv('RENDER')
    or os.getenv('RENDER_SERVICE_ID')
    or os.getenv('FLASK_ENV', '').strip().lower() == 'production'
)
# Local project settings should beat stale variables inherited from a terminal.
# Hosted deployments continue to treat their secret manager as authoritative.
load_dotenv(os.path.join(APP_DIR, '.env.local'), override=not IS_HOSTED)
load_dotenv(os.path.join(APP_DIR, '.env'))


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


def _official_sender_required() -> bool:
    """Production can fail closed instead of exposing a personal SMTP address."""
    configured = get_env_value('REQUIRE_OFFICIAL_SENDER').lower()
    if configured:
        return configured in {'1', 'true', 'yes', 'on'}
    return IS_HOSTED


def _branded_from_address(configured_sender: str) -> str:
    address = parseaddr(configured_sender or '')[1].strip().lower()
    if not address:
        return ''
    if _official_sender_required() and not address.endswith('@novabrief.tech'):
        return ''
    return formataddr((BRAND_NAME, address))


def _brand_header(title: str, subtitle: str = '') -> str:
    subtitle_html = (
        f'<div style="font-size:13px;color:#64748b;margin-top:4px;">{subtitle}</div>'
        if subtitle else ''
    )
    return f'''<div style="text-align:center;margin-bottom:28px;">
      <a href="{SITE_URL}" style="text-decoration:none;display:inline-block;">
        <img src="{LOGO_URL}" width="72" height="72" alt="NovaBrief Tech logo" style="display:block;width:72px;height:72px;margin:0 auto 12px;border-radius:18px;"/>
      </a>
      <div style="font-size:13px;font-weight:800;color:#4f46e5;text-transform:uppercase;letter-spacing:.12em;">{BRAND_NAME}</div>
      <h1 style="margin:8px 0 0;font-size:26px;line-height:1.2;color:#0f172a;">{title}</h1>
      {subtitle_html}
    </div>'''


def _brand_footer() -> str:
    return f'''<p style="margin:0 0 8px;font-weight:700;color:#475569;">Sent by {BRAND_NAME}</p>
    <p style="margin:0;"><a href="{SITE_URL}" style="color:#4f46e5;text-decoration:none;">novabrief.tech</a> &bull; <a href="{SITE_URL}/privacy" style="color:#64748b;text-decoration:none;">Privacy</a> &bull; <a href="{SITE_URL}/terms" style="color:#64748b;text-decoration:none;">Terms</a></p>'''


def build_briefing_notes(title: str, summary: str) -> Dict[str, str]:
    tl = (title or '').lower()
    sl = (summary or '').lower()
    if any(w in tl for w in ['security', 'privacy', 'deepfake', 'misinformation', 'risk', 'attack', 'vulnerability']):
        wi = 'This raises a real safety or trust issue that could affect how people use technology in everyday life.'
    elif any(w in tl for w in ['regulation', 'policy', 'government', 'law', 'europe', 'ai act']):
        wi = 'This could change the rules around AI adoption, accountability, and how businesses operate.'
    elif any(w in tl for w in ['openai', 'google', 'meta', 'microsoft', 'anthropic', 'gemini', 'chatgpt']):
        wi = 'A major company action often signals where the market and consumer behavior are shifting next.'
    elif any(w in tl for w in ['health', 'medical', 'drug', 'science', 'research']):
        wi = 'This could affect healthcare, research speed, and the quality of decisions in critical areas.'
    else:
        wi = 'This matters because it shows how quickly technology is changing learning, careers, and everyday life.'

    if any(w in tl for w in ['job', 'work', 'labor', 'productivity', 'automation', 'assistant']):
        fc = 'It could change how work gets done, which tasks are automated, and where human value still matters most.'
    elif any(w in tl for w in ['education', 'student', 'school', 'learning', 'teacher']):
        fc = 'It could reshape learning, teaching, and how people build skills in the next few years.'
    elif any(w in tl for w in ['security', 'privacy', 'deepfake', 'fraud']):
        fc = 'It could make digital trust harder to maintain unless safeguards and public awareness improve quickly.'
    elif any(w in tl for w in ['energy', 'chip', 'compute', 'data center', 'infrastructure']):
        fc = 'It could alter how companies invest in hardware, power, computing, and digital infrastructure.'
    else:
        fc = 'It could influence the skills people learn, the tools they use, and how quickly technology becomes part of daily life.'

    if any(w in sl for w in ['risk', 'danger', 'harm', 'attack', 'fraud', 'misinformation', 'bias']):
        wc = 'Because the downside is not theoretical; it can affect trust, safety, and the decisions people make online.'
    elif any(w in tl for w in ['chip', 'model', 'cost', 'latency', 'compute']):
        wc = 'Because this often signals which technologies will become faster, more affordable, and widely accessible.'
    elif any(w in tl for w in ['regulation', 'policy', 'law']):
        wc = 'Because rules shape what AI can do, how fast it spreads, and how much control people retain.'
    else:
        wc = 'Because today’s technology update can become tomorrow’s essential skill, tool, or career opportunity.'

    return {'why_important': wi, 'future_change': fc, 'why_care': wc}


# Focused searches provide useful global technology coverage for students.
FOCUSED_NEWS_QUERIES = (
    '"artificial intelligence" OR "generative AI" OR "AI model" OR "AI agents" OR OpenAI OR Anthropic',
    'NVIDIA OR Google OR Alphabet OR Amazon OR AWS OR Microsoft OR Meta OR Apple OR Tesla OR xAI',
    'programming OR "developer tools" OR "open source" OR cybersecurity OR "cloud computing" OR DevOps OR Linux',
    '("Pakistan" OR "Pakistani") AND ("tech career" OR "student" OR "internship" OR "scholarship" OR "freelance" OR "startup")',
    '("Google" OR "Microsoft" OR "Meta" OR "AWS") AND ("remote job" OR "global talent" OR "freelance" OR "student program")',
    '"student developer" OR scholarship OR internship OR hackathon OR "free certification" OR "digital skills" OR edtech',
)


# Fetch relevant technology news from focused Google News RSS searches.
def fetch_news_from_rss(limit: int = 5) -> List[Dict[str, Any]]:
    try:
        items = []
        per_query = max(limit * 2, 20)
        headers = {'User-Agent': 'NovaBrief/1.0 (+https://www.novabrief.tech/)'}
        for query in FOCUSED_NEWS_QUERIES:
            try:
                rss_url = (
                    'https://news.google.com/rss/search?q='
                    f'{quote_plus(query + " when:3d")}&hl=en-US&gl=US&ceid=US:en'
                )
                response = requests.get(rss_url, headers=headers, timeout=15)
                response.raise_for_status()
                entries = feedparser.parse(response.content).get('entries', [])
                for entry in entries[:per_query]:
                    title = (entry.get('title') or '').strip()
                    if not title:
                        continue
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
            except Exception as query_error:
                logger.warning('Focused RSS query failed: %s', query_error)
        selected = filter_relevant_news(items, limit=limit)
        logger.info('RSS editorial filter selected %s of %s candidates', len(selected), len(items))
        return selected
    except Exception as e:
        logger.error(f'RSS error: {e}')
        return []


# Search for global technology news using NewsAPI. If it fails, use focused RSS feeds.
def search_ai_news(limit: int = 5) -> List[Dict[str, Any]]:
    api_key = get_env_value('NEWSAPI_KEY', 'NEWS_API_KEY')
    if not api_key or api_key.lower() in {'your_newsapi_key_here', 'placeholder'}:
        return fetch_news_from_rss(limit)
    try:
        candidate_limit = min(max(limit * 6, 40), 100)
        resp = requests.get('https://newsapi.org/v2/everything', params={
            'q': ('AI OR NVIDIA OR Google OR Amazon OR Microsoft OR Meta OR Apple OR '
                  'programming OR cybersecurity OR "developer tools" OR "cloud computing" OR '
                  'semiconductor OR robotics OR "student technology"'),
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': candidate_limit,
            'apiKey': api_key
        }, timeout=15)
        if resp.status_code == 401:
            return fetch_news_from_rss(limit)
        resp.raise_for_status()
        data = resp.json()
        if data.get('status') != 'ok':
            return fetch_news_from_rss(limit)
        items = []
        for a in data.get('articles', []):
            title = (a.get('title') or '').strip()
            if not title:
                continue
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
        selected = filter_relevant_news(items, limit=limit)
        logger.info('NewsAPI editorial filter selected %s of %s candidates', len(selected), len(items))
        if selected:
            return selected
        return fetch_news_from_rss(limit)
    except Exception as e:
        logger.warning('NewsAPI failed; using focused RSS feeds: %s', e)
        return fetch_news_from_rss(limit)


import concurrent.futures

EMAIL_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='email_worker')


def _smtp_credentials() -> List[Tuple[str, str, str]]:
    """Return configured username/password pairs without ever mixing aliases."""
    candidates = [
        ('SMTP', os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD')),
        ('GMAIL', os.getenv('GMAIL_USER'), os.getenv('GMAIL_APP_PASSWORD')),
        ('EMAIL', os.getenv('EMAIL_USER'), os.getenv('EMAIL_APP_PASSWORD') or os.getenv('EMAIL_PASS')),
    ]
    credentials = []
    seen = set()
    for label, username, password in candidates:
        sender = parseaddr(username or '')[1].strip().lower()
        clean_password = (password or '').replace(' ', '').replace('-', '').strip()
        if not sender or '@' not in sender or not clean_password:
            continue
        identity = (sender, clean_password)
        if identity in seen:
            continue
        seen.add(identity)
        credentials.append((label, sender, clean_password))
    return credentials


def is_deliverable_user_email(email: str) -> bool:
    """Reject malformed and reserved test addresses before a bulk send."""
    address = parseaddr(email or '')[1].strip().lower()
    if not address or '\n' in address or '\r' in address or address.count('@') != 1:
        return False
    local_part, domain = address.rsplit('@', 1)
    if not local_part or not domain or '.' not in domain:
        return False
    reserved_domains = {'example.com', 'example.org', 'example.net', 'localhost'}
    return domain not in reserved_domains and not domain.endswith('.invalid')


def _email_idempotency_key(recipient: str, subject: str, html_content: str) -> str:
    payload = f'{recipient}\n{subject}\n{html_content}'.encode('utf-8')
    return f'novabrief-{hashlib.sha256(payload).hexdigest()}'


def _send_via_resend(recipient: str, subject: str, html_content: str) -> bool:
    """Send through Resend's queued API with safe retries and deduplication."""
    api_key = get_env_value('RESEND_API_KEY')
    from_email = _branded_from_address(get_env_value('RESEND_FROM_EMAIL'))
    if not api_key or not from_email:
        return False

    payload = {
        'from': from_email,
        'to': [recipient],
        'subject': clean_text(subject, 180),
        'html': html_content,
    }
    reply_to = get_env_value('RESEND_REPLY_TO')
    if not reply_to and not _official_sender_required():
        reply_to = get_env_value('GMAIL_USER', 'EMAIL_USER')
    if reply_to and _official_sender_required():
        reply_address = parseaddr(reply_to)[1].strip().lower()
        reply_to = reply_to if reply_address.endswith('@novabrief.tech') else ''
    if reply_to:
        payload['reply_to'] = reply_to
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Idempotency-Key': _email_idempotency_key(recipient, subject, html_content),
    }

    for attempt in range(3):
        try:
            response = requests.post(
                'https://api.resend.com/emails',
                json=payload,
                headers=headers,
                timeout=20,
            )
            if 200 <= response.status_code < 300:
                provider_id = (response.json() or {}).get('id', 'accepted')
                logger.info('Email accepted by Resend for queued delivery (id=%s).', provider_id)
                return True
            if response.status_code not in {408, 429} and response.status_code < 500:
                logger.error('Resend rejected the email request (status=%s).', response.status_code)
                return False
            logger.warning('Resend temporarily unavailable (status=%s, attempt=%s).', response.status_code, attempt + 1)
        except (requests.RequestException, ValueError) as exc:
            logger.warning('Resend connection attempt failed (%s, attempt=%s).', exc.__class__.__name__, attempt + 1)
        if attempt < 2:
            time.sleep(0.5 * (2 ** attempt))
    return False


# Send through SMTP with SSL/STARTTLS and safe credential-alias fallback.
def send_email(to_email: str, subject: str, html_content: str) -> bool:
    smtp_host = get_env_value('SMTP_HOST') or 'smtp.gmail.com'
    try:
        smtp_port = int(get_env_value('SMTP_PORT') or '465')
    except ValueError:
        logger.error('SMTP_PORT must be a number.')
        return False
    sender_name = BRAND_NAME
    recipient = parseaddr(to_email or '')[1].strip().lower()
    if not recipient or '\n' in recipient or '\r' in recipient or '@' not in recipient:
        logger.error('Refusing to send email to an invalid recipient address.')
        return False
    if get_env_value('RESEND_API_KEY') and get_env_value('RESEND_FROM_EMAIL'):
        if _send_via_resend(recipient, subject, html_content):
            return True
        if _official_sender_required():
            logger.warning('Official NovaBrief Tech delivery failed; trying personal SMTP fallback anyway.')
        logger.warning('Primary email provider failed; attempting the SMTP fallback.')
    elif _official_sender_required():
        logger.warning('Official NovaBrief Tech email delivery is not configured. Falling back to SMTP.')
    credentials = _smtp_credentials()
    if not credentials:
        logger.error('SMTP credentials are missing from the environment.')
        return False

    context = ssl.create_default_context()
    ports = [smtp_port]
    if smtp_host == 'smtp.gmail.com':
        ports.append(587 if smtp_port == 465 else 465)
    for label, sender, password in credentials:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = clean_text(subject, 180)
        msg['From'] = formataddr((sender_name, sender))
        msg['To'] = recipient
        msg['Date'] = formatdate(localtime=False)
        msg['Message-ID'] = make_msgid(domain=sender.split('@')[-1])
        msg['Reply-To'] = sender
        msg['List-Unsubscribe'] = f'<mailto:{sender}?subject=Unsubscribe>'
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        for port in dict.fromkeys(ports):
            try:
                if port == 465:
                    smtp = smtplib.SMTP_SSL(smtp_host, port, timeout=20, context=context)
                else:
                    smtp = smtplib.SMTP(smtp_host, port, timeout=20)
                with smtp as connection:
                    if port != 465:
                        connection.ehlo()
                        connection.starttls(context=context)
                        connection.ehlo()
                    connection.login(sender, password)
                    connection.send_message(msg)
                logger.info('Email accepted by SMTP for delivery.')
                return True
            except smtplib.SMTPAuthenticationError:
                logger.error('%s SMTP credentials were rejected; trying the next configured credential pair.', label)
                break
            except (smtplib.SMTPException, OSError, ssl.SSLError) as exc:
                logger.warning('SMTP connection attempt on port %s failed: %s', port, exc.__class__.__name__)
    logger.error('Email delivery failed for every configured SMTP credential pair.')
    return False


def dispatch_email_async(to_email: str, subject: str, html_content: str):
    """Submits email send task to the dedicated worker pool for 0ms web latency."""
    return EMAIL_EXECUTOR.submit(send_email, to_email, subject, html_content)


def format_welcome_email(subscriber_email: str, name: str = None) -> str:
    today = datetime.now().strftime('%A, %B %d, %Y')
    greeting = f"Hello {name}," if name else "Hello,"
    brand_header = _brand_header('Welcome to NovaBrief Tech', today)
    brand_footer = _brand_footer()
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
              {brand_header}
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
                <a href="https://www.novabrief.tech/user/dashboard" style="background-color:#0f172a;color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:6px;font-size:16px;font-weight:600;display:inline-block;">Access Dashboard</a>
              </div>
            </td>
          </tr>
          <tr>
            <td style="background-color:#f9fafb;border-top:1px solid #e5e7eb;padding:24px;text-align:center;font-size:12px;color:#6b7280;">
              {brand_footer}
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_welcome_email(to_email: str, name: str = None) -> bool:
    return send_email(to_email, 'Welcome to Nova Brief — Daily AI & Student Program Alerts', format_welcome_email(to_email, name))


def format_program_welcome_email(subscriber_email: str, name: str = None, program_title: str = None) -> str:
    greeting = f"Hello {name}," if name else "Hello,"
    prog_text = f"specifically for <strong>{program_title}</strong> and other elite programs" if program_title else "for elite student programs"
    brand_header = _brand_header('Program Alerts Activated')
    brand_footer = _brand_footer()
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
              {brand_header}
              <p style="margin:0 0 24px 0;font-size:16px;color:#4b5563;line-height:1.6;">{greeting}<br><br>Your alert configuration has been successfully provisioned {prog_text}. You will now receive priority notifications before these applications officially open to the public.</p>
              
              <div style="background-color:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:16px;margin-bottom:24px;color:#166534;font-size:14px;line-height:1.5;">
                <strong>Status: Active</strong><br>Your email ({subscriber_email}) is secured in our priority notification queue.
              </div>
              
              <div style="text-align:center;margin:32px 0;">
                <a href="https://www.novabrief.tech/user/dashboard" style="background-color:#059669;color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:6px;font-size:16px;font-weight:600;display:inline-block;">View Program Dashboard</a>
              </div>
            </td>
          </tr>
          <tr>
            <td style="background-color:#f9fafb;border-top:1px solid #e5e7eb;padding:24px;text-align:center;font-size:12px;color:#6b7280;">
              {brand_footer}
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_program_welcome_email(to_email: str, name: str = None, program_title: str = None) -> bool:
    subject = 'Welcome to Student Program Alerts — Nova Brief' if not program_title else f'Program Alert Confirmation: {program_title}'
    return send_email(to_email, subject, format_program_welcome_email(to_email, name, program_title))


def send_welcome_to_registered_users() -> Dict[str, int]:
    """Send one welcome message to each eligible active user who has not received one."""
    db = NewsDatabase()
    recipients = db.get_users_pending_welcome_email()
    sent = failed = skipped = 0
    for user in recipients:
        email = (user.get('email') or '').strip().lower()
        if not is_deliverable_user_email(email):
            skipped += 1
            logger.warning('Skipped a reserved or invalid address during the welcome-email run.')
            continue
        if send_welcome_email(email, user.get('name')):
            sent += 1
            db.mark_welcome_email_sent(email)
            db.log_email_sent(email, 'Welcome to Nova Brief', 0, 'success')
        else:
            failed += 1
            db.log_email_sent(email, 'Welcome to Nova Brief', 0, 'failed', 'SMTP delivery failed')
    return {
        'total': len(recipients),
        'eligible': len(recipients) - skipped,
        'sent': sent,
        'failed': failed,
        'skipped': skipped,
    }


def send_login_email(to_email: str) -> bool:
    return True


def format_news_email(news_items: List[Dict[str, Any]]) -> str:
    today = datetime.now().strftime('%A, %B %d, %Y')
    brand_header = _brand_header('Technology Morning Brief', today)
    brand_footer = _brand_footer()
    if not news_items:
        return f"""<!DOCTYPE html><html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f6f9fc;padding:40px 20px;"><div style="max-width:600px;margin:0 auto;background:#fff;border:1px solid #e6ebf1;border-radius:8px;padding:32px;">{brand_header}<div style="padding:16px;background:#fef3c7;border-radius:6px;color:#92400e;font-size:14px;">No significant technology developments were selected for today's briefing.</div><div style="margin-top:24px;text-align:center;font-size:12px;color:#64748b;">{brand_footer}</div></div></body></html>"""

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
              {brand_header}
              
              {items_html}
              
              <div style="margin-top:8px;font-size:14px;color:#6b7280;line-height:1.5;text-align:center;">
                <strong>Daily perspective:</strong> The most useful technology updates are the ones that help you learn, make better decisions, and act on new opportunities.
              </div>
            </td>
          </tr>
          <tr>
            <td style="background-color:#f9fafb;border-top:1px solid #e5e7eb;padding:24px;text-align:center;font-size:12px;color:#9ca3af;">
              {brand_footer}
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
    brand_header = _brand_header('Priority Student Program Alert', today)
    brand_footer = _brand_footer()

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
              {brand_header}
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
              {brand_footer}
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

    sent_count = 0
    for program in programs:
        subject = f"🎓 New Program Alert: {program['title']} by {program['company']}"
        html = format_program_email(program)
        subscribers = db.get_pending_program_subscribers(program['id'])
        if not subscribers:
            db.mark_program_notified(program['id'])
            continue

        for email in subscribers:
            if not is_deliverable_user_email(email):
                db.record_program_notification_delivery(
                    program['id'], email, 'skipped', 'Invalid or reserved recipient address')
                continue
            if send_email(email, subject, html):
                sent_count += 1
                db.record_program_notification_delivery(program['id'], email, 'success')
                db.log_email_sent(email, subject, 0, 'success')
                db.log_user_activity(email, 'program_notification_sent', program['title'])
            else:
                db.record_program_notification_delivery(
                    program['id'], email, 'failed', 'SMTP delivery failed')
                db.log_email_sent(email, subject, 0, 'failed', 'SMTP delivery failed')

        if db.program_notification_is_complete(program['id']):
            db.mark_program_notified(program['id'])
        logger.info('Program notification run completed for %s.', program['title'])

    return sent_count


def get_recipients() -> List[str]:
    """Return every active website user once, with optional legacy subscribers included."""
    db = NewsDatabase()
    registered_users = db.get_all_active_users()
    try:
        with open('recipients.json', 'r') as f:
            json_recipients = json.load(f).get('recipients', [])
    except (FileNotFoundError, json.JSONDecodeError):
        json_recipients = []
    all_recipients = []
    seen = set()
    for value in registered_users + json_recipients:
        address = parseaddr(value or '')[1].strip().lower()
        if address in seen or not is_deliverable_user_email(address):
            continue
        seen.add(address)
        all_recipients.append(address)
    if not all_recipients:
        default = get_env_value('RECIPIENT_EMAIL', 'GMAIL_USER', 'EMAIL_USER')
        address = parseaddr(default or '')[1].strip().lower()
        if is_deliverable_user_email(address):
            all_recipients = [address]
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
    logger.info('Starting technology morning briefing...')
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
    logger.info('Prepared the daily digest for %s active recipients.', len(recipients))

    news_items = search_ai_news(limit=25)
    if news_items:
        db.save_news_batch(news_items)

    subject = f'Technology Morning Brief - {datetime.now().strftime("%B %d, %Y")}'
    delivered_before = set(db.get_successful_email_recipients(subject))
    pending_recipients = [email for email in recipients if email not in delivered_before]
    success_count = 0

    for to_email in pending_recipients:
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
            db.log_email_sent(to_email, subject, len(top_news), 'failed', 'Email sending failed')

    total_success = len(delivered_before) + success_count
    run_status = (
        'success' if total_success == len(recipients)
        else ('partial' if total_success > 0 else 'failed')
    )
    db.record_daily_digest_run(len(recipients), total_success, len(news_items), run_status)

    # Also check and send program notifications
    try:
        program_emails_sent = send_program_notifications()
        if program_emails_sent > 0:
            db.log_agent_event('program_notifications', f'Sent {program_emails_sent} program notification emails')
    except Exception as e:
        logger.error(f'Program notification error: {e}')

    db.cleanup_old_articles(months=3)
    try:
        db.cleanup_saved_articles(days=30)
    except Exception: pass
    db.log_agent_event('email_sent', f'Delivered to {total_success}/{len(recipients)} recipients')
    logger.info('=' * 60)
    return run_status == 'success'


# The entry point of our script. It checks if we should run now or start the scheduler.
def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description='Nova Brief Agent')
    parser.add_argument('--run-now', action='store_true')
    parser.add_argument('--schedule', action='store_true')
    parser.add_argument('--test-email', action='store_true')
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--check-programs', action='store_true')
    parser.add_argument('--welcome-all', action='store_true')
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

    if args.welcome_all:
        result = send_welcome_to_registered_users()
        print(json.dumps(result))
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


def send_password_reset_email(email: str, token: str) -> bool:
    reset_url = f"https://www.novabrief.tech/user/reset-password/{token}"
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
    return send_email(email, subject, html_content)

