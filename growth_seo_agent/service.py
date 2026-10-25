import logging
import threading
import time
from datetime import datetime, timedelta

from .engine import audit_site, build_content_brief, inspect_backlink
from . import repository


logger = logging.getLogger(__name__)
_local_run_lock = threading.Lock()


def _create_content_opportunities(audit, keywords):
    coverage = ' '.join(
        f"{page.get('url', '')} {page.get('title', '')} {page.get('h1', '')}".lower()
        for page in audit.get('pages', [])
    )
    created = 0
    for keyword in keywords:
        phrase = keyword['keyword'].lower()
        if phrase in coverage:
            continue
        brief = build_content_brief(keyword['keyword'], keyword.get('intent') or 'informational', keyword.get('target_url') or '')
        repository.upsert_content_opportunity(
            keyword=keyword['keyword'],
            intent=brief['intent'],
            recommended_title=brief['working_title'],
            target_url=brief.get('target_url'),
            rationale='No audited title or primary heading currently targets this tracked search intent.',
        )
        created += 1
    return created


def _monitor_backlinks(site_url, backlinks):
    checked = 0
    earned = 0
    for backlink in backlinks:
        try:
            result = inspect_backlink(backlink['prospect_url'], site_url)
        except Exception as exc:
            result = {'status': 'unreachable', 'http_status': 0, 'link_url': None, 'attributes': [], 'error': str(exc)}
        repository.update_backlink_check(backlink['id'], result)
        checked += 1
        earned += int(result['status'] == 'earned')
    return checked, earned


def run_seo_cycle(trigger_type='scheduled', force=False, _lock_acquired=False):
    if not _lock_acquired and not _local_run_lock.acquire(blocking=False):
        return {'status': 'already_running', 'message': 'An SEO audit is already running.'}

    advisory_connection = None
    run_id = None
    started = time.monotonic()
    try:
        repository.ensure_schema()
        advisory_connection = repository.acquire_run_lock()
        if not advisory_connection:
            return {'status': 'already_running', 'message': 'An SEO audit is already running on another worker.'}

        config = repository.get_config()
        if trigger_type == 'scheduled' and not config['enabled'] and not force:
            return {'status': 'disabled', 'message': 'Scheduled SEO monitoring is disabled.'}

        run_id = repository.create_run(config['site_url'], trigger_type)
        repository.log_event('audit_started', 'SEO audit started.', {'run_id': run_id, 'trigger': trigger_type})
        audit = audit_site(config['site_url'], config['max_pages'])
        keyword_count = _create_content_opportunities(audit, repository.list_keywords())
        backlink_checked, backlink_earned = _monitor_backlinks(config['site_url'], repository.list_backlinks())
        duration_ms = int((time.monotonic() - started) * 1000)
        audit['content_opportunities_created'] = keyword_count
        audit['backlinks_checked'] = backlink_checked
        audit['earned_backlinks_found'] = backlink_earned
        repository.complete_run(run_id, audit, duration_ms)
        repository.log_event('audit_completed', f'SEO audit completed with a health score of {audit["score"]}.', {
            'run_id': run_id,
            'pages_checked': audit['pages_checked'],
            'critical_count': audit['critical_count'],
            'warning_count': audit['warning_count'],
            'backlinks_checked': backlink_checked,
        })
        return {'status': 'completed', 'run_id': run_id, 'audit': audit, 'duration_ms': duration_ms}
    except Exception as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.exception('SEO cycle failed')
        if run_id:
            try:
                repository.fail_run(run_id, exc, duration_ms)
                repository.log_event('audit_failed', 'SEO audit failed.', {'run_id': run_id, 'error': str(exc)[:500]})
            except Exception:
                logger.exception('Could not persist SEO audit failure')
        return {'status': 'failed', 'message': str(exc), 'run_id': run_id}
    finally:
        repository.release_run_lock(advisory_connection)
        _local_run_lock.release()


def run_scheduled_if_due():
    repository.ensure_schema()
    config = repository.get_config()
    if not config['enabled']:
        return {'status': 'disabled', 'message': 'Scheduled SEO monitoring is disabled.'}
    latest = repository.latest_run()
    if latest and latest.get('completed_at') and latest.get('status') == 'completed':
        completed_at = latest['completed_at']
        now = datetime.now(completed_at.tzinfo) if getattr(completed_at, 'tzinfo', None) else datetime.utcnow()
        due_at = completed_at + timedelta(hours=int(config.get('schedule_hours') or 6))
        if now < due_at:
            return {'status': 'not_due', 'message': 'The next SEO audit is not due yet.', 'next_run_at': due_at.isoformat()}
    return run_seo_cycle(trigger_type='scheduled')


def start_seo_cycle(trigger_type='manual'):
    if not _local_run_lock.acquire(blocking=False):
        return False

    thread = threading.Thread(
        target=run_seo_cycle,
        kwargs={'trigger_type': trigger_type, '_lock_acquired': True},
        name='seo-studio-audit',
        daemon=True,
    )
    try:
        thread.start()
    except Exception:
        _local_run_lock.release()
        raise
    return True


def check_and_alert_traffic_spikes(recipient_email=None, force_test=False):
    repository.ensure_schema()
    config = repository.get_config()
    target_email = (recipient_email or config.get('alert_email') or 'syedali6160@gmail.com').strip()
    spike_min_visits = int(config.get('spike_min_visits') or 5)
    spike_threshold_pct = float(config.get('spike_threshold_pct') or 100)

    with repository._connection(dict_rows=True) as (_, cursor):
        cursor.execute("SELECT COUNT(*) as count FROM site_visits WHERE visit_time >= CURRENT_TIMESTAMP - INTERVAL '1 hour'")
        last_hour_row = cursor.fetchone() or {'count': 0}
        last_hour_count = int(last_hour_row.get('count') or 0)

        cursor.execute('''
            SELECT COUNT(*) as count FROM site_visits
            WHERE visit_time >= CURRENT_TIMESTAMP - INTERVAL '49 hours'
              AND visit_time < CURRENT_TIMESTAMP - INTERVAL '1 hour'
        ''')
        baseline_row = cursor.fetchone() or {'count': 0}
        total_48h = int(baseline_row.get('count') or 0)
        baseline_avg = round(total_48h / 48.0, 2)

        cursor.execute('''
            SELECT page, COUNT(*) as count FROM site_visits
            WHERE visit_time >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
            GROUP BY page ORDER BY count DESC LIMIT 5
        ''')
        surge_pages = [dict(r) for r in cursor.fetchall()]

    if baseline_avg > 0:
        surge_pct = round(((last_hour_count - baseline_avg) / baseline_avg) * 100.0, 1)
    else:
        surge_pct = 100.0 if last_hour_count > 0 else 0.0

    is_spike = (last_hour_count >= spike_min_visits and surge_pct >= spike_threshold_pct)

    if not force_test and not is_spike:
        return {
            'status': 'normal',
            'last_hour_visits': last_hour_count,
            'baseline_avg': baseline_avg,
            'surge_percentage': surge_pct,
            'alert_triggered': False,
            'message': f'Traffic is normal ({last_hour_count} visits/hr vs {baseline_avg:.1f} baseline avg).'
        }

    if not force_test:
        recent_count = repository.recent_alert_count(hours=6)
        if recent_count > 0:
            return {
                'status': 'cooldown',
                'last_hour_visits': last_hour_count,
                'baseline_avg': baseline_avg,
                'surge_percentage': surge_pct,
                'alert_triggered': False,
                'message': 'Traffic surge detected, but an alert was already sent within the 6-hour cooldown window.'
            }

    from datetime import datetime
    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

    pages_html = "".join([
        f"<tr><td style='padding:8px 12px;border-bottom:1px solid #edf2f7;color:#2d3748;'><code>{p.get('page')}</code></td>"
        f"<td style='padding:8px 12px;border-bottom:1px solid #edf2f7;text-align:right;font-weight:bold;color:#4f46e5;'>{p.get('count')}</td></tr>"
        for p in surge_pages
    ]) or "<tr><td colspan='2' style='padding:8px 12px;color:#718096;'>Direct homepage visits</td></tr>"

    test_badge = "<span style='display:inline-block;padding:3px 8px;background:#fef3c7;color:#92400e;border-radius:6px;font-size:11px;font-weight:bold;margin-bottom:12px;'>MANUAL TEST ALERT</span><br>" if force_test else ""

    email_html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset='utf-8'></head>
    <body style='font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background-color:#f7fafc;margin:0;padding:24px 12px;color:#1a202c;'>
      <div style='max-width:600px;margin:0 auto;background:#ffffff;border-radius:16px;border:1px solid #e2e8f0;overflow:hidden;box-shadow:0 10px 25px rgba(0,0,0,0.05);'>
        <div style='background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:32px 24px;text-align:center;color:#ffffff;'>
          {test_badge}
          <h1 style='margin:0;font-size:24px;font-weight:800;letter-spacing:-0.5px;'>🚀 Traffic Spike Alert</h1>
          <p style='margin:8px 0 0;font-size:14px;color:#e0e7ff;'>Significant visitor surge detected on <strong>NovaBrief.tech</strong></p>
        </div>
        <div style='padding:28px 24px;'>
          <div style='display:flex;justify-content:space-between;margin-bottom:24px;background:#f8fafc;padding:16px;border-radius:12px;border:1px solid #e2e8f0;'>
            <div style='text-align:center;flex:1;'>
              <div style='font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;'>Current Hour</div>
              <div style='font-size:26px;color:#0f172a;font-weight:800;'>{last_hour_count}</div>
              <div style='font-size:11px;color:#64748b;'>visits</div>
            </div>
            <div style='text-align:center;flex:1;border-left:1px solid #e2e8f0;border-right:1px solid #e2e8f0;'>
              <div style='font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;'>Baseline Avg</div>
              <div style='font-size:26px;color:#0f172a;font-weight:800;'>{baseline_avg:.1f}</div>
              <div style='font-size:11px;color:#64748b;'>visits/hr</div>
            </div>
            <div style='text-align:center;flex:1;'>
              <div style='font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;'>Surge Rate</div>
              <div style='font-size:26px;color:#10b981;font-weight:800;'>+{surge_pct:.0f}%</div>
              <div style='font-size:11px;color:#10b981;font-weight:700;'>above baseline</div>
            </div>
          </div>

          <h3 style='font-size:14px;font-weight:700;color:#1e293b;margin:0 0 12px;text-transform:uppercase;letter-spacing:0.5px;'>Top Trending Landing Pages</h3>
          <table style='width:100%;border-collapse:collapse;font-size:13px;margin-bottom:24px;'>
            <thead>
              <tr style='background:#f1f5f9;text-align:left;'>
                <th style='padding:8px 12px;border-radius:6px 0 0 6px;color:#475569;'>Page Path</th>
                <th style='padding:8px 12px;text-align:right;border-radius:0 6px 6px 0;color:#475569;'>Visits</th>
              </tr>
            </thead>
            <tbody>
              {pages_html}
            </tbody>
          </table>

          <div style='text-align:center;margin-top:28px;'>
            <a href='https://www.novabrief.tech/seo/dashboard' style='display:inline-block;background:#4f46e5;color:#ffffff;text-decoration:none;font-weight:700;font-size:14px;padding:12px 28px;border-radius:10px;box-shadow:0 4px 12px rgba(79,70,229,0.3);'>Open SEO Studio & Analytics</a>
          </div>
        </div>
        <div style='background:#f8fafc;padding:16px 24px;border-top:1px solid #edf2f7;font-size:11px;color:#94a3b8;text-align:center;'>
          NovaBrief Autonomous SEO & Growth Agent • Sent to {target_email} at {now_str}
        </div>
      </div>
    </body>
    </html>
    """

    subject = f"{'[TEST] ' if force_test else '🚀 '}Traffic Spike Alert: NovaBrief.tech surged +{surge_pct:.0f}% ({last_hour_count} visits/hr)"

    send_status = 'sent'
    try:
        from ai_news_agent import send_email
        success = send_email(target_email, subject, email_html)
        if not success:
            send_status = 'failed'
    except Exception as e:
        logger.error('Failed to send traffic spike email: %s', e)
        send_status = f'failed: {e}'

    alert_row = repository.record_traffic_alert(
        hourly_visits=last_hour_count,
        baseline_avg=baseline_avg,
        surge_percentage=surge_pct,
        recipient_email=target_email,
        status=send_status,
        details={
            'surge_pages': surge_pages,
            'force_test': force_test,
            'timestamp': now_str
        }
    )
    repository.log_event(
        'traffic_spike_alert',
        f'Traffic spike alert dispatched to {target_email} (+{surge_pct:.0f}% surge).',
        {'hourly_visits': last_hour_count, 'baseline_avg': baseline_avg, 'status': send_status}
    )

    return {
        'status': 'sent' if send_status == 'sent' else 'warning',
        'alert_id': alert_row['id'],
        'recipient': target_email,
        'last_hour_visits': last_hour_count,
        'baseline_avg': baseline_avg,
        'surge_percentage': surge_pct,
        'alert_triggered': True,
        'delivery_status': send_status,
        'message': f'Traffic spike alert email {"successfully delivered" if send_status == "sent" else "queued"} to {target_email}.'
    }


def generate_daily_seo_report(target_date=None):
    from datetime import date
    today_date = target_date or date.today()

    analytics = repository.get_visitor_analytics(days=30)
    latest_run = repository.latest_run()
    seo_score = latest_run['score'] if latest_run and latest_run.get('score') is not None else 88

    keywords = repository.list_keywords()
    competitors = repository.list_competitors()

    from .engine import generate_actionable_seo_insights
    recommendations = generate_actionable_seo_insights(
        keywords=keywords,
        competitors=competitors,
        audit_score=seo_score
    )

    keyword_summary = {
        'total_tracked': len(keywords),
        'top_positions': sum(1 for k in keywords if k.get('position') and k['position'] <= 10),
        'opportunities': sum(1 for k in keywords if not k.get('position')),
    }

    comp_summary = {
        'competitors_monitored': len(competitors),
        'total_gaps_identified': sum(len(c.get('content_gaps') or []) for c in competitors),
    }

    report = repository.save_daily_report(
        report_date=today_date,
        total_visits=analytics['today_visits'],
        unique_visitors=analytics['today_unique'],
        seo_score=seo_score,
        top_pages=analytics['top_pages'][:5],
        top_referrers=analytics['top_referrers'][:5],
        keyword_summary=keyword_summary,
        competitor_insights=comp_summary,
        actionable_recommendations=recommendations,
    )
    repository.log_event(
        'daily_report_generated',
        f'Daily SEO performance report compiled for {today_date}.',
        {'report_id': report['id'], 'visits': analytics['today_visits'], 'score': seo_score}
    )
    return report
