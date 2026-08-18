from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from database import NewsDatabase
from datetime import datetime, timedelta
import os
import logging
import json
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-this-secret-key')

ADMIN_EMAIL = (os.getenv('ADMIN_EMAIL') or 'admin@novabrief.local').strip().lower()
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD') or 'change-me-now'

logger = logging.getLogger(__name__)
db = NewsDatabase()


def _is_api_request() -> bool:
    return request.path.startswith('/api/')


def _json_unauthorized(message: str, status_code: int = 401):
    return jsonify({'status': 'error', 'message': message}), status_code


def _login_redirect_for_role(role: str):
    if role == 'admin':
        return redirect(url_for('admin_login_page'))
    return redirect(url_for('user_login_page'))


def role_required(required_role: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_role = session.get('role')

            if not current_role:
                if _is_api_request():
                    return _json_unauthorized('Please log in first.', 401)
                return _login_redirect_for_role(required_role)

            if current_role != required_role:
                if _is_api_request():
                    return _json_unauthorized('Access denied.', 403)

                # Block admin dashboard access for users.
                if current_role == 'user':
                    return redirect(url_for('user_dashboard'))
                return redirect(url_for('dashboard'))

            return func(*args, **kwargs)

        return wrapper

    return decorator


user_required = role_required('user')
admin_required = role_required('admin')


@app.before_request
def track_visitor():
    """Log anonymous site visits for traffic analytics."""
    if request.path.startswith('/static'):
        return
    if request.path.startswith('/api'):
        return
    try:
        db.record_site_visit(
            page=request.path,
            ip_address=request.remote_addr or 'unknown',
            user_agent=request.user_agent.string[:250],
            email=session.get('user_email'),
        )
    except Exception:
        pass

# Get the absolute path to the recipients.json file
RECIPIENTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recipients.json')


@app.route('/')
def index():
    """Public landing page for new subscribers."""
    return render_template('index.html')


@app.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard for monitoring and managing the news agent."""
    try:
        db.record_user_login('admin@local', 'dashboard_view')
    except Exception:
        pass
    return render_template('dashboard.html')


@app.route('/user/dashboard')
@user_required
def user_dashboard():
    """User dashboard for registered users."""
    return render_template('user_dashboard.html', user_name=session.get('user_name'), user_email=session.get('user_email'))


@app.route('/user/login')
def user_login_page():
    """User login screen."""
    if session.get('role') == 'user':
        return redirect(url_for('user_dashboard'))
    return render_template('user_login.html')


@app.route('/user/register')
def user_register_page():
    """User registration screen."""
    if session.get('role') == 'user':
        return redirect(url_for('user_dashboard'))
    return render_template('user_register.html')


@app.route('/admin/login')
def admin_login_page():
    """Admin login screen."""
    if session.get('role') == 'admin':
        return redirect(url_for('dashboard'))
    return render_template('admin_login.html')


def _safe_add_recipient(email: str):
    """Ensure registered user is also in recipients list for daily emails."""
    try:
        with open(RECIPIENTS_FILE, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {'recipients': []}

    recipients = data.setdefault('recipients', [])
    if email not in recipients:
        recipients.append(email)
        with open(RECIPIENTS_FILE, 'w') as f:
            json.dump(data, f, indent=2)


@app.route('/api/auth/register', methods=['POST'])
def register_user_account():
    """Register a new user account with password for dashboard access."""
    payload = request.get_json(silent=True) or request.form.to_dict()
    name = (payload.get('name') or '').strip()
    email = (payload.get('email') or '').strip().lower()
    password = payload.get('password') or ''

    if not name or not email or '@' not in email or len(password) < 6:
        return jsonify({'status': 'error', 'message': 'Name, valid email, and password (min 6 chars) are required.'}), 400

    password_hash = generate_password_hash(password)
    result = db.create_or_update_user_account(email=email, name=name, password_hash=password_hash)
    _safe_add_recipient(email)

    session['user_email'] = email
    session['user_name'] = name
    session['role'] = 'user'
    db.record_user_login(email, 'user_login')

    if result == 'created':
        message = 'Account created successfully.'
    elif result == 'updated':
        message = 'Account activated with a new password.'
    else:
        message = 'This account already has a password. Please login.'
        return jsonify({'status': 'error', 'message': message}), 409

    return jsonify({'status': 'success', 'message': message, 'redirect': '/user/dashboard'})


@app.route('/api/auth/login', methods=['POST'])
def login_user_account():
    """Authenticate standard user and start session."""
    payload = request.get_json(silent=True) or request.form.to_dict()
    email = (payload.get('email') or '').strip().lower()
    password = payload.get('password') or ''

    user = db.get_user_by_email(email)
    if not user or not user.get('password_hash'):
        return jsonify({'status': 'error', 'message': 'Account not found. Please register first.'}), 404

    if not check_password_hash(user['password_hash'], password):
        return jsonify({'status': 'error', 'message': 'Invalid email or password.'}), 401

    session['user_email'] = user['email']
    session['user_name'] = user.get('name') or 'User'
    session['role'] = 'user'
    db.record_user_login(user['email'], 'user_login')

    return jsonify({'status': 'success', 'message': 'Logged in successfully.', 'redirect': '/user/dashboard'})


@app.route('/api/auth/admin/login', methods=['POST'])
def login_admin_account():
    """Authenticate admin and start admin session."""
    payload = request.get_json(silent=True) or request.form.to_dict()
    email = (payload.get('email') or '').strip().lower()
    password = payload.get('password') or ''

    if email != ADMIN_EMAIL or password != ADMIN_PASSWORD:
        return jsonify({'status': 'error', 'message': 'Invalid admin credentials.'}), 401

    session['user_email'] = ADMIN_EMAIL
    session['user_name'] = 'Administrator'
    session['role'] = 'admin'
    db.record_user_login(ADMIN_EMAIL, 'admin_login')

    return jsonify({'status': 'success', 'message': 'Admin login successful.', 'redirect': '/dashboard'})


@app.route('/api/auth/me')
def current_session_user():
    """Return current authenticated session user."""
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
    """Destroy current session for both user and admin."""
    session.clear()
    return jsonify({'status': 'success', 'redirect': '/'})


@app.route('/api/user/overview')
@user_required
def get_user_overview():
    """User-facing dashboard summary."""
    email = session.get('user_email')
    summary = db.get_user_dashboard_summary(email)
    recent_articles = db.get_recent_articles(limit=8)

    return jsonify({
        'profile': {
            'email': email,
            'name': session.get('user_name')
        },
        'summary': summary,
        'articles': recent_articles
    })


@app.route('/api/statistics')
def get_statistics():
    """Get database statistics."""
    stats = db.get_statistics()
    return jsonify(stats)


@app.route('/api/dashboard-overview')
@admin_required
def get_dashboard_overview():
    """Combined dashboard metrics for the admin portal."""
    return jsonify({
        'stats': db.get_statistics(),
        'activity': db.get_recent_user_activity(limit=12)
    })


@app.route('/api/user-activity')
@admin_required
def get_user_activity():
    """Recent user and site activity."""
    return jsonify(db.get_recent_user_activity(limit=12))


@app.route('/api/articles')
def get_articles():
    """Get recent articles with optional filters."""
    limit = request.args.get('limit', 50, type=int)
    days = request.args.get('days', type=int)

    articles = db.get_recent_articles(limit=limit, days=days)
    return jsonify(articles)


@app.route('/api/articles/search')
def search_articles():
    """Search articles by query."""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 50, type=int)

    if not query:
        return jsonify([])

    articles = db.search_articles(query, limit=limit)
    return jsonify(articles)


@app.route('/api/articles/range')
def get_articles_by_range():
    """Get articles within a date range."""
    start = request.args.get('start')
    end = request.args.get('end')

    if not start or not end:
        return jsonify({'error': 'Start and end dates required'}), 400

    articles = db.get_articles_by_date_range(start, end)
    return jsonify(articles)


@app.route('/api/email-logs')
@admin_required
def get_email_logs():
    """Get email sending history."""
    limit = request.args.get('limit', 100, type=int)
    logs = db.get_email_logs(limit=limit)
    return jsonify(logs)


@app.route('/api/agent-logs')
@admin_required
def get_agent_logs():
    """Get agent activity logs."""
    limit = request.args.get('limit', 100, type=int)
    logs = db.get_agent_logs(limit=limit)
    return jsonify(logs)


@app.route('/api/agent/run-now', methods=['POST'])
@admin_required
def run_agent_now():
    """Trigger agent to run immediately."""
    try:
        from ai_news_agent import run_news_digest
        success = run_news_digest()
        return jsonify({
            'status': 'success' if success else 'failed',
            'message': 'News digest sent successfully' if success else 'Failed to send digest'
        })
    except Exception as e:
        logger.error(f'Error running agent: {e}')
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/cleanup', methods=['POST'])
@admin_required
def cleanup_old_data():
    """Manually trigger cleanup of old articles."""
    months = request.json.get('months', 3)
    deleted = db.cleanup_old_articles(months=months)
    return jsonify({
        'status': 'success',
        'deleted_count': deleted
    })


@app.route('/api/recipients')
@admin_required
def get_recipients():
    """Get list of recipient emails."""
    try:
        with open(RECIPIENTS_FILE, 'r') as f:
            data = json.load(f)
            return jsonify(data.get('recipients', []))
    except FileNotFoundError:
        return jsonify([os.getenv('RECIPIENT_EMAIL')])
    except Exception as e:
        logger.error(f'Error loading recipients: {e}')
        return jsonify({'error': str(e)}), 500


def _get_subscribe_payload():
    """Support JSON and form-based signups for public-facing registration."""
    payload = request.get_json(silent=True) or {}
    if payload:
        return payload
    return request.form.to_dict()


@app.route('/api/subscribe', methods=['POST'])
def subscribe_public():
    """Public signup endpoint for website visitors."""
    payload = _get_subscribe_payload()
    email = (payload.get('email') or '').strip().lower()
    name = (payload.get('name') or '').strip()

    if not email or '@' not in email:
        return jsonify({'status': 'error', 'message': 'Please enter a valid email address.'}), 400

    try:
        with open(RECIPIENTS_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {'recipients': []}
    except json.JSONDecodeError:
        data = {'recipients': []}

    already_registered = email in data.get('recipients', [])
    if not already_registered:
        data.setdefault('recipients', []).append(email)
        with open(RECIPIENTS_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    try:
        from ai_news_agent import send_welcome_email
        db = NewsDatabase()
        db.register_user(email, name or None)
        db.record_user_login(email, 'subscription')
        welcome_email_sent = send_welcome_email(email) if not already_registered else False
    except Exception as e:
        logger.error(f'Error handling public signup for {email}: {e}')
        welcome_email_sent = False

    logger.info(f'Public signup: {email} | already_registered={already_registered} | welcome_email_sent={welcome_email_sent}')
    return jsonify({
        'status': 'success' if not already_registered or welcome_email_sent else 'ok',
        'message': 'You are subscribed.' if not already_registered else 'This email is already subscribed.',
        'already_registered': already_registered,
        'welcome_email_sent': welcome_email_sent,
        'recipients': data.get('recipients', [])
    })


@app.route('/api/recipients/add', methods=['POST'])
@admin_required
def add_recipient():
    """Add a new recipient email and send a welcome email when possible."""
    payload = _get_subscribe_payload()
    email = (payload.get('email') or '').strip().lower()
    name = (payload.get('name') or '').strip()

    if not email or '@' not in email:
        return jsonify({'error': 'Invalid email address'}), 400

    try:
        with open(RECIPIENTS_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {'recipients': []}
    except json.JSONDecodeError:
        data = {'recipients': []}

    if email in data.get('recipients', []):
        return jsonify({'status': 'already_exists', 'message': 'Email already exists'}), 200

    data.setdefault('recipients', []).append(email)
    with open(RECIPIENTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    try:
        from ai_news_agent import send_welcome_email
        db = NewsDatabase()
        db.register_user(email, name or None)
        db.record_user_login(email, 'subscription')
        welcome_email_sent = send_welcome_email(email)
    except Exception as e:
        logger.error(f'Error sending welcome email for {email}: {e}')
        welcome_email_sent = False

    logger.info(f'Added recipient: {email} | Welcome email sent: {welcome_email_sent}')
    return jsonify({
        'status': 'success',
        'recipients': data['recipients'],
        'welcome_email_sent': welcome_email_sent
    })


@app.route('/api/recipients/remove', methods=['POST'])
@admin_required
def remove_recipient():
    """Remove a recipient email."""
    try:
        email = request.json.get('email')

        try:
            with open(RECIPIENTS_FILE, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            return jsonify({'error': 'No recipients file found'}), 404

        if email in data['recipients']:
            data['recipients'].remove(email)
            with open(RECIPIENTS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f'Removed recipient: {email}')
            return jsonify({'status': 'success', 'recipients': data['recipients']})
        else:
            return jsonify({'error': 'Email not found'}), 404
    except Exception as e:
        logger.error(f'Error removing recipient: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/config')
@admin_required
def get_config():
    """Get current agent configuration."""
    config = {
        'recipient_email': os.getenv('RECIPIENT_EMAIL'),
        'sender_email': os.getenv('GMAIL_USER') or os.getenv('EMAIL_USER'),
        'has_newsapi_key': bool(os.getenv('NEWSAPI_KEY')),
        'schedule_time': '8:03 AM daily'
    }
    return jsonify(config)


@app.route('/api/contact', methods=['POST'])
def handle_contact():
    """Handle contact form submissions."""
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    subject = (data.get('subject') or '').strip()
    message = (data.get('message') or '').strip()

    if not all([name, email, subject, message]):
        return jsonify({'status': 'error', 'message': 'All fields are required'}), 400

    if '@' not in email:
        return jsonify({'status': 'error', 'message': 'Invalid email address'}), 400

    try:
        # Log contact message to database
        db.record_contact_message(name, email, subject, message)
        
        # Try to send email notification (if configured)
        try:
            from ai_news_agent import send_contact_notification_email
            send_contact_notification_email(name, email, subject, message)
        except Exception as e:
            logger.warning(f'Could not send contact notification email: {e}')
        
        logger.info(f'Contact form submitted: {name} ({email}) - Subject: {subject}')
        return jsonify({
            'status': 'success',
            'message': 'Thank you for your message! We\'ll get back to you shortly.'
        })
    except Exception as e:
        logger.error(f'Error handling contact form: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to process your message'}), 500


@app.route('/privacy')
def privacy():
    """Privacy Policy page."""
    return render_template('privacy.html')


@app.route('/terms')
def terms():
    """Terms of Service page."""
    return render_template('terms.html')


@app.route('/cookies')
def cookies():
    """Cookie Policy page."""
    return render_template('cookies.html')


@app.route('/sitemap.xml')
def sitemap():
    """XML sitemap for SEO."""
    response = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://novabrief.ai-news.app/</loc>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://novabrief.ai-news.app/dashboard</loc>
        <changefreq>daily</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://novabrief.ai-news.app/privacy</loc>
        <changefreq>monthly</changefreq>
        <priority>0.5</priority>
    </url>
    <url>
        <loc>https://novabrief.ai-news.app/terms</loc>
        <changefreq>monthly</changefreq>
        <priority>0.5</priority>
    </url>
</urlset>'''
    return response, 200, {'Content-Type': 'application/xml'}


@app.route('/robots.txt')
def robots():
    """Robots.txt for search engines."""
    response = '''User-agent: *
Allow: /
Disallow: /api/
Disallow: /dashboard
Sitemap: https://novabrief.ai-news.app/sitemap.xml'''
    return response, 200, {'Content-Type': 'text/plain'}


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Page not found'}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f'Server error: {error}')
    return jsonify({'error': 'Internal server error'}), 500



if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))

    print('=' * 60)
    print('Nova Brief')
    print('=' * 60)
    print(f'Dashboard running at: http://0.0.0.0:{port}')
    print('Press CTRL+C to stop')
    print('=' * 60)

    # Use debug=False in production
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
