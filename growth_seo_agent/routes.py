from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from functools import wraps

seo_bp = Blueprint('seo', __name__, template_folder='templates')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('admin_login_page'))
        return f(*args, **kwargs)
    return decorated_function

@seo_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('seo_dashboard.html')

@seo_bp.route('/keywords')
@admin_required
def keywords():
    return render_template('seo_keywords.html')

@seo_bp.route('/content')
@admin_required
def content_assistant():
    return render_template('seo_content.html')

