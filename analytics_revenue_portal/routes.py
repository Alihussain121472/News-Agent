from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from functools import wraps
from database import NewsDatabase
import sqlite3
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__, template_folder='templates')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('admin_login_page'))
        return f(*args, **kwargs)
    return decorated_function

@analytics_bp.route('/dashboard')
@admin_required
def dashboard():
    db = NewsDatabase()
    
    # Real data from database
    total_users = db.get_user_count()
    visitor_stats = db.get_visitor_stats()
    total_visitors = visitor_stats.get('total_visits', 0)
    monthly_visitors = visitor_stats.get('monthly_visits', 0)
    
    # Leads (contact messages)
    leads = len(db.get_contact_messages(limit=10000))
    
    return render_template('analytics_dashboard.html', 
        total_visitors=total_visitors,
        monthly_visitors=monthly_visitors,
        total_users=total_users,
        leads=leads,
        revenue=0.00
    )

@analytics_bp.route('/revenue')
@admin_required
def revenue():
    db = NewsDatabase()
    payout = db.get_payout_account()
    ad_stats = db.get_ad_stats()
    visitor_stats = db.get_visitor_stats()
    return render_template('analytics_revenue.html', payout=payout, ad_stats=ad_stats, visitor_stats=visitor_stats)


@analytics_bp.route('/api/payout-account', methods=['GET', 'POST'])
@admin_required
def payout_account_api():
    from flask import request
    db = NewsDatabase()
    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form.to_dict()
        name = (data.get('account_name') or '').strip()
        num = (data.get('account_number') or '').strip()
        bank = (data.get('bank_name') or '').strip()
        iban = (data.get('iban') or '').strip()
        if not name or not num or not bank:
            return jsonify({'status': 'error', 'message': 'Account name, number, and bank are required.'}), 400
        db.update_payout_account(name, num, bank, iban)
        return jsonify({'status': 'success', 'message': 'Payout account updated successfully.', 'payout': db.get_payout_account()})
    return jsonify(db.get_payout_account())


@analytics_bp.route('/api/track-ad-event', methods=['POST'])
def track_ad_event():
    from flask import request
    db = NewsDatabase()
    data = request.get_json(silent=True) or {}
    event_type = data.get('event_type') or 'impression'
    page = data.get('page') or request.referrer or '/'
    detail = data.get('detail') or 'Google AdSense ca-pub-1036052096443002'
    db.log_ad_event(event_type, page, request.remote_addr, detail)
    return jsonify({'status': 'ok'})

@analytics_bp.route('/reports')
@admin_required
def reports():
    return render_template('analytics_reports.html')

@analytics_bp.route('/api/stats')
@admin_required
def get_stats():
    # Return true historical data for charts
    db = NewsDatabase()
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    # Traffic last 7 days
    labels = []
    traffic_data = []
    revenue_data = []
    
    for i in range(6, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        labels.append(d)
        
        cursor.execute("SELECT COUNT(*) FROM site_visits WHERE date(visit_time) = ?", (d,))
        t = cursor.fetchone()[0]
        traffic_data.append(t)
        
        # Revenue is zero for now
        revenue_data.append(0)
        
    conn.close()
    
    return jsonify({
        'labels': labels,
        'traffic': traffic_data,
        'revenue': revenue_data
    })

@analytics_bp.route('/messages')
@admin_required
def messages():
    db = NewsDatabase()
    all_messages = db.get_contact_messages(limit=100)
    return render_template('messages.html', messages=all_messages)

@analytics_bp.route('/insights')
@admin_required
def insights():
    return render_template('analytics_insights.html')

@analytics_bp.route('/settings')
@admin_required
def settings():
    return render_template('analytics_settings.html')

@analytics_bp.route('/notifications')
@admin_required
def notifications():
    return render_template('analytics_notifications.html')
