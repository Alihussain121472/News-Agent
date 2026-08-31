import os
from contextlib import contextmanager

import psycopg2.extras

from database import safe_connect


DEFAULT_SITE_URL = os.getenv('SEO_SITE_URL', 'https://www.novabrief.tech').strip()
DEFAULT_KEYWORDS = [
    ('AI news daily', 'informational', 1),
    ('artificial intelligence news', 'informational', 1),
    ('AI tools for students', 'commercial', 2),
    ('technology career opportunities', 'informational', 2),
    ('student internship alerts', 'transactional', 2),
]
RUN_LOCK_ID = 67190311


@contextmanager
def _connection(dict_rows=False):
    conn = safe_connect()
    cursor_factory = psycopg2.extras.RealDictCursor if dict_rows else None
    cursor = conn.cursor(cursor_factory=cursor_factory)
    try:
        yield conn, cursor
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def ensure_schema():
    statements = [
        '''CREATE TABLE IF NOT EXISTS seo_agent_config (
            id INTEGER PRIMARY KEY,
            site_url TEXT NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            schedule_hours INTEGER NOT NULL DEFAULT 6,
            max_pages INTEGER NOT NULL DEFAULT 20,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS seo_audit_runs (
            id SERIAL PRIMARY KEY,
            trigger_type TEXT NOT NULL DEFAULT 'scheduled',
            site_url TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'running',
            score INTEGER,
            pages_checked INTEGER DEFAULT 0,
            critical_count INTEGER DEFAULT 0,
            warning_count INTEGER DEFAULT 0,
            notice_count INTEGER DEFAULT 0,
            duration_ms INTEGER,
            summary JSONB,
            error_message TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS seo_audit_issues (
            id SERIAL PRIMARY KEY,
            run_id INTEGER NOT NULL,
            issue_key TEXT NOT NULL,
            category TEXT NOT NULL,
            severity TEXT NOT NULL,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            detail TEXT,
            recommendation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS seo_keywords (
            id SERIAL PRIMARY KEY,
            keyword TEXT UNIQUE NOT NULL,
            position INTEGER,
            previous_position INTEGER,
            search_volume INTEGER DEFAULT 0,
            intent TEXT DEFAULT 'informational',
            target_url TEXT,
            priority INTEGER DEFAULT 3,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS seo_backlink_opportunities (
            id SERIAL PRIMARY KEY,
            domain TEXT NOT NULL,
            prospect_url TEXT UNIQUE NOT NULL,
            contact_email TEXT,
            target_url TEXT,
            relevance_score INTEGER NOT NULL DEFAULT 3,
            status TEXT NOT NULL DEFAULT 'prospect',
            notes TEXT,
            discovered_link_url TEXT,
            link_attributes TEXT,
            last_http_status INTEGER,
            last_checked_at TIMESTAMP,
            next_follow_up DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS seo_content_opportunities (
            id SERIAL PRIMARY KEY,
            keyword TEXT UNIQUE NOT NULL,
            intent TEXT NOT NULL DEFAULT 'informational',
            recommended_title TEXT NOT NULL,
            target_url TEXT,
            rationale TEXT,
            status TEXT NOT NULL DEFAULT 'idea',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS seo_agent_events (
            id SERIAL PRIMARY KEY,
            event_type TEXT NOT NULL,
            message TEXT NOT NULL,
            details JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
    ]

    with _connection() as (conn, cursor):
        for statement in statements:
            cursor.execute(statement)
        cursor.execute("ALTER TABLE seo_keywords ADD COLUMN IF NOT EXISTS intent TEXT DEFAULT 'informational'")
        cursor.execute('ALTER TABLE seo_keywords ADD COLUMN IF NOT EXISTS target_url TEXT')
        cursor.execute('ALTER TABLE seo_keywords ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 3')
        cursor.execute('ALTER TABLE seo_keywords ADD COLUMN IF NOT EXISTS notes TEXT')
        cursor.execute('''INSERT INTO seo_agent_config (id, site_url, enabled, schedule_hours, max_pages)
            VALUES (1, %s, TRUE, 6, 20) ON CONFLICT (id) DO NOTHING''', (DEFAULT_SITE_URL,))
        for keyword, intent, priority in DEFAULT_KEYWORDS:
            cursor.execute('''INSERT INTO seo_keywords (keyword, intent, priority)
                VALUES (%s, %s, %s) ON CONFLICT (keyword) DO NOTHING''', (keyword, intent, priority))
        conn.commit()


def get_config():
    ensure_schema()
    with _connection(dict_rows=True) as (_, cursor):
        cursor.execute('SELECT * FROM seo_agent_config WHERE id = 1')
        return dict(cursor.fetchone())


def update_config(site_url, enabled, schedule_hours, max_pages):
    ensure_schema()
    with _connection(dict_rows=True) as (conn, cursor):
        cursor.execute('''UPDATE seo_agent_config SET site_url=%s, enabled=%s, schedule_hours=%s,
            max_pages=%s, updated_at=CURRENT_TIMESTAMP WHERE id=1 RETURNING *''',
            (site_url, enabled, schedule_hours, max_pages))
        row = dict(cursor.fetchone())
        conn.commit()
        return row


def acquire_run_lock():
    conn = safe_connect()
    cursor = conn.cursor()
    cursor.execute('SELECT pg_try_advisory_lock(%s)', (RUN_LOCK_ID,))
    acquired = bool(cursor.fetchone()[0])
    cursor.close()
    if not acquired:
        conn.close()
        return None
    return conn


def release_run_lock(conn):
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT pg_advisory_unlock(%s)', (RUN_LOCK_ID,))
        cursor.close()
    finally:
        conn.close()


def create_run(site_url, trigger_type):
    ensure_schema()
    with _connection() as (conn, cursor):
        cursor.execute('''INSERT INTO seo_audit_runs (site_url, trigger_type, status)
            VALUES (%s, %s, 'running') RETURNING id''', (site_url, trigger_type))
        run_id = cursor.fetchone()[0]
        conn.commit()
        return run_id


def complete_run(run_id, audit, duration_ms):
    summary = {key: value for key, value in audit.items() if key != 'issues'}
    with _connection() as (conn, cursor):
        cursor.execute('DELETE FROM seo_audit_issues WHERE run_id=%s', (run_id,))
        for issue in audit['issues']:
            cursor.execute('''INSERT INTO seo_audit_issues
                (run_id, issue_key, category, severity, url, title, detail, recommendation)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''', (
                    run_id, issue['key'], issue['category'], issue['severity'], issue['url'],
                    issue['title'], issue.get('detail'), issue.get('recommendation'),
                ))
        cursor.execute('''UPDATE seo_audit_runs SET status='completed', score=%s, pages_checked=%s,
            critical_count=%s, warning_count=%s, notice_count=%s, duration_ms=%s, summary=%s,
            completed_at=CURRENT_TIMESTAMP WHERE id=%s''', (
                audit['score'], audit['pages_checked'], audit['critical_count'], audit['warning_count'],
                audit['notice_count'], duration_ms, psycopg2.extras.Json(summary), run_id,
            ))
        conn.commit()


def fail_run(run_id, error_message, duration_ms):
    with _connection() as (conn, cursor):
        cursor.execute('''UPDATE seo_audit_runs SET status='failed', error_message=%s, duration_ms=%s,
            completed_at=CURRENT_TIMESTAMP WHERE id=%s''', (str(error_message)[:2000], duration_ms, run_id))
        conn.commit()


def list_runs(limit=8):
    ensure_schema()
    with _connection(dict_rows=True) as (_, cursor):
        cursor.execute('SELECT * FROM seo_audit_runs ORDER BY started_at DESC LIMIT %s', (max(1, min(limit, 50)),))
        return [dict(row) for row in cursor.fetchall()]


def latest_run():
    runs = list_runs(1)
    return runs[0] if runs else None


def latest_issues(limit=30):
    ensure_schema()
    with _connection(dict_rows=True) as (_, cursor):
        cursor.execute('''SELECT i.* FROM seo_audit_issues i
            JOIN seo_audit_runs r ON r.id=i.run_id
            WHERE r.status='completed' AND r.id=(SELECT MAX(id) FROM seo_audit_runs WHERE status='completed')
            ORDER BY CASE i.severity WHEN 'critical' THEN 1 WHEN 'warning' THEN 2 ELSE 3 END, i.id
            LIMIT %s''', (max(1, min(limit, 100)),))
        return [dict(row) for row in cursor.fetchall()]


def list_keywords():
    ensure_schema()
    with _connection(dict_rows=True) as (_, cursor):
        cursor.execute('SELECT * FROM seo_keywords ORDER BY priority ASC, keyword ASC')
        rows = []
        for row in cursor.fetchall():
            item = dict(row)
            current, previous = item.get('position'), item.get('previous_position')
            item['change'] = (previous - current) if current and previous else 0
            rows.append(item)
        return rows


def save_keyword(keyword, intent, target_url, priority, position=None, search_volume=0, notes=''):
    ensure_schema()
    with _connection(dict_rows=True) as (conn, cursor):
        cursor.execute('''INSERT INTO seo_keywords
            (keyword, intent, target_url, priority, position, previous_position, search_volume, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (keyword) DO UPDATE SET
                intent=EXCLUDED.intent, target_url=EXCLUDED.target_url, priority=EXCLUDED.priority,
                previous_position=seo_keywords.position, position=COALESCE(EXCLUDED.position, seo_keywords.position),
                search_volume=EXCLUDED.search_volume, notes=EXCLUDED.notes, updated_at=CURRENT_TIMESTAMP
            RETURNING *''', (keyword, intent, target_url or None, priority, position, position, search_volume, notes or None))
        row = dict(cursor.fetchone())
        conn.commit()
        return row


def delete_keyword(keyword_id):
    with _connection() as (conn, cursor):
        cursor.execute('DELETE FROM seo_keywords WHERE id=%s', (keyword_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted


def list_backlinks():
    ensure_schema()
    with _connection(dict_rows=True) as (_, cursor):
        cursor.execute('SELECT * FROM seo_backlink_opportunities ORDER BY relevance_score DESC, created_at DESC')
        return [dict(row) for row in cursor.fetchall()]


def get_backlink(backlink_id):
    ensure_schema()
    with _connection(dict_rows=True) as (_, cursor):
        cursor.execute('SELECT * FROM seo_backlink_opportunities WHERE id=%s', (backlink_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def save_backlink(domain, prospect_url, contact_email, target_url, relevance_score, notes, next_follow_up=None):
    ensure_schema()
    with _connection(dict_rows=True) as (conn, cursor):
        cursor.execute('''INSERT INTO seo_backlink_opportunities
            (domain, prospect_url, contact_email, target_url, relevance_score, notes, next_follow_up)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (prospect_url) DO UPDATE SET
                domain=EXCLUDED.domain, contact_email=EXCLUDED.contact_email, target_url=EXCLUDED.target_url,
                relevance_score=EXCLUDED.relevance_score, notes=EXCLUDED.notes,
                next_follow_up=EXCLUDED.next_follow_up, updated_at=CURRENT_TIMESTAMP
            RETURNING *''', (domain, prospect_url, contact_email or None, target_url or None, relevance_score, notes or None, next_follow_up))
        row = dict(cursor.fetchone())
        conn.commit()
        return row


def update_backlink_status(backlink_id, status):
    with _connection(dict_rows=True) as (conn, cursor):
        cursor.execute('''UPDATE seo_backlink_opportunities SET status=%s, updated_at=CURRENT_TIMESTAMP
            WHERE id=%s RETURNING *''', (status, backlink_id))
        row = cursor.fetchone()
        conn.commit()
        return dict(row) if row else None


def update_backlink_check(backlink_id, result):
    with _connection() as (conn, cursor):
        cursor.execute('''UPDATE seo_backlink_opportunities SET status=CASE
                WHEN %s='earned' THEN 'earned'
                WHEN %s='unreachable' THEN 'unreachable'
                WHEN %s='prospect' AND status='earned' THEN 'lost'
                ELSE status END,
            discovered_link_url=%s,
            link_attributes=%s, last_http_status=%s, last_checked_at=CURRENT_TIMESTAMP,
            updated_at=CURRENT_TIMESTAMP WHERE id=%s''', (
                result['status'], result['status'], result['status'], result.get('link_url'),
                ', '.join(result.get('attributes') or []),
                result.get('http_status'), backlink_id,
            ))
        conn.commit()


def delete_backlink(backlink_id):
    with _connection() as (conn, cursor):
        cursor.execute('DELETE FROM seo_backlink_opportunities WHERE id=%s', (backlink_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted


def list_content_opportunities():
    ensure_schema()
    with _connection(dict_rows=True) as (_, cursor):
        cursor.execute("SELECT * FROM seo_content_opportunities ORDER BY CASE status WHEN 'idea' THEN 1 WHEN 'approved' THEN 2 WHEN 'briefed' THEN 3 ELSE 4 END, created_at DESC")
        return [dict(row) for row in cursor.fetchall()]


def upsert_content_opportunity(keyword, intent, recommended_title, target_url, rationale):
    with _connection() as (conn, cursor):
        cursor.execute('''INSERT INTO seo_content_opportunities
            (keyword, intent, recommended_title, target_url, rationale)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (keyword) DO UPDATE SET intent=EXCLUDED.intent,
                recommended_title=EXCLUDED.recommended_title, target_url=EXCLUDED.target_url,
                rationale=EXCLUDED.rationale, updated_at=CURRENT_TIMESTAMP''',
            (keyword, intent, recommended_title, target_url or None, rationale))
        conn.commit()


def update_content_status(content_id, status):
    with _connection(dict_rows=True) as (conn, cursor):
        cursor.execute('''UPDATE seo_content_opportunities SET status=%s, updated_at=CURRENT_TIMESTAMP
            WHERE id=%s RETURNING *''', (status, content_id))
        row = cursor.fetchone()
        conn.commit()
        return dict(row) if row else None


def get_content_opportunity(content_id):
    with _connection(dict_rows=True) as (_, cursor):
        cursor.execute('SELECT * FROM seo_content_opportunities WHERE id=%s', (content_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def log_event(event_type, message, details=None):
    ensure_schema()
    with _connection() as (conn, cursor):
        cursor.execute('''INSERT INTO seo_agent_events (event_type, message, details)
            VALUES (%s, %s, %s)''', (event_type, message, psycopg2.extras.Json(details or {})))
        conn.commit()


def list_events(limit=12):
    ensure_schema()
    with _connection(dict_rows=True) as (_, cursor):
        cursor.execute('SELECT * FROM seo_agent_events ORDER BY created_at DESC LIMIT %s', (max(1, min(limit, 50)),))
        return [dict(row) for row in cursor.fetchall()]


def dashboard_snapshot():
    return {
        'config': get_config(),
        'latest_run': latest_run(),
        'issues': latest_issues(),
        'keywords': list_keywords(),
        'backlinks': list_backlinks(),
        'content_opportunities': list_content_opportunities(),
        'runs': list_runs(),
        'events': list_events(),
    }
