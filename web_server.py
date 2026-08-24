from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from database import NewsDatabase
from datetime import datetime
import os, logging, json
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'nova-brief-secret-key-2026')

from growth_seo_agent.routes import seo_bp
from social_media_agent.routes import social_bp
from analytics_revenue_portal.routes import analytics_bp

app.register_blueprint(seo_bp, url_prefix='/seo')
app.register_blueprint(social_bp, url_prefix='/social')
app.register_blueprint(analytics_bp, url_prefix='/analytics')


ADMIN_EMAIL = (os.getenv('ADMIN_EMAIL') or 'admin@novabrief.local').strip().lower()
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD') or 'NovaBriefAdmin2026!'

logger = logging.getLogger(__name__)
db = NewsDatabase()

RECIPIENTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recipients.json')
if not os.path.exists(RECIPIENTS_FILE):
    try:
        with open(RECIPIENTS_FILE, 'w') as _f:
            json.dump({'recipients': []}, _f)
    except Exception: pass


# â”€â”€ Auth helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def role_required(required_role: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            role = session.get('role')
            if not role:
                if request.path.startswith('/api/'):
                    return jsonify({'status': 'error', 'message': 'Please log in first.'}), 401
                return redirect(url_for('admin_login_page') if required_role == 'admin' else url_for('user_login_page'))
            if role != required_role:
                if request.path.startswith('/api/'):
                    return jsonify({'status': 'error', 'message': 'Access denied.'}), 403
                return redirect(url_for('user_dashboard') if role == 'user' else url_for('dashboard'))
            return func(*args, **kwargs)
        return wrapper
    return decorator

user_required = role_required('user')
admin_required = role_required('admin')


@app.before_request
def track_visitor():
    if request.path.startswith('/static') or request.path.startswith('/api'):
        return
    try:
        db.record_site_visit(request.path, request.remote_addr, request.user_agent.string[:250], session.get('user_email'))
        if session.get('user_email') and session.get('role') == 'user':
            db.log_user_activity(session['user_email'], 'page_visit', None, request.path)
    except Exception:
        pass


def _safe_add_recipient(email: str):
    try:
        with open(RECIPIENTS_FILE, 'r') as f: data = json.load(f)
    except Exception:
        data = {'recipients': []}
    if email not in data.setdefault('recipients', []):
        data['recipients'].append(email)
        with open(RECIPIENTS_FILE, 'w') as f: json.dump(data, f, indent=2)


# â”€â”€ Page routes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@admin_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/user/dashboard')
@user_required
def user_dashboard():
    # Redirect legacy dashboard to the new SaaS OS Dashboard
    return redirect(url_for('analytics.dashboard'))

@app.route('/user/login')
def user_login_page():
    if session.get('role') == 'user': return redirect(url_for('user_dashboard'))
    return render_template('user_login.html')

@app.route('/user/register')
def user_register_page():
    if session.get('role') == 'user': return redirect(url_for('user_dashboard'))
    return render_template('user_register.html')

@app.route('/admin/login')
def admin_login_page():
    if session.get('role') == 'admin': return redirect(url_for('dashboard'))
    return render_template('admin_login.html')

@app.route('/privacy')
def privacy(): return render_template('privacy.html')

@app.route('/terms')
def terms(): return render_template('terms.html')

@app.route('/cookies')
def cookies(): return render_template('cookies.html')


# â”€â”€ Auth API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route('/api/auth/register', methods=['POST'])
def register_user_account():
    p = request.get_json(silent=True) or request.form.to_dict()
    name = (p.get('name') or '').strip()
    email = (p.get('email') or '').strip().lower()
    password = p.get('password') or ''
    if not name or not email or '@' not in email or len(password) < 6:
        return jsonify({'status': 'error', 'message': 'Name, valid email, and password (min 6 chars) are required.'}), 400
    result = db.create_or_update_user_account(email, name, generate_password_hash(password))
    if result == 'exists':
        return jsonify({'status': 'error', 'message': 'Account already has a password. Please login.'}), 409
    _safe_add_recipient(email)
    session.update({'user_email': email, 'user_name': name, 'role': 'user'})
    db.record_user_login(email, 'register')
    db.log_user_activity(email, 'account_created', f'Registered as {name}')
    try:
        from ai_news_agent import send_welcome_email
        import threading
        threading.Thread(target=send_welcome_email, args=(email,), daemon=True).start()
    except Exception: pass
    msg = 'Account created successfully.' if result == 'created' else 'Account activated with new password.'
    return jsonify({'status': 'success', 'message': msg, 'redirect': '/user/dashboard'})


@app.route('/api/auth/login', methods=['POST'])
def login_user_account():
    p = request.get_json(silent=True) or request.form.to_dict()
    email = (p.get('email') or '').strip().lower()
    password = p.get('password') or ''
    user = db.get_user_by_email(email)
    if not user or not user.get('password_hash'):
        return jsonify({'status': 'error', 'message': 'Account not found. Please register first.'}), 404
    if not check_password_hash(user['password_hash'], password):
        return jsonify({'status': 'error', 'message': 'Invalid email or password.'}), 401
    session.update({'user_email': user['email'], 'user_name': user.get('name') or 'User', 'role': 'user'})
    db.record_user_login(email, 'user_login')
    db.log_user_activity(email, 'login', 'User logged in')
    try:
        from ai_news_agent import send_login_email
        import threading
        threading.Thread(target=send_login_email, args=(email,), daemon=True).start()
    except Exception: pass
    return jsonify({'status': 'success', 'message': 'Logged in successfully.', 'redirect': '/user/dashboard'})


@app.route('/api/auth/admin/login', methods=['POST'])
def login_admin_account():
    p = request.get_json(silent=True) or request.form.to_dict()
    email = (p.get('email') or '').strip().lower()
    password = p.get('password') or ''
    if email != ADMIN_EMAIL or password != ADMIN_PASSWORD:
        return jsonify({'status': 'error', 'message': 'Invalid admin credentials.'}), 401
    session.update({'user_email': ADMIN_EMAIL, 'user_name': 'Administrator', 'role': 'admin'})
    db.record_user_login(ADMIN_EMAIL, 'admin_login')
    return jsonify({'status': 'success', 'message': 'Admin login successful.', 'redirect': '/dashboard'})


@app.route('/api/auth/me')
def current_session_user():
    if not session.get('role'): return jsonify({'authenticated': False})
    return jsonify({'authenticated': True, 'email': session.get('user_email'),
                    'name': session.get('user_name'), 'role': session.get('role')})


@app.route('/api/auth/logout', methods=['POST'])
def logout_account():
    if session.get('user_email') and session.get('role') == 'user':
        try: db.log_user_activity(session['user_email'], 'logout', 'User logged out')
        except Exception: pass
    session.clear()
    return jsonify({'status': 'success', 'redirect': '/'})


# â”€â”€ User dashboard API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route('/api/user/overview')
@user_required
def get_user_overview():
    email = session.get('user_email')
    db.log_user_activity(email, 'dashboard_view', 'Viewed user dashboard')
    return jsonify({
        'profile': {'email': email, 'name': session.get('user_name')},
        'summary': db.get_user_dashboard_summary(email),
        'articles': db.get_recent_articles(limit=8),
        'programs': db.get_active_programs(limit=6),
    })


@app.route('/api/user/activity')
@user_required
def get_user_activity_log():
    email = session.get('user_email')
    limit = request.args.get('limit', 50, type=int)
    db.log_user_activity(email, 'activity_view', 'Viewed activity log')
    return jsonify({
        'activity': db.get_user_activity_log(email, limit),
        'stats': db.get_user_activity_stats(email),
    })


@app.route('/api/user/programs')
@user_required
def get_user_programs():
    email = session.get('user_email')
    db.log_user_activity(email, 'programs_view', 'Viewed student programs')
    return jsonify(db.get_active_programs(limit=20))


@app.route('/api/user/daily-progress')
@user_required
def get_user_daily_progress():
    email = session.get('user_email')
    db.log_user_activity(email, 'progress_view', 'Viewed daily progress')
    return jsonify(db.get_user_daily_progress(email))


@app.route('/api/user/weekly-summary')
@user_required
def get_user_weekly_summary():
    email = session.get('user_email')
    return jsonify(db.get_user_weekly_summary(email))


# â”€â”€ Admin dashboard API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route('/api/statistics')
def get_statistics():
    return jsonify(db.get_statistics())


@app.route('/api/dashboard-overview')
@admin_required
def get_dashboard_overview():
    return jsonify({'stats': db.get_statistics(), 'activity': db.get_recent_user_activity(limit=12),
                    'admin_stats': db.get_admin_dashboard_stats()})


@app.route('/api/user-activity')
@admin_required
def get_user_activity():
    return jsonify(db.get_recent_user_activity(limit=20))


@app.route('/api/admin/users')
@admin_required
def admin_get_all_users():
    return jsonify(db.get_all_users_with_stats())


@app.route('/api/admin/users/<email>/activity')
@admin_required
def admin_get_user_activity(email):
    limit = request.args.get('limit', 100, type=int)
    return jsonify({
        'user': db.get_user_by_email(email),
        'activity': db.get_user_full_activity(email, limit),
        'stats': db.get_user_activity_stats(email),
    })


@app.route('/api/admin/users/<email>/deactivate', methods=['POST'])
@admin_required
def admin_deactivate_user(email):
    success = db.deactivate_user(email)
    return jsonify({'status': 'success' if success else 'error',
                    'message': f'User {email} deactivated.' if success else 'User not found.'})


@app.route('/api/admin/contact-messages')
@admin_required
def admin_get_contact_messages():
    return jsonify(db.get_contact_messages(limit=50))


# â”€â”€ Student programs API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route('/api/programs')
def get_programs():
    return jsonify(db.get_active_programs(limit=20))


@app.route('/api/admin/programs')
@admin_required
def admin_get_programs():
    return jsonify(db.get_all_programs(limit=100))


@app.route('/api/admin/programs/add', methods=['POST'])
@admin_required
def admin_add_program():
    p = request.get_json() or {}
    title = (p.get('title') or '').strip()
    company = (p.get('company') or '').strip()
    description = (p.get('description') or '').strip()
    reg_url = (p.get('registration_url') or '').strip()
    if not title or not company or not reg_url:
        return jsonify({'status': 'error', 'message': 'Title, company, and registration URL are required.'}), 400
    prog_id = db.add_student_program(
        title=title, company=company, description=description,
        registration_url=reg_url,
        deadline=p.get('deadline') or None,
        launch_date=p.get('launch_date') or None,
        category=p.get('category') or 'program',
        notify_before_days=int(p.get('notify_before_days') or 7))
    return jsonify({'status': 'success', 'id': prog_id, 'message': f'Program "{title}" added successfully.'})


@app.route('/api/admin/programs/<int:prog_id>/delete', methods=['POST'])
@admin_required
def admin_delete_program(prog_id):
    success = db.delete_program(prog_id)
    return jsonify({'status': 'success' if success else 'error'})


@app.route('/api/admin/programs/notify-now', methods=['POST'])
@admin_required
def admin_send_program_notifications():
    try:
        from ai_news_agent import send_program_notifications
        count = send_program_notifications()
        return jsonify({'status': 'success', 'sent': count, 'message': f'Sent {count} program notification emails.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# â”€â”€ Articles API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route('/api/articles')
def get_articles():
    return jsonify(db.get_recent_articles(limit=request.args.get('limit', 50, type=int),
                                          days=request.args.get('days', type=int)))

@app.route('/api/articles/search')
def search_articles():
    q = request.args.get('q', '')
    if not q: return jsonify([])
    return jsonify(db.search_articles(q, request.args.get('limit', 50, type=int)))

@app.route('/api/articles/range')
def get_articles_by_range():
    start, end = request.args.get('start'), request.args.get('end')
    if not start or not end: return jsonify({'error': 'Start and end dates required'}), 400
    return jsonify(db.get_articles_by_date_range(start, end))


# â”€â”€ Admin control API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route('/api/email-logs')
@admin_required
def get_email_logs():
    return jsonify(db.get_email_logs(request.args.get('limit', 100, type=int)))

@app.route('/api/agent-logs')
@admin_required
def get_agent_logs():
    return jsonify(db.get_agent_logs(request.args.get('limit', 100, type=int)))

@app.route('/api/agent/run-now', methods=['POST'])
@admin_required
def run_agent_now():
    try:
        from ai_news_agent import run_news_digest
        success = run_news_digest()
        return jsonify({'status': 'success' if success else 'failed',
                        'message': 'News digest sent successfully.' if success else 'Failed to send digest.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/cleanup', methods=['POST'])
@admin_required
def cleanup_old_data():
    months = (request.json or {}).get('months', 3)
    deleted = db.cleanup_old_articles(months=months)
    return jsonify({'status': 'success', 'deleted_count': deleted})

@app.route('/api/recipients')
@admin_required
def get_recipients():
    try:
        with open(RECIPIENTS_FILE, 'r') as f: return jsonify(json.load(f).get('recipients', []))
    except FileNotFoundError: return jsonify([])
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/recipients/add', methods=['POST'])
@admin_required
def add_recipient():
    p = request.get_json(silent=True) or request.form.to_dict()
    email = (p.get('email') or '').strip().lower()
    if not email or '@' not in email: return jsonify({'error': 'Invalid email'}), 400
    try:
        with open(RECIPIENTS_FILE, 'r') as f: data = json.load(f)
    except Exception: data = {'recipients': []}
    if email in data.get('recipients', []):
        return jsonify({'status': 'already_exists', 'message': 'Email already exists'}), 200
    data.setdefault('recipients', []).append(email)
    with open(RECIPIENTS_FILE, 'w') as f: json.dump(data, f, indent=2)
    db.register_user(email, p.get('name') or None)
    return jsonify({'status': 'success', 'recipients': data['recipients']})

@app.route('/api/recipients/remove', methods=['POST'])
@admin_required
def remove_recipient():
    email = (request.json or {}).get('email')
    try:
        with open(RECIPIENTS_FILE, 'r') as f: data = json.load(f)
        if email in data['recipients']:
            data['recipients'].remove(email)
            with open(RECIPIENTS_FILE, 'w') as f: json.dump(data, f, indent=2)
            return jsonify({'status': 'success', 'recipients': data['recipients']})
        return jsonify({'error': 'Email not found'}), 404
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/config')
@admin_required
def get_config():
    return jsonify({'recipient_email': os.getenv('RECIPIENT_EMAIL'),
                    'sender_email': os.getenv('GMAIL_USER') or os.getenv('EMAIL_USER'),
                    'has_newsapi_key': bool(os.getenv('NEWSAPI_KEY')),
                    'schedule_time': '8:00 AM daily'})

@app.route('/api/subscribe', methods=['POST'])
def subscribe_public():
    p = request.get_json(silent=True) or request.form.to_dict()
    email = (p.get('email') or '').strip().lower()
    name = (p.get('name') or '').strip()
    if not email or '@' not in email:
        return jsonify({'status': 'error', 'message': 'Please enter a valid email address.'}), 400
    try:
        with open(RECIPIENTS_FILE, 'r') as f: data = json.load(f)
    except Exception: data = {'recipients': []}
    already = email in data.get('recipients', [])
    if not already:
        data.setdefault('recipients', []).append(email)
        with open(RECIPIENTS_FILE, 'w') as f: json.dump(data, f, indent=2)
    db.register_user(email, name or None)
    db.record_user_login(email, 'subscription')
    welcome_sent = False
    if not already:
        try:
            from ai_news_agent import send_welcome_email
            welcome_sent = send_welcome_email(email)
        except Exception: pass
    return jsonify({'status': 'success', 'message': 'You are subscribed.' if not already else 'Already subscribed.',
                    'already_registered': already, 'welcome_email_sent': welcome_sent})


@app.route('/api/contact', methods=['POST'])
def handle_contact():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    subject = (data.get('subject') or '').strip()
    message = (data.get('message') or '').strip()
    if not all([name, email, subject, message]) or '@' not in email:
        return jsonify({'status': 'error', 'message': 'All fields are required.'}), 400
    try:
        db.record_contact_message(name, email, subject, message)
        try:
            from ai_news_agent import send_contact_notification_email
            send_contact_notification_email(name, email, subject, message)
        except Exception: pass
        return jsonify({'status': 'success', 'message': "Thank you! We'll get back to you shortly."})
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to process your message.'}), 500


@app.route('/sitemap.xml')
def sitemap():
    domain = 'novabrief.tech' if 'novabrief.tech' in request.host_url else request.host_url.strip('/')
    domain_url = f"https://{domain}" if not domain.startswith('http') else domain
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>{domain_url}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>
<url><loc>{domain_url}/privacy</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>
<url><loc>{domain_url}/terms</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>
</urlset>''', 200, {'Content-Type': 'application/xml'}


@app.route('/robots.txt')
def robots():
    domain = 'novabrief.tech' if 'novabrief.tech' in request.host_url else request.host_url.strip('/')
    domain_url = f"https://{domain}" if not domain.startswith('http') else domain
    return f'User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /dashboard\nSitemap: {domain_url}/sitemap.xml', 200, {'Content-Type': 'text/plain'}


@app.route('/ads.txt')
def adstxt():
    return 'google.com, pub-1036052096443002, DIRECT, f08c47fec0942fa0', 200, {'Content-Type': 'text/plain'}


@app.route('/api/admin/ping-google', methods=['POST'])
@admin_required
def ping_google():
    """Use REST API in the backend to ping Google to index the website."""
    try:
        import requests
        domain = 'novabrief.tech' if 'novabrief.tech' in request.host_url else request.host_url.strip('/')
        domain_url = f"https://{domain}" if not domain.startswith('http') else domain
        sitemap_url = f'{domain_url}/sitemap.xml'
        google_ping_url = f'https://www.google.com/ping?sitemap={sitemap_url}'
        response = requests.get(google_ping_url)
        if response.status_code == 200:
            return jsonify({'status': 'success', 'message': 'Successfully pinged Google! The website will be indexed.'})
        else:
            return jsonify({'status': 'error', 'message': f'Failed to ping Google. Status: {response.status_code}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


@app.errorhandler(404)
def not_found(e): return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def server_error(e): logger.error(f'Server error: {e}'); return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'\n{"="*60}\nNova Brief â€” running at http://0.0.0.0:{port}\n{"="*60}\n')
    app.run(debug=os.environ.get('FLASK_ENV') == 'development', host='0.0.0.0', port=port)



