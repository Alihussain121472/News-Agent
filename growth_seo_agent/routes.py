import os
import re
from datetime import timedelta
from functools import wraps
from urllib.parse import urlparse

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

import logging
from . import repository
from .engine import (
    build_content_brief,
    crawl_and_analyze_competitor,
    generate_actionable_seo_insights,
    normalize_site_url,
)
from .service import (
    check_and_alert_traffic_spikes,
    generate_daily_seo_report,
    start_seo_cycle,
)

logger = logging.getLogger(__name__)


seo_bp = Blueprint('seo', __name__, template_folder='templates')
ALLOWED_INTENTS = {'informational', 'commercial', 'transactional', 'navigational'}
ALLOWED_BACKLINK_STATUSES = {'prospect', 'qualified', 'contacted', 'earned', 'declined', 'lost', 'unreachable'}
ALLOWED_CONTENT_STATUSES = {'idea', 'approved', 'briefed', 'published', 'dismissed'}
EMAIL_PATTERN = re.compile(r'^[^@\s]{1,64}@[^@\s]{1,189}\.[^@\s]{2,63}$')


def _as_bool(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {'true', '1', 'yes', 'on'}:
            return True
        if normalized in {'false', '0', 'no', 'off'}:
            return False
    raise ValueError('Enabled must be true or false.')


def admin_required(handler):
    @wraps(handler)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            if request.path.startswith('/seo/api/'):
                return jsonify({'status': 'error', 'message': 'Please log in as an admin first.'}), 401
            return redirect(url_for('admin_login_page'))
        return handler(*args, **kwargs)

    return decorated_function


def _same_origin():
    source = request.headers.get('Origin') or request.headers.get('Referer')
    if not source:
        return os.getenv('FLASK_ENV', 'development').strip().lower() != 'production'
    try:
        source_url = urlparse(source)
        app_url = urlparse(request.host_url)
        return source_url.scheme == app_url.scheme and source_url.netloc == app_url.netloc
    except ValueError:
        return False


def same_origin_required(handler):
    @wraps(handler)
    def decorated_function(*args, **kwargs):
        if not _same_origin():
            return jsonify({'status': 'error', 'message': 'This action must be started from Nova OS.'}), 403
        return handler(*args, **kwargs)

    return decorated_function


def _dashboard_view_model():
    snapshot = repository.dashboard_snapshot()
    config = snapshot['config']
    latest = snapshot['latest_run']
    if latest and latest.get('completed_at'):
        schedule_hours = int(config.get('schedule_hours') or 6)
        snapshot['next_run_at'] = latest['completed_at'] + timedelta(hours=schedule_hours)
    else:
        snapshot['next_run_at'] = None
    snapshot['earned_backlinks'] = sum(1 for item in snapshot['backlinks'] if item.get('status') == 'earned')
    snapshot['open_content'] = sum(1 for item in snapshot['content_opportunities'] if item.get('status') in {'idea', 'approved', 'briefed'})
    snapshot['total_competitors'] = len(snapshot.get('competitors') or [])
    snapshot['total_gaps'] = sum(len(c.get('content_gaps') or []) for c in snapshot.get('competitors') or [])
    try:
        snapshot['actionable_insights'] = generate_actionable_seo_insights(
            keywords=snapshot.get('keywords'),
            competitors=snapshot.get('competitors'),
            audit_score=latest.get('score') if latest else 88
        )
    except Exception:
        snapshot['actionable_insights'] = []
    return snapshot


@seo_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('seo_dashboard.html', **_dashboard_view_model())


@seo_bp.route('/keywords')
@admin_required
def keywords():
    return redirect(url_for('seo.dashboard', _anchor='keywords'))


@seo_bp.route('/content')
@admin_required
def content_studio():
    return redirect(url_for('seo.dashboard', _anchor='content'))


@seo_bp.route('/api/status')
@admin_required
def agent_status():
    snapshot = _dashboard_view_model()
    latest = snapshot['latest_run']
    return jsonify({
        'status': 'active' if snapshot['config']['enabled'] else 'paused',
        'site_url': snapshot['config']['site_url'],
        'schedule_hours': snapshot['config']['schedule_hours'],
        'latest_run': dict(latest) if latest else None,
        'next_run_at': snapshot['next_run_at'].isoformat() if snapshot['next_run_at'] else None,
    })


@seo_bp.route('/api/run', methods=['POST'])
@admin_required
@same_origin_required
def run_agent():
    if not start_seo_cycle('manual'):
        return jsonify({'status': 'already_running', 'message': 'An SEO audit is already running.'}), 409
    return jsonify({'status': 'started', 'message': 'SEO Studio started a fresh audit. Results will appear here shortly.'}), 202


@seo_bp.route('/api/config', methods=['POST'])
@admin_required
@same_origin_required
def save_config():
    data = request.get_json(silent=True) or {}
    try:
        site_url = normalize_site_url(data.get('site_url'))
        schedule_hours = int(data.get('schedule_hours') or 6)
        max_pages = int(data.get('max_pages') or 20)
        enabled = _as_bool(data.get('enabled'), default=True)
    except (ValueError, TypeError) as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    if schedule_hours not in {1, 3, 6, 12, 24}:
        return jsonify({'status': 'error', 'message': 'Choose a schedule of 1, 3, 6, 12, or 24 hours.'}), 400
    if not 1 <= max_pages <= 50:
        return jsonify({'status': 'error', 'message': 'Page limit must be between 1 and 50.'}), 400
    config = repository.update_config(site_url, enabled, schedule_hours, max_pages)
    repository.log_event('config_updated', 'SEO Studio configuration updated.', {'site_url': site_url, 'enabled': enabled, 'schedule_hours': schedule_hours, 'max_pages': max_pages})
    return jsonify({'status': 'success', 'message': 'SEO monitoring settings saved.', 'config': config})


@seo_bp.route('/api/keywords', methods=['POST'])
@admin_required
@same_origin_required
def save_keyword():
    data = request.get_json(silent=True) or {}
    keyword = re.sub(r'\s+', ' ', (data.get('keyword') or '').strip())
    intent = (data.get('intent') or 'informational').strip().lower()
    notes = (data.get('notes') or '').strip()
    target_url = (data.get('target_url') or '').strip()
    if not keyword or len(keyword) > 160:
        return jsonify({'status': 'error', 'message': 'Enter a keyword of 160 characters or fewer.'}), 400
    if intent not in ALLOWED_INTENTS:
        return jsonify({'status': 'error', 'message': 'Choose a valid search intent.'}), 400
    try:
        priority = int(data.get('priority') or 3)
        position = int(data['position']) if data.get('position') not in {None, ''} else None
        search_volume = int(data.get('search_volume') or 0)
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Priority, position, and search volume must be numbers.'}), 400
    if priority not in {1, 2, 3, 4, 5} or (position is not None and position < 1) or search_volume < 0:
        return jsonify({'status': 'error', 'message': 'Enter valid positive tracking values.'}), 400
    if target_url:
        try:
            target_url = normalize_site_url(target_url)
        except ValueError as exc:
            return jsonify({'status': 'error', 'message': str(exc)}), 400
    row = repository.save_keyword(keyword, intent, target_url, priority, position, search_volume, notes)
    brief = build_content_brief(keyword, intent, target_url)
    repository.upsert_content_opportunity(keyword, intent, brief['working_title'], target_url, 'Tracked keyword ready for content planning and on-page review.')
    repository.log_event('keyword_saved', f'Keyword saved: {keyword}', {'keyword_id': row['id'], 'intent': intent})
    return jsonify({'status': 'success', 'message': 'Keyword added to monitoring.', 'keyword': row})


@seo_bp.route('/api/keywords/<int:keyword_id>', methods=['DELETE'])
@admin_required
@same_origin_required
def remove_keyword(keyword_id):
    if not repository.delete_keyword(keyword_id):
        return jsonify({'status': 'error', 'message': 'Keyword not found.'}), 404
    return jsonify({'status': 'success', 'message': 'Keyword removed.'})


@seo_bp.route('/api/backlinks', methods=['POST'])
@admin_required
@same_origin_required
def save_backlink():
    data = request.get_json(silent=True) or {}
    try:
        prospect_url = normalize_site_url(data.get('prospect_url'))
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    domain = (urlparse(prospect_url).hostname or '').lower()
    contact_email = (data.get('contact_email') or '').strip().lower()
    if contact_email and not EMAIL_PATTERN.fullmatch(contact_email):
        return jsonify({'status': 'error', 'message': 'Enter a valid contact email or leave it blank.'}), 400
    target_url = (data.get('target_url') or repository.get_config()['site_url']).strip()
    try:
        target_url = normalize_site_url(target_url)
        relevance_score = int(data.get('relevance_score') or 3)
    except (ValueError, TypeError) as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    if relevance_score not in {1, 2, 3, 4, 5}:
        return jsonify({'status': 'error', 'message': 'Relevance score must be between 1 and 5.'}), 400
    row = repository.save_backlink(domain, prospect_url, contact_email, target_url, relevance_score, (data.get('notes') or '').strip(), data.get('next_follow_up') or None)
    repository.log_event('backlink_saved', f'Backlink prospect added: {domain}', {'backlink_id': row['id']})
    return jsonify({'status': 'success', 'message': 'Backlink prospect added for monitoring.', 'backlink': row})


@seo_bp.route('/api/backlinks/<int:backlink_id>/status', methods=['POST'])
@admin_required
@same_origin_required
def set_backlink_status(backlink_id):
    status = ((request.get_json(silent=True) or {}).get('status') or '').strip().lower()
    if status not in ALLOWED_BACKLINK_STATUSES:
        return jsonify({'status': 'error', 'message': 'Choose a valid backlink status.'}), 400
    row = repository.update_backlink_status(backlink_id, status)
    if not row:
        return jsonify({'status': 'error', 'message': 'Backlink prospect not found.'}), 404
    return jsonify({'status': 'success', 'message': 'Backlink status updated.', 'backlink': row})


@seo_bp.route('/api/backlinks/<int:backlink_id>', methods=['DELETE'])
@admin_required
@same_origin_required
def remove_backlink(backlink_id):
    if not repository.delete_backlink(backlink_id):
        return jsonify({'status': 'error', 'message': 'Backlink prospect not found.'}), 404
    return jsonify({'status': 'success', 'message': 'Backlink prospect removed.'})


@seo_bp.route('/api/backlinks/<int:backlink_id>/outreach')
@admin_required
def backlink_outreach(backlink_id):
    backlink = repository.get_backlink(backlink_id)
    if not backlink:
        return jsonify({'status': 'error', 'message': 'Backlink prospect not found.'}), 404
    target = backlink.get('target_url') or repository.get_config()['site_url']
    subject = f'Resource suggestion for {backlink["domain"]}'
    body = (
        f'Hello,\n\nI’m reaching out from NovaBrief Tech. I noticed your work at {backlink["domain"]} '
        f'and thought this resource may be useful to your readers: {target}\n\n'
        'If it genuinely improves an existing article or resource page, please consider referencing it. '
        'No obligation—relevance and reader value come first.\n\nBest,\nNovaBrief Tech'
    )
    return jsonify({'status': 'success', 'subject': subject, 'body': body})


@seo_bp.route('/api/content/<int:content_id>/status', methods=['POST'])
@admin_required
@same_origin_required
def set_content_status(content_id):
    status = ((request.get_json(silent=True) or {}).get('status') or '').strip().lower()
    if status not in ALLOWED_CONTENT_STATUSES:
        return jsonify({'status': 'error', 'message': 'Choose a valid content status.'}), 400
    row = repository.update_content_status(content_id, status)
    if not row:
        return jsonify({'status': 'error', 'message': 'Content opportunity not found.'}), 404
    return jsonify({'status': 'success', 'message': 'Content workflow updated.', 'content': row})


@seo_bp.route('/api/content/<int:content_id>/brief')
@admin_required
def content_brief(content_id):
    opportunity = repository.get_content_opportunity(content_id)
    if not opportunity:
        return jsonify({'status': 'error', 'message': 'Content opportunity not found.'}), 404
    brief = build_content_brief(opportunity['keyword'], opportunity.get('intent') or 'informational', opportunity.get('target_url') or '')
    return jsonify({'status': 'success', 'brief': brief})

import requests
import json
from markupsafe import escape

@seo_bp.route('/api/generate-article', methods=['POST'])
@admin_required
def generate_seo_article():
    data = request.get_json(silent=True) or {}
    keyword = str(data.get('keyword') or '').strip()
    
    if not keyword:
        return jsonify({'status': 'error', 'message': 'Keyword is required.'}), 400
    if len(keyword) > 160:
        return jsonify({'status': 'error', 'message': 'Keyword must be 160 characters or fewer.'}), 400
        
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        return jsonify({'status': 'error', 'message': 'Groq API Key is not configured.'}), 500
        
    system_prompt = """You are NovaBrief Tech's senior, people-first SEO editor.
Create genuinely useful content for university students and early-career technology readers.
The article must satisfy the search intent behind the keyword before promoting NovaBrief.

Use these operating rules from NovaBrief's SEO playbook:
- Expand the keyword into closely related, non-duplicative subtopics and natural long-tail questions.
- Cover practical details such as eligibility, deadlines, application steps, preparation, costs, tools, or examples when relevant.
- Structure the article with exactly one H1, descriptive H2 sections, and H3 subsections only where they improve scanning.
- Use a concise, accurate title of 60 characters or fewer and a compelling meta description of 155 characters or fewer.
- Return a lowercase, hyphenated URL slug with no dates unless the year is essential to the query.
- Add useful internal-link opportunities using descriptive anchor text, but never invent URLs; use [INTERNAL_LINK: suggested topic] placeholders.
- Include a short FAQ section only for real questions the article answers.
- Prefer original explanations, clearly attributed facts, and visible update context. Do not keyword-stuff, copy competitors, make unsupported claims, or promise rankings.
- If competitor or source material is not supplied, do not pretend to have performed competitor research. State gaps as editorial opportunities in the article notes instead.

Return exactly and ONLY a valid JSON object with these keys:
"title", "meta_description", "slug", "content", "target_questions", "internal_link_opportunities", "editor_notes".
The content must be Markdown. The three list fields must be JSON arrays of strings."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        model_name = os.environ.get('GROQ_MODEL', 'openai/gpt-oss-120b').strip()
            
        payload = {
            'model': model_name,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f'Target Keyword: {keyword}'}
            ],
            'temperature': 0.7,
            'max_tokens': 800,
            'response_format': {'type': 'json_object'}
        }
        
        resp = requests.post('https://api.groq.com/openai/v1/chat/completions', headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        result_text = resp.json()['choices'][0]['message']['content'].strip()
        result = json.loads(result_text)
        required_fields = ('title', 'meta_description', 'slug', 'content')
        if not isinstance(result, dict) or not all(isinstance(result.get(field), str) for field in required_fields):
            raise ValueError('Groq returned an incomplete SEO article.')
        if not all(isinstance(result.get(field), list) for field in ('target_questions', 'internal_link_opportunities', 'editor_notes')):
            raise ValueError('Groq returned invalid SEO metadata.')
        return jsonify({'status': 'success', 'data': result})
    except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as e:
        return jsonify({'status': 'error', 'message': f'Invalid AI response: {e}'}), 502
    except requests.RequestException as e:
        return jsonify({'status': 'error', 'message': f'Groq API request failed: {e}'}), 502
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'API Error: {str(e)}'}), 500


@seo_bp.route('/api/visitor-analytics')
@admin_required
def visitor_analytics_api():
    days = int(request.args.get('days') or 30)
    data = repository.get_visitor_analytics(days=days)
    return jsonify({'status': 'success', 'data': data})


@seo_bp.route('/api/actionable-insights')
@admin_required
def actionable_insights_api():
    latest = repository.latest_run()
    score = latest.get('score') if latest else 88
    keywords = repository.list_keywords()
    competitors = repository.list_competitors()
    insights = generate_actionable_seo_insights(
        keywords=keywords,
        competitors=competitors,
        audit_score=score
    )
    return jsonify({'status': 'success', 'insights': insights})


@seo_bp.route('/api/competitors', methods=['GET'])
@admin_required
def list_competitors_api():
    competitors = repository.list_competitors()
    return jsonify({'status': 'success', 'competitors': competitors})


@seo_bp.route('/api/competitors', methods=['POST'])
@admin_required
@same_origin_required
def add_competitor_api():
    data = request.get_json(silent=True) or {}
    domain = (data.get('domain') or '').strip().lower()
    name = (data.get('name') or '').strip()
    notes = (data.get('notes') or '').strip()

    if not domain:
        return jsonify({'status': 'error', 'message': 'Competitor domain or URL is required.'}), 400

    try:
        saved = repository.save_competitor(domain, name, notes)
        our_keywords = repository.list_keywords()
        analysis = crawl_and_analyze_competitor(saved['domain'], our_keywords=our_keywords)
        updated = repository.update_competitor_analysis(saved['id'], analysis)
        repository.log_event('competitor_analyzed', f"Analyzed competitor: {saved['domain']}", {'competitor_id': saved['id']})
        return jsonify({
            'status': 'success',
            'message': f"Competitor '{saved['domain']}' added and analyzed successfully.",
            'competitor': updated or saved
        })
    except Exception as e:
        logger.exception('Competitor analysis failed')
        return jsonify({'status': 'error', 'message': f'Failed to analyze competitor: {str(e)}'}), 400


@seo_bp.route('/api/competitors/<int:competitor_id>/analyze', methods=['POST'])
@admin_required
@same_origin_required
def reanalyze_competitor_api(competitor_id):
    competitor = repository.get_competitor(competitor_id)
    if not competitor:
        return jsonify({'status': 'error', 'message': 'Competitor not found.'}), 404
    try:
        our_keywords = repository.list_keywords()
        analysis = crawl_and_analyze_competitor(competitor['domain'], our_keywords=our_keywords)
        updated = repository.update_competitor_analysis(competitor_id, analysis)
        return jsonify({
            'status': 'success',
            'message': f"Competitor '{competitor['domain']}' re-analyzed.",
            'competitor': updated
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@seo_bp.route('/api/competitors/<int:competitor_id>', methods=['DELETE'])
@admin_required
@same_origin_required
def delete_competitor_api(competitor_id):
    if not repository.delete_competitor(competitor_id):
        return jsonify({'status': 'error', 'message': 'Competitor not found.'}), 404
    return jsonify({'status': 'success', 'message': 'Competitor removed.'})


@seo_bp.route('/api/daily-reports', methods=['GET'])
@admin_required
def list_daily_reports_api():
    reports = repository.list_daily_reports(limit=20)
    return jsonify({'status': 'success', 'reports': reports})


@seo_bp.route('/api/daily-reports/generate', methods=['POST'])
@admin_required
@same_origin_required
def generate_daily_report_api():
    try:
        report = generate_daily_seo_report()
        return jsonify({
            'status': 'success',
            'message': 'Daily SEO performance report generated successfully.',
            'report': report
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to generate report: {str(e)}'}), 500


@seo_bp.route('/api/test-spike-alert', methods=['POST'])
@admin_required
@same_origin_required
def test_spike_alert_api():
    try:
        res = check_and_alert_traffic_spikes(recipient_email='syedali6160@gmail.com', force_test=True)
        return jsonify(res)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to send test alert: {str(e)}'}), 500


@seo_bp.route('/api/traffic-alerts', methods=['GET'])
@admin_required
def list_traffic_alerts_api():
    alerts = repository.list_traffic_alerts(limit=15)
    return jsonify({'status': 'success', 'alerts': alerts})


@seo_bp.route('/api/integrations', methods=['POST'])
@admin_required
@same_origin_required
def save_integrations_api():
    data = request.get_json(silent=True) or {}
    ga_id = (data.get('ga_measurement_id') or '').strip()
    gsc_token = (data.get('google_site_verification') or '').strip()
    alert_email = (data.get('alert_email') or '').strip() or 'syedali6160@gmail.com'
    spike_threshold = int(data.get('spike_threshold_pct') or 100)
    spike_min = int(data.get('spike_min_visits') or 5)

    if alert_email and not EMAIL_PATTERN.fullmatch(alert_email):
        return jsonify({'status': 'error', 'message': 'Enter a valid email for traffic alerts.'}), 400

    cfg = repository.update_integrations(
        ga_measurement_id=ga_id,
        google_site_verification=gsc_token,
        alert_email=alert_email,
        spike_threshold_pct=spike_threshold,
        spike_min_visits=spike_min,
    )
    repository.log_event('integrations_updated', 'Updated Google Analytics, Search Console, and Alert settings.', {
        'ga_configured': bool(ga_id),
        'gsc_configured': bool(gsc_token),
        'alert_email': alert_email
    })
    return jsonify({
        'status': 'success',
        'message': 'Google Analytics, Search Console, and Traffic Alert settings saved.',
        'config': cfg
    })
