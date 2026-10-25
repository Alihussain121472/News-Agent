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
_schema_ensured = False


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
    global _schema_ensured
    if _schema_ensured:
        return
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
        '''CREATE TABLE IF NOT EXISTS seo_competitors (
            id SERIAL PRIMARY KEY,
            domain TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            target_keywords JSONB,
            top_headings JSONB,
            meta_info JSONB,
            content_gaps JSONB,
            benchmark_score INTEGER DEFAULT 50,
            notes TEXT,
            last_crawled_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS seo_daily_reports (
            id SERIAL PRIMARY KEY,
            report_date DATE UNIQUE NOT NULL,
            total_visits INTEGER DEFAULT 0,
            unique_visitors INTEGER DEFAULT 0,
            seo_score INTEGER DEFAULT 0,
            top_pages JSONB,
            top_referrers JSONB,
            keyword_summary JSONB,
            competitor_insights JSONB,
            actionable_recommendations JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS seo_traffic_alerts (
            id SERIAL PRIMARY KEY,
            alert_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            hourly_visits INTEGER NOT NULL,
            baseline_avg_visits NUMERIC(8,2) NOT NULL,
            surge_percentage NUMERIC(8,2) NOT NULL,
            recipient_email TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'sent',
            details JSONB
        )''',
    ]

    with _connection() as (conn, cursor):
        for statement in statements:
            cursor.execute(statement)
        cursor.execute("ALTER TABLE seo_keywords ADD COLUMN IF NOT EXISTS intent TEXT DEFAULT 'informational'")
        cursor.execute('ALTER TABLE seo_keywords ADD COLUMN IF NOT EXISTS target_url TEXT')
        cursor.execute('ALTER TABLE seo_keywords ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 3')
        cursor.execute('ALTER TABLE seo_keywords ADD COLUMN IF NOT EXISTS notes TEXT')
        cursor.execute('ALTER TABLE seo_agent_config ADD COLUMN IF NOT EXISTS ga_measurement_id TEXT')
        cursor.execute('ALTER TABLE seo_agent_config ADD COLUMN IF NOT EXISTS google_site_verification TEXT')
        cursor.execute("ALTER TABLE seo_agent_config ADD COLUMN IF NOT EXISTS alert_email TEXT DEFAULT 'syedali6160@gmail.com'")
        cursor.execute('ALTER TABLE seo_agent_config ADD COLUMN IF NOT EXISTS spike_threshold_pct INTEGER DEFAULT 100')
        cursor.execute('ALTER TABLE seo_agent_config ADD COLUMN IF NOT EXISTS spike_min_visits INTEGER DEFAULT 5')
        cursor.execute('ALTER TABLE site_visits ADD COLUMN IF NOT EXISTS referrer TEXT')
        cursor.execute('''INSERT INTO seo_agent_config (id, site_url, enabled, schedule_hours, max_pages, alert_email)
            VALUES (1, %s, TRUE, 6, 20, 'syedali6160@gmail.com') ON CONFLICT (id) DO NOTHING''', (DEFAULT_SITE_URL,))
        for keyword, intent, priority in DEFAULT_KEYWORDS:
            cursor.execute('''INSERT INTO seo_keywords (keyword, intent, priority)
                VALUES (%s, %s, %s) ON CONFLICT (keyword) DO NOTHING''', (keyword, intent, priority))
        cursor.execute('''INSERT INTO seo_competitors (domain, name, notes)
            VALUES ('techcrunch.com', 'TechCrunch', 'Leading global tech and startup journalism benchmark')
            ON CONFLICT (domain) DO NOTHING''')
        cursor.execute('''INSERT INTO seo_competitors (domain, name, notes)
            VALUES ('tldr.tech', 'TLDR Tech', 'Curated daily technology and developer newsletter benchmark')
            ON CONFLICT (domain) DO NOTHING''')
        conn.commit()
        _schema_ensured = True


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


def list_competitors():
    ensure_schema()
    with _connection(dict_rows=True) as (_, cursor):
        cursor.execute('SELECT * FROM seo_competitors ORDER BY updated_at DESC, id DESC')
        return [dict(row) for row in cursor.fetchall()]


def get_competitor(competitor_id):
    ensure_schema()
    with _connection(dict_rows=True) as (_, cursor):
        cursor.execute('SELECT * FROM seo_competitors WHERE id = %s', (competitor_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def save_competitor(domain, name, notes=None):
    ensure_schema()
    clean_domain = (domain or '').strip().lower()
    clean_name = (name or '').strip() or clean_domain
    with _connection(dict_rows=True) as (conn, cursor):
        cursor.execute('''INSERT INTO seo_competitors (domain, name, notes)
            VALUES (%s, %s, %s)
            ON CONFLICT (domain) DO UPDATE SET
                name=EXCLUDED.name,
                notes=COALESCE(EXCLUDED.notes, seo_competitors.notes),
                updated_at=CURRENT_TIMESTAMP
            RETURNING *''', (clean_domain, clean_name, (notes or '').strip() or None))
        row = dict(cursor.fetchone())
        conn.commit()
        return row


def update_competitor_analysis(competitor_id, analysis_data):
    ensure_schema()
    with _connection(dict_rows=True) as (conn, cursor):
        cursor.execute('''UPDATE seo_competitors SET
            target_keywords=%s,
            top_headings=%s,
            meta_info=%s,
            content_gaps=%s,
            benchmark_score=%s,
            last_crawled_at=CURRENT_TIMESTAMP,
            updated_at=CURRENT_TIMESTAMP
            WHERE id=%s RETURNING *''', (
                psycopg2.extras.Json(analysis_data.get('target_keywords') or []),
                psycopg2.extras.Json(analysis_data.get('top_headings') or []),
                psycopg2.extras.Json(analysis_data.get('meta_info') or {}),
                psycopg2.extras.Json(analysis_data.get('content_gaps') or []),
                int(analysis_data.get('benchmark_score') or 50),
                competitor_id,
            ))
        row = cursor.fetchone()
        conn.commit()
        return dict(row) if row else None


def delete_competitor(competitor_id):
    ensure_schema()
    with _connection() as (conn, cursor):
        cursor.execute('DELETE FROM seo_competitors WHERE id=%s', (competitor_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted


def save_daily_report(report_date, total_visits, unique_visitors, seo_score, top_pages, top_referrers, keyword_summary, competitor_insights, actionable_recommendations):
    ensure_schema()
    with _connection(dict_rows=True) as (conn, cursor):
        cursor.execute('''INSERT INTO seo_daily_reports
            (report_date, total_visits, unique_visitors, seo_score, top_pages, top_referrers, keyword_summary, competitor_insights, actionable_recommendations)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (report_date) DO UPDATE SET
                total_visits=EXCLUDED.total_visits,
                unique_visitors=EXCLUDED.unique_visitors,
                seo_score=EXCLUDED.seo_score,
                top_pages=EXCLUDED.top_pages,
                top_referrers=EXCLUDED.top_referrers,
                keyword_summary=EXCLUDED.keyword_summary,
                competitor_insights=EXCLUDED.competitor_insights,
                actionable_recommendations=EXCLUDED.actionable_recommendations,
                created_at=CURRENT_TIMESTAMP
            RETURNING *''', (
                report_date, total_visits, unique_visitors, seo_score,
                psycopg2.extras.Json(top_pages or []),
                psycopg2.extras.Json(top_referrers or []),
                psycopg2.extras.Json(keyword_summary or {}),
                psycopg2.extras.Json(competitor_insights or {}),
                psycopg2.extras.Json(actionable_recommendations or [])
            ))
        row = dict(cursor.fetchone())
        conn.commit()
        return row


def list_daily_reports(limit=14):
    ensure_schema()
    with _connection(dict_rows=True) as (_, cursor):
        cursor.execute('SELECT * FROM seo_daily_reports ORDER BY report_date DESC LIMIT %s', (max(1, min(limit, 60)),))
        return [dict(row) for row in cursor.fetchall()]


def latest_daily_report():
    reports = list_daily_reports(limit=1)
    return reports[0] if reports else None


def record_traffic_alert(hourly_visits, baseline_avg, surge_percentage, recipient_email, status='sent', details=None):
    ensure_schema()
    with _connection(dict_rows=True) as (conn, cursor):
        cursor.execute('''INSERT INTO seo_traffic_alerts
            (hourly_visits, baseline_avg_visits, surge_percentage, recipient_email, status, details)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING *''', (
                hourly_visits, baseline_avg, surge_percentage, recipient_email, status,
                psycopg2.extras.Json(details or {})
            ))
        row = dict(cursor.fetchone())
        conn.commit()
        return row


def list_traffic_alerts(limit=10):
    ensure_schema()
    with _connection(dict_rows=True) as (_, cursor):
        cursor.execute('SELECT * FROM seo_traffic_alerts ORDER BY alert_time DESC LIMIT %s', (max(1, min(limit, 50)),))
        return [dict(row) for row in cursor.fetchall()]


def recent_alert_count(hours=6):
    ensure_schema()
    with _connection() as (_, cursor):
        cursor.execute("SELECT COUNT(*) FROM seo_traffic_alerts WHERE alert_time >= CURRENT_TIMESTAMP - INTERVAL '%s hours' AND status='sent'", (hours,))
        return cursor.fetchone()[0] or 0


def update_integrations(ga_measurement_id=None, google_site_verification=None, alert_email=None, spike_threshold_pct=100, spike_min_visits=5):
    ensure_schema()
    with _connection(dict_rows=True) as (conn, cursor):
        cursor.execute('''UPDATE seo_agent_config SET
            ga_measurement_id=%s,
            google_site_verification=%s,
            alert_email=COALESCE(%s, alert_email),
            spike_threshold_pct=%s,
            spike_min_visits=%s,
            updated_at=CURRENT_TIMESTAMP
            WHERE id=1 RETURNING *''', (
                (ga_measurement_id or '').strip() or None,
                (google_site_verification or '').strip() or None,
                (alert_email or '').strip() or 'syedali6160@gmail.com',
                int(spike_threshold_pct or 100),
                int(spike_min_visits or 5),
            ))
        row = dict(cursor.fetchone())
        conn.commit()
        return row


def get_visitor_analytics(days=30):
    ensure_schema()
    with _connection(dict_rows=True) as (_, cursor):
        cursor.execute('''
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT ip_address) as unique_ips,
                COUNT(*) FILTER (WHERE visit_time >= CURRENT_DATE) as today_total,
                COUNT(DISTINCT ip_address) FILTER (WHERE visit_time >= CURRENT_DATE) as today_unique,
                COUNT(*) FILTER (WHERE visit_time >= CURRENT_DATE - INTERVAL '1 day' AND visit_time < CURRENT_DATE) as yest_total
            FROM site_visits
        ''')
        totals_row = cursor.fetchone() or {}
        total_visits = int(totals_row.get('total') or 0)
        unique_visitors = int(totals_row.get('unique_ips') or 0)
        today_visits = int(totals_row.get('today_total') or 0)
        today_unique = int(totals_row.get('today_unique') or 0)
        yesterday_visits = int(totals_row.get('yest_total') or 0)

        cursor.execute('''
            SELECT DATE(visit_time) as date, COUNT(*) as visits, COUNT(DISTINCT ip_address) as unique_visits
            FROM site_visits
            WHERE visit_time >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY DATE(visit_time)
            ORDER BY date ASC
        ''', (int(days),))
        daily_history = []
        for r in cursor.fetchall():
            daily_history.append({
                'date': str(r['date']),
                'visits': int(r.get('visits') or 0),
                'unique': int(r.get('unique_visits') or 0)
            })

        cursor.execute('''
            SELECT page, COUNT(*) as count, COUNT(DISTINCT ip_address) as unique_visits
            FROM site_visits
            GROUP BY page
            ORDER BY count DESC
            LIMIT 10
        ''')
        top_pages = []
        for r in cursor.fetchall():
            cnt = int(r.get('count') or 0)
            pct = round((cnt / max(1, total_visits)) * 100, 1)
            top_pages.append({
                'page': r.get('page') or '/',
                'count': cnt,
                'unique': int(r.get('unique_visits') or 0),
                'percentage': pct
            })

        cursor.execute('''
            SELECT COALESCE(NULLIF(referrer, ''), 'Direct / Bookmark') as source, COUNT(*) as count
            FROM site_visits
            GROUP BY source
            ORDER BY count DESC
            LIMIT 10
        ''')
        top_referrers = []
        for r in cursor.fetchall():
            cnt = int(r.get('count') or 0)
            pct = round((cnt / max(1, total_visits)) * 100, 1)
            top_referrers.append({
                'source': r.get('source') or 'Direct',
                'count': cnt,
                'percentage': pct
            })

        cursor.execute('SELECT user_agent FROM site_visits ORDER BY id DESC LIMIT 500')
        agents = [r.get('user_agent') or '' for r in cursor.fetchall()]

        devices = {'desktop': 0, 'mobile': 0, 'tablet': 0}
        browsers = {'chrome': 0, 'safari': 0, 'firefox': 0, 'edge': 0, 'other': 0}
        for ua in agents:
            ua_lower = ua.lower()
            if 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
                devices['mobile'] += 1
            elif 'ipad' in ua_lower or 'tablet' in ua_lower:
                devices['tablet'] += 1
            else:
                devices['desktop'] += 1

            if 'edg/' in ua_lower or 'edge/' in ua_lower:
                browsers['edge'] += 1
            elif 'chrome/' in ua_lower:
                browsers['chrome'] += 1
            elif 'safari/' in ua_lower and 'chrome' not in ua_lower:
                browsers['safari'] += 1
            elif 'firefox/' in ua_lower:
                browsers['firefox'] += 1
            else:
                browsers['other'] += 1

        return {
            'total_visits': total_visits,
            'unique_visitors': unique_visitors,
            'today_visits': today_visits,
            'today_unique': today_unique,
            'yesterday_visits': yesterday_visits,
            'avg_daily_visits': round(total_visits / max(1, len(daily_history) or 1), 1),
            'daily_trend': daily_history,
            'top_pages': top_pages,
            'top_referrers': top_referrers,
            'devices': devices,
            'browsers': browsers,
        }


def dashboard_snapshot():
    cfg = get_config()
    return {
        'config': cfg,
        'latest_run': latest_run(),
        'issues': latest_issues(),
        'keywords': list_keywords(),
        'backlinks': list_backlinks(),
        'content_opportunities': list_content_opportunities(),
        'competitors': list_competitors(),
        'daily_reports': list_daily_reports(limit=7),
        'traffic_alerts': list_traffic_alerts(limit=5),
        'visitor_analytics': get_visitor_analytics(days=30),
        'runs': list_runs(),
        'events': list_events(),
    }
