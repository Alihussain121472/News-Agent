from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from functools import wraps
import json

analytics_bp = Blueprint('analytics', __name__, template_folder='templates')

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_email'):
            return redirect(url_for('user_login_page'))
        return f(*args, **kwargs)
    return decorated_function

@analytics_bp.route('/dashboard')
@user_required
def dashboard():
    return render_template('analytics_dashboard.html')

@analytics_bp.route('/revenue')
@user_required
def revenue():
    return render_template('analytics_revenue.html')

@analytics_bp.route('/reports')
@user_required
def reports():
    return render_template('analytics_reports.html')

@analytics_bp.route('/api/stats')
@user_required
def get_stats():
    # Return mock stats for the charts
    return jsonify({
        'traffic': {'today': 1250, 'growth': 12},
        'revenue': {'today': 340.50, 'growth': 8},
        'leads': {'today': 45, 'growth': 5}
    })
