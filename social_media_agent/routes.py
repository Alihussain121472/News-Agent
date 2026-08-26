from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from functools import wraps
from database import NewsDatabase, safe_connect

social_bp = Blueprint('social', __name__, template_folder='templates')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('admin_login_page'))
        return f(*args, **kwargs)
    return decorated_function

@social_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('social_dashboard.html')

@social_bp.route('/campaigns')
@admin_required
def campaigns():
    return render_template('social_calendar.html')

def init_social_db():
    conn = safe_connect()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS social_campaigns (
        id SERIAL PRIMARY KEY,
        platform TEXT, content TEXT, scheduled_for TIMESTAMP,
        status TEXT DEFAULT 'pending'
    )''')
    conn.commit()
    conn.close()

try:
    init_social_db()
except Exception: pass
