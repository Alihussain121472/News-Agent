# Import Flask and necessary libraries to build the web server
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from database import NewsDatabase
from datetime import datetime
import os, logging, json, threading
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
# Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'nova-brief-secret-key-2026')

try:
    from growth_seo_agent.routes import seo_bp
    app.register_blueprint(seo_bp, url_prefix='/seo')
except Exception: pass

try:
    from social_media_agent.routes import social_bp
    app.register_blueprint(social_bp, url_prefix='/social')
except Exception: pass

try:
    from analytics_revenue_portal.routes import analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
except Exception: pass


ADMIN_EMAIL = (os.getenv('ADMIN_EMAIL') or 'admin@novabrief.local').strip().lower()
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD') or 'NovaBriefAdmin2026!'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Connect to our local SQLite database (where all user data is stored)
db = NewsDatabase()

RECIPIENTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recipients.json')
if not os.path.exists(RECIPIENTS_FILE):
    try:
        with open(RECIPIENTS_FILE, 'w') as _f:
            json.dump({'recipients': []}, _f)
    except Exception: pass


# â”€â”€ Auth Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
        with open(RECIPIENTS_FILE, 'r') as f:
            data = json.load(f)
    except Exception:
        data = {'recipients': []}
    if email not in data.setdefault('recipients', []):
        data['recipients'].append(email)
        with open(RECIPIENTS_FILE, 'w') as f:
            json.dump(data, f, indent=2)


# â”€â”€ Page Routes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# This is the main homepage route. When someone visits our website, this runs.
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
    return render_template('user_dashboard.html')

@app.route('/user/login')
def user_login_page():
    if session.get('role') == 'user':
        return redirect(url_for('user_dashboard'))
    return render_template('user_login.html')

@app.route('/user/register')
def user_register_page():
    if session.get('role') == 'user':
        return redirect(url_for('user_dashboard'))
    return render_template('user_register.html')

@app.route('/admin/login')
def admin_login_page():
    if session.get('role') == 'admin':
        return redirect(url_for('dashboard'))
    return render_template('admin_login.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/cookies')
def cookies():
    return render_template('cookies.html')


# â”€â”€ Auth API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# Handle new user registrations. We receive their email and password here.
@app.route('/api/auth/register', methods=['POST'])
def register_user_account():
    p = request.get_json(silent=True) or request.form.to_dict()
    name = (p.get('name') or '').strip()
    email = (p.get('email') or '').strip().lower()
    password = p.get('password') or ''
    if not email or '@' not in email:
        return jsonify({'status': 'error', 'message': 'Please enter a valid email address.'}), 400
    if not name:
        name = email.split('@')[0].replace('.', ' ').title()
    
    pwd_hash = generate_password_hash(password) if password and len(password) >= 4 else None
    result = db.create_or_update_user_account(email, name, pwd_hash)
    _safe_add_recipient(email)
    session.update({'user_email': email, 'user_name': name, 'role': 'user'})
    db.record_user_login(email, 'register')
    db.log_user_activity(email, 'account_created', f'Registered as {name}')
    
    # Asynchronously dispatch welcome email
    try:
        from ai_news_agent import send_welcome_email
        threading.Thread(target=send_welcome_email, args=(email, name), daemon=True).start()
    except Exception as e:
        logger.error(f'Error triggering welcome email: {e}')
        
    return jsonify({
        'status': 'success',
        'message': 'Welcome to Nova Brief! Your account is active and a welcome email is on the way.',
        'redirect': '/user/dashboard'
    })


# Handle user login. We check if the password matches the one in our database.
@app.route('/api/auth/login', methods=['POST'])
def login_user_account():
    p = request.get_json(silent=True) or request.form.to_dict()
    email = (p.get('email') or '').strip().lower()
    password = p.get('password') or ''
    if not email or '@' not in email:
        return jsonify({'status': 'error', 'message': 'Please enter a valid email address.'}), 400
    
    user = db.get_user_by_email(email)
    if not user:
        name = email.split('@')[0].replace('.', ' ').title()
        pwd_hash = generate_password_hash(password) if password and len(password) >= 4 else None
        db.create_or_update_user_account(email, name, pwd_hash)
        _safe_add_recipient(email)
        user = db.get_user_by_email(email)
        try:
            from ai_news_agent import send_welcome_email
            threading.Thread(target=send_welcome_email, args=(email, name), daemon=True).start()
        except Exception: pass
    elif user.get('password_hash') and password:
        if not check_password_hash(user['password_hash'], password):
            return jsonify({'status': 'error', 'message': 'Invalid password. You can also sign in with just your email.'}), 401
    
    user_name = user.get('name') or email.split('@')[0].title()
    session.update({'user_email': user['email'], 'user_name': user_name, 'role': 'user'})
    db.record_user_login(email, 'user_login')
    db.log_user_activity(email, 'login', 'User logged in')
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
    if not session.get('role'):
        return jsonify({'authenticated': False})
    return jsonify({
        'authenticated': True,
        'email': session.get('user_email'),
        'name': session.get('user_name'),
        'role': session.get('role')
    })


@app.route('/api/auth/logout', methods=['POST'])
def logout_account():
    if session.get('user_email') and session.get('role') == 'user':
        try:
            db.log_user_activity(session['user_email'], 'logout', 'User logged out')
        except Exception: pass
    session.clear()
    return jsonify({'status': 'success', 'redirect': '/'})


# â”€â”€ User Dashboard API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


# â”€â”€ Admin Dashboard API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route('/api/statistics')
def get_statistics():
    return jsonify(db.get_statistics())


@app.route('/api/dashboard-overview')
@admin_required
def get_dashboard_overview():
    stats = db.get_statistics()
    recent_emails = db.get_recent_email_logs(limit=10)
    agent_logs = db.get_recent_agent_logs(limit=10)
    top_actions = db.get_top_actions_platform(limit=5)
    return jsonify({
        'stats': stats,
        'recent_emails': recent_emails,
        'agent_logs': agent_logs,
        'top_actions': top_actions
    })


@app.route('/api/admin/users-monitor')
@admin_required
def get_users_monitor():
    users = db.get_all_users_with_stats()
    return jsonify({'users': users, 'total': len(users)})


@app.route('/api/admin/user/<email>')
@admin_required
def get_user_detail(email):
    detail = db.get_user_activity_detail(email)
    if not detail:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(detail)


@app.route('/api/admin/recent-articles')
@admin_required
def get_admin_articles():
    limit = request.args.get('limit', 20, type=int)
    return jsonify(db.get_recent_articles(limit=limit))


@app.route('/api/admin/programs')
@admin_required
def get_admin_programs():
    return jsonify(db.get_all_programs())


@app.route('/api/admin/programs/add', methods=['POST'])
@admin_required
def add_program():
    p = request.get_json(silent=True) or request.form.to_dict()
    title = (p.get('title') or '').strip()
    company = (p.get('company') or '').strip()
    if not title or not company:
        return jsonify({'error': 'Title and Company are required'}), 400
    prog_id = db.add_student_program(
        title=title, company=company,
        description=p.get('description', ''),
        registration_url=p.get('registration_url', ''),
        deadline=p.get('deadline') or None,
        launch_date=p.get('launch_date') or None,
        category=p.get('category', 'program'),
        notify_before_days=int(p.get('notify_before_days', 7))
    )
    return jsonify({'status': 'success', 'program_id': prog_id, 'message': 'Program added successfully.'})


@app.route('/api/admin/programs/<int:prog_id>/toggle', methods=['POST'])
@admin_required
def toggle_program(prog_id):
    p = request.get_json() or {}
    active = int(p.get('is_active', 1))
    db.toggle_program_active(prog_id, active)
    return jsonify({'status': 'success'})


@app.route('/api/admin/programs/<int:prog_id>', methods=['DELETE'])
@admin_required
def delete_program(prog_id):
    db.delete_program(prog_id)
    return jsonify({'status': 'success'})


@app.route('/api/admin/programs/send-notifications', methods=['POST'])
@admin_required
def trigger_program_notifications():
    try:
        from ai_news_agent import send_program_notifications
        sent = send_program_notifications()
        return jsonify({'status': 'success', 'sent_count': sent, 'message': f'Sent {sent} notification emails.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/articles')
def get_articles():
    limit = request.args.get('limit', 20, type=int)
    return jsonify(db.get_recent_articles(limit=limit))


@app.route('/api/email-logs')
@admin_required
def get_email_logs():
    limit = request.args.get('limit', 50, type=int)
    return jsonify(db.get_recent_email_logs(limit=limit))


@app.route('/api/agent-logs')
@admin_required
def get_agent_logs():
    limit = request.args.get('limit', 50, type=int)
    return jsonify(db.get_recent_agent_logs(limit=limit))


@app.route('/api/contact-messages')
@admin_required
def get_contact_messages():
    limit = request.args.get('limit', 50, type=int)
    return jsonify(db.get_contact_messages(limit=limit))


@app.route('/api/recipients')
@admin_required
def get_recipients():
    try:
        with open(RECIPIENTS_FILE, 'r') as f:
            data = json.load(f)
    except Exception:
        data = {'recipients': []}
    return jsonify(data)


@app.route('/api/recipients/add', methods=['POST'])
@admin_required
def add_recipient():
    p = request.json or {}
    email = (p.get('email') or '').strip().lower()
    if not email or '@' not in email:
        return jsonify({'error': 'Invalid email'}), 400
    try:
        with open(RECIPIENTS_FILE, 'r') as f:
            data = json.load(f)
    except Exception:
        data = {'recipients': []}
    if email in data.get('recipients', []):
        return jsonify({'status': 'already_exists', 'message': 'Email already exists'}), 200
    data.setdefault('recipients', []).append(email)
    with open(RECIPIENTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    db.register_user(email, p.get('name') or None)
    return jsonify({'status': 'success', 'recipients': data['recipients']})


@app.route('/api/recipients/remove', methods=['POST'])
@admin_required
def remove_recipient():
    email = (request.json or {}).get('email')
    try:
        with open(RECIPIENTS_FILE, 'r') as f:
            data = json.load(f)
        if email in data['recipients']:
            data['recipients'].remove(email)
            with open(RECIPIENTS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            return jsonify({'status': 'success', 'recipients': data['recipients']})
        return jsonify({'error': 'Email not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config')
@admin_required
def get_config():
    return jsonify({
        'recipient_email': os.getenv('RECIPIENT_EMAIL'),
        'sender_email': os.getenv('GMAIL_USER') or os.getenv('EMAIL_USER'),
        'has_newsapi_key': bool(os.getenv('NEWSAPI_KEY')),
        'schedule_time': '8:00 AM daily'
    })


# â”€â”€ Public Subscribe & Contact â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route('/api/subscribe', methods=['POST'])
def subscribe_public():
    p = request.get_json(silent=True) or request.form.to_dict()
    email = (p.get('email') or '').strip().lower()
    name = (p.get('name') or '').strip()
    if not email or '@' not in email:
        return jsonify({'status': 'error', 'message': 'Please enter a valid email address.'}), 400
    if not name:
        name = email.split('@')[0].replace('.', ' ').title()
        
    _safe_add_recipient(email)
    db.create_or_update_user_account(email, name)
    db.record_user_login(email, 'subscription')
    session.update({'user_email': email, 'user_name': name, 'role': 'user'})
    
    # Asynchronously dispatch welcome email
    try:
        from ai_news_agent import send_welcome_email
        threading.Thread(target=send_welcome_email, args=(email, name), daemon=True).start()
    except Exception: pass
    
    return jsonify({
        'status': 'success',
        'message': f'Welcome, {name}! You are now subscribed and signed in. Check your inbox for the welcome briefing.',
        'already_registered': False,
        'welcome_email_sent': True,
        'redirect': '/user/dashboard'
    })


@app.route('/api/programs/join-alert', methods=['POST'])
def join_program_alert():
    p = request.get_json(silent=True) or request.form.to_dict()
    email = (p.get('email') or '').strip().lower()
    name = (p.get('name') or '').strip()
    program_title = (p.get('program_title') or p.get('program') or '').strip()
    if not email or '@' not in email:
        return jsonify({'status': 'error', 'message': 'Please enter a valid email address.'}), 400
    if not name:
        name = email.split('@')[0].replace('.', ' ').title()
    
    _safe_add_recipient(email)
    db.enable_user_program_notifications(email, name)
    db.record_user_login(email, 'program_alert_join')
    db.log_user_activity(email, 'joined_program_alerts', f'Joined alerts for {program_title or "all programs"}')
    session.update({'user_email': email, 'user_name': name, 'role': 'user'})
    
    # Asynchronously dispatch dedicated program welcome email
    try:
        from ai_news_agent import send_program_welcome_email
        threading.Thread(target=send_program_welcome_email, args=(email, name, program_title), daemon=True).start()
    except Exception as e:
        logger.error(f'Error sending program welcome email: {e}')
        
    return jsonify({
        'status': 'success',
        'message': f'Welcome, {name}! You have joined Student Program Alerts. We have sent a welcome email to {email}.',
        'welcome_email_sent': True,
        'redirect': '/user/dashboard'
    })


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
            threading.Thread(target=send_contact_notification_email, args=(name, email, subject, message), daemon=True).start()
        except Exception: pass
        return jsonify({'status': 'success', 'message': "Thank you! We'll get back to you shortly."})
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to process your message.'}), 500


# â”€â”€ SEO & Search Engine Endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# Provide a sitemap for Google and other search engines to discover our pages.
@app.route('/sitemap.xml')
def sitemap():
    domain = 'https://novabrief-web.onrender.com'
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>{domain}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>
<url><loc>{domain}/privacy</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>
<url><loc>{domain}/terms</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>
<url><loc>{domain}/cookies</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>
</urlset>''', 200, {'Content-Type': 'application/xml'}


@app.route('/robots.txt')
def robots():
    domain = 'https://novabrief-web.onrender.com'
    return f'User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /dashboard\nSitemap: {domain}/sitemap.xml', 200, {'Content-Type': 'text/plain'}


@app.route('/ads.txt')
def adstxt():
    return 'google.com, pub-1036052096443002, DIRECT, f08c47fec0942fa0', 200, {'Content-Type': 'text/plain'}


@app.route('/api/admin/ping-google', methods=['POST'])
@admin_required
def ping_google():
    try:
        import requests
        sitemap_url = 'https://novabrief-web.onrender.com/sitemap.xml'
        google_ping_url = f'https://www.google.com/ping?sitemap={sitemap_url}'
        response = requests.get(google_ping_url, timeout=10)
        return jsonify({'status': 'success', 'message': f'Google ping response code: {response.status_code}'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Resource not found'}), 404
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f'Server error: {e}')
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('index.html'), 500


# This starts the web server so people can access the website on the internet.
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'\n{"="*60}\nNova Brief â€” running at http://0.0.0.0:{port}\n{"="*60}\n')
    app.run(debug=os.environ.get('FLASK_ENV') == 'development', host='0.0.0.0', port=port)

