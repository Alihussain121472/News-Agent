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
