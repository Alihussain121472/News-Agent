import base64
import hashlib
import hmac
import os
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import urlparse

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for
from markupsafe import escape

from database import NewsDatabase, safe_connect

from . import adsense_repository
from .adsense_service import (
    AdSenseError,
    build_authorization_url,
    connect_authorized_account,
    connection_status,
    exchange_code,
    revoke_and_disconnect,
    sync_connection,
)


analytics_bp = Blueprint('analytics', __name__, template_folder='templates')


def admin_required(handler):
    @wraps(handler)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            if request.path.startswith('/analytics/api/'):
                return jsonify({'status': 'error', 'message': 'Please log in as an admin first.'}), 401
            return redirect(url_for('admin_login_page'))
        return handler(*args, **kwargs)

    return decorated_function


def _same_origin():
    source = request.headers.get('Origin') or request.headers.get('Referer')
    if not source:
        return os.getenv('FLASK_ENV', 'development').strip().lower() != 'production'
    source_url = urlparse(source)
    app_url = urlparse(request.host_url)
    return source_url.scheme == app_url.scheme and source_url.netloc == app_url.netloc


def same_origin_required(handler):
    @wraps(handler)
    def decorated_function(*args, **kwargs):
        if not _same_origin():
            return jsonify({'status': 'error', 'message': 'This action must be started from Nova OS.'}), 403
        return handler(*args, **kwargs)

    return decorated_function


def _adsense_redirect_uri():
    configured = (os.getenv('GOOGLE_ADSENSE_REDIRECT_URI') or '').strip()
    return configured or url_for('analytics.adsense_callback', _external=True)


@analytics_bp.route('/dashboard')
@admin_required
def dashboard():
    db = NewsDatabase()
    visitor_stats = db.get_visitor_stats()
    revenue_data = adsense_repository.revenue_snapshot(30)
    return render_template(
        'analytics_dashboard.html',
        total_visitors=visitor_stats.get('total_visits', 0),
        monthly_visitors=visitor_stats.get('monthly_visits', 0),
        total_users=db.get_user_count(),
        leads=len(db.get_contact_messages(limit=10000)),
        revenue=revenue_data['month_earnings'],
    )


@analytics_bp.route('/revenue')
@admin_required
def revenue():
    db = NewsDatabase()
    status = connection_status()
    if status['connected']:
        sync_connection(force=False)
        status = connection_status()
    return render_template(
        'analytics_revenue.html',
        adsense=status,
        currency=(status['account'] or {}).get('currency_code') or 'USD',
        revenue_data=adsense_repository.revenue_snapshot(90),
        ad_stats=db.get_ad_stats(),
        visitor_stats=db.get_visitor_stats(),
    )


@analytics_bp.route('/adsense/connect')
@admin_required
def adsense_connect():
    if not connection_status()['configured']:
        return redirect(url_for('analytics.revenue', connection='setup_required'))
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode('ascii')).digest()).decode('ascii').rstrip('=')
    redirect_uri = _adsense_redirect_uri()
    session['adsense_oauth'] = {
        'state': state,
        'verifier': verifier,
        'redirect_uri': redirect_uri,
        'created_at': int(time.time()),
    }
    return redirect(build_authorization_url(redirect_uri, state, challenge))


@analytics_bp.route('/adsense/callback')
@admin_required
def adsense_callback():
    pending = session.pop('adsense_oauth', None) or {}
    state = request.args.get('state') or ''
    if request.args.get('error'):
        return redirect(url_for('analytics.revenue', connection='cancelled'))
    if (
        not pending
        or not hmac.compare_digest(state, pending.get('state') or '')
        or int(time.time()) - int(pending.get('created_at') or 0) > 600
    ):
        return redirect(url_for('analytics.revenue', connection='invalid_state'))
    code = request.args.get('code') or ''
    if not code:
        return redirect(url_for('analytics.revenue', connection='failed'))
    try:
        token_payload = exchange_code(code, pending['redirect_uri'], pending['verifier'])
        connect_authorized_account(token_payload)
        return redirect(url_for('analytics.revenue', connection='connected'))
    except AdSenseError:
        return redirect(url_for('analytics.revenue', connection='failed'))


@analytics_bp.route('/api/adsense/sync', methods=['POST'])
@admin_required
@same_origin_required
def sync_adsense():
    try:
        result = sync_connection(force=True)
        if result['status'] == 'disconnected':
            return jsonify({'status': 'error', 'message': 'Connect an AdSense account first.'}), 409
        return jsonify({'status': 'success', 'message': 'AdSense earnings refreshed.', 'result': result})
    except AdSenseError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 502


@analytics_bp.route('/api/adsense/disconnect', methods=['POST'])
@admin_required
@same_origin_required
def disconnect_adsense():
    if not revoke_and_disconnect():
        return jsonify({'status': 'error', 'message': 'No AdSense account is connected.'}), 404
    return jsonify({'status': 'success', 'message': 'AdSense was disconnected from Nova OS.'})


@analytics_bp.route('/api/adsense/revenue')
@admin_required
def adsense_revenue_api():
    try:
        days = int(request.args.get('days', 30))
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Choose a valid reporting period.'}), 400
    if days not in {7, 30, 90}:
        return jsonify({'status': 'error', 'message': 'Choose 7, 30, or 90 days.'}), 400
    account = connection_status()['account'] or {}
    return jsonify({
        'status': 'success',
        'currency': account.get('currency_code') or 'USD',
        **adsense_repository.revenue_snapshot(days),
    })


@analytics_bp.route('/api/payout-account', methods=['GET', 'POST'])
@admin_required
def payout_account_api():
    db = NewsDatabase()
    if request.method == 'POST':
        if not _same_origin():
            return jsonify({'status': 'error', 'message': 'This action must be started from Nova OS.'}), 403
        data = request.get_json(silent=True) or request.form.to_dict()
        name = (data.get('account_name') or '').strip()
        number = (data.get('account_number') or '').strip()
        bank = (data.get('bank_name') or '').strip()
        iban = (data.get('iban') or '').strip()
        if not name or not number or not bank:
            return jsonify({'status': 'error', 'message': 'Account name, number, and bank are required.'}), 400
        db.update_payout_account(name, number, bank, iban)
        return jsonify({'status': 'success', 'message': 'Payout account updated successfully.', 'payout': db.get_payout_account()})
    return jsonify(db.get_payout_account())


@analytics_bp.route('/api/track-ad-event', methods=['POST'])
def track_ad_event():
    data = request.get_json(silent=True) or {}
    event_type = data.get('event_type') or 'impression'
    if event_type not in {'impression', 'click', 'view'}:
        return jsonify({'status': 'error', 'message': 'Unsupported ad event.'}), 400
    page = data.get('page') or request.referrer or '/'
    detail = data.get('detail') or 'Google AdSense ca-pub-1036052096443002'
    NewsDatabase().log_ad_event(event_type, page, request.remote_addr, detail)
    return jsonify({'status': 'ok'})


@analytics_bp.route('/reports')
@admin_required
def reports():
    return render_template('analytics_reports.html')


@analytics_bp.route('/api/stats')
@admin_required
def get_stats():
    connection = safe_connect()
    cursor = connection.cursor()
    start = (datetime.now() - timedelta(days=6)).date()
    cursor.execute('''SELECT date(visit_time) AS visit_date, COUNT(*) FROM site_visits
        WHERE visit_time >= %s GROUP BY date(visit_time)''', (start,))
    traffic_by_date = {str(row[0]): int(row[1]) for row in cursor.fetchall()}
    connection.close()
    adsense_data = adsense_repository.revenue_snapshot(7)
    labels = [item['date'] for item in adsense_data['series']]
    return jsonify({
        'labels': labels,
        'traffic': [traffic_by_date.get(label, 0) for label in labels],
        'revenue': [item['estimated_earnings'] for item in adsense_data['series']],
    })


@analytics_bp.route('/messages')
@admin_required
def messages():
    return render_template('messages.html', messages=NewsDatabase().get_contact_messages(limit=100))


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


@analytics_bp.route('/api/unread-count')
@admin_required
def unread_count():
    return jsonify({'count': NewsDatabase().get_unread_message_count()})


@analytics_bp.route('/api/messages/<int:message_id>/read', methods=['POST'])
@admin_required
@same_origin_required
def mark_message_read(message_id):
    NewsDatabase().mark_message_read(message_id)
    return jsonify({'status': 'success'})


@analytics_bp.route('/api/messages/<int:message_id>/reply', methods=['POST'])
@admin_required
@same_origin_required
def reply_message(message_id):
    from ai_news_agent import send_email

    db = NewsDatabase()
    reply_text = ((request.get_json(silent=True) or {}).get('reply') or '').strip()
    if not reply_text:
        return jsonify({'status': 'error', 'message': 'Reply cannot be empty.'}), 400
    message = db.get_contact_message(message_id)
    if not message:
        return jsonify({'status': 'error', 'message': 'Message not found.'}), 404
    subject = f"Re: {message['subject']}"
    safe_name = escape(message['name'])
    safe_reply = escape(reply_text).replace('\n', '<br>')
    safe_original = escape(message['message'])
    html = f'''<html><body style="font-family:Arial,sans-serif;color:#333;line-height:1.6;">
        <p>Hi {safe_name},</p><p>{safe_reply}</p><br><p>Best regards,<br>Nova Admin Team</p>
        <hr style="border:0;border-top:1px solid #eee;margin:20px 0;">
        <p style="color:#888;font-size:12px;">On {str(message['submitted_at'])[:10]}, you wrote:<br><em>{safe_original}</em></p>
        </body></html>'''
    sent = send_email(message['email'], subject, html)
    db.mark_message_replied(message_id, reply_text)
    result_message = 'Reply sent and saved to history.' if sent else 'Reply saved, but email delivery is currently unavailable.'
    return jsonify({'status': 'success', 'message': result_message})
