from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from functools import wraps

social_bp = Blueprint('social', __name__, template_folder='templates')

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_email'):
            return redirect(url_for('user_login_page'))
        return f(*args, **kwargs)
    return decorated_function

@social_bp.route('/dashboard')
@user_required
def dashboard():
    return render_template('social_dashboard.html')

@social_bp.route('/calendar')
@user_required
def calendar():
    return render_template('social_calendar.html')

@social_bp.route('/campaigns')
@user_required
def campaigns():
    return render_template('social_campaigns.html')
