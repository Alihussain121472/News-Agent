import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class NewsDatabase:
    def __init__(self, db_path: str = 'news_history.db'):
        self.db_path = db_path
        self.init_database()

    def _ensure_table_columns(self, conn: sqlite3.Connection, table_name: str, columns: List[str]) -> None:
        cursor = conn.cursor()
        cursor.execute(f'PRAGMA table_info({table_name})')
        existing = {row[1] for row in cursor.fetchall()}
        for column in columns:
            column_name = column.split()[0].strip()
            if column_name not in existing:
                cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column}')
                logger.info(f'Added missing column {column_name} to {table_name}')

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, summary TEXT, source TEXT, url TEXT,
            published TEXT, fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            why_important TEXT, future_change TEXT, why_care TEXT,
            sent_in_email BOOLEAN DEFAULT 1)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            recipient TEXT NOT NULL, subject TEXT, article_count INTEGER,
            status TEXT DEFAULT 'success', error_message TEXT)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS agent_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL, message TEXT, details TEXT)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS registered_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL, name TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1, total_emails_received INTEGER DEFAULT 0,
            last_email_sent TIMESTAMP, last_login_at TIMESTAMP,
            login_count INTEGER DEFAULT 0, password_hash TEXT,
            role TEXT DEFAULT 'user', program_notifications BOOLEAN DEFAULT 1)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS site_visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            page TEXT NOT NULL, ip_address TEXT, user_agent TEXT, email TEXT)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS user_login_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            email TEXT NOT NULL, source TEXT DEFAULT 'portal')''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            name TEXT NOT NULL, email TEXT NOT NULL, subject TEXT NOT NULL,
            message TEXT NOT NULL, status TEXT DEFAULT 'new')''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS daily_digest_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date DATE NOT NULL, executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            recipient_count INTEGER DEFAULT 0, success_count INTEGER DEFAULT 0,
            article_count INTEGER DEFAULT 0, status TEXT DEFAULT 'success')''')

        # Feature 1: Student programs table
        cursor.execute('''CREATE TABLE IF NOT EXISTS student_programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, company TEXT NOT NULL, description TEXT,
            registration_url TEXT, deadline DATE, launch_date DATE,
            category TEXT DEFAULT 'program', is_active BOOLEAN DEFAULT 1,
            notified_at TIMESTAMP, notify_before_days INTEGER DEFAULT 7,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Feature 2: User activity log
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL, action TEXT NOT NULL, detail TEXT, page TEXT,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Feature 3: Admin notes on users
        cursor.execute('''CREATE TABLE IF NOT EXISTS admin_user_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL, note TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        self._ensure_table_columns(conn, 'registered_users', [
            'last_login_at TIMESTAMP', 'login_count INTEGER DEFAULT 0',
            'password_hash TEXT', 'role TEXT DEFAULT "user"',
            'program_notifications BOOLEAN DEFAULT 1'])
        self._ensure_table_columns(conn, 'student_programs', [
            'notified_at TIMESTAMP', 'notify_before_days INTEGER DEFAULT 7'])

        for idx_sql in [
            'CREATE INDEX IF NOT EXISTS idx_fetched_at ON news_articles(fetched_at DESC)',
            'CREATE INDEX IF NOT EXISTS idx_sent_at ON email_logs(sent_at DESC)',
            'CREATE INDEX IF NOT EXISTS idx_user_email ON registered_users(email)',
            'CREATE INDEX IF NOT EXISTS idx_active_users ON registered_users(is_active)',
            'CREATE INDEX IF NOT EXISTS idx_activity_email ON user_activity_log(email)',
            'CREATE INDEX IF NOT EXISTS idx_programs_active ON student_programs(is_active)',
        ]:
            cursor.execute(idx_sql)

        conn.commit()
        conn.close()
        logger.info(f'Database initialized at {self.db_path}')
        self.seed_default_programs()

    # ── News articles ─────────────────────────────────────────────────────────

    def save_news_article(self, article: Dict[str, Any]) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO news_articles
            (title,summary,source,url,published,why_important,future_change,why_care,sent_in_email)
            VALUES (?,?,?,?,?,?,?,?,?)''', (
            article.get('title', ''), article.get('summary', ''),
            article.get('source', ''), article.get('url', ''),
            article.get('published', ''), article.get('why_important', ''),
            article.get('future_change', ''), article.get('why_care', ''),
            article.get('sent_in_email', True)))
        article_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return article_id

    def save_news_batch(self, articles: List[Dict[str, Any]]) -> int:
        count = sum(1 for a in articles if self.save_news_article(a))
        logger.info(f'Saved {count} articles to database')
        return count

    def get_recent_articles(self, limit: int = 50, days: int = None) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            cursor.execute('SELECT * FROM news_articles WHERE fetched_at >= ? ORDER BY fetched_at DESC LIMIT ?', (cutoff, limit))
        else:
            cursor.execute('SELECT * FROM news_articles ORDER BY fetched_at DESC LIMIT ?', (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_articles_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM news_articles WHERE fetched_at BETWEEN ? AND ? ORDER BY fetched_at DESC', (start_date, end_date))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def search_articles(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        p = f'%{query}%'
        cursor.execute('SELECT * FROM news_articles WHERE title LIKE ? OR summary LIKE ? ORDER BY fetched_at DESC LIMIT ?', (p, p, limit))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def cleanup_old_articles(self, months: int = 3) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cutoff = (datetime.now() - timedelta(days=months * 30)).isoformat()
        cursor.execute('DELETE FROM news_articles WHERE fetched_at < ?', (cutoff,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        logger.info(f'Cleaned up {deleted} articles')
        return deleted

    # ── Email / agent logs ────────────────────────────────────────────────────

    def log_email_sent(self, recipient, subject, article_count, status='success', error_message=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO email_logs (recipient,subject,article_count,status,error_message) VALUES (?,?,?,?,?)',
                       (recipient, subject, article_count, status, error_message))
        conn.commit()
        conn.close()

    def log_agent_event(self, event_type: str, message: str, details: str = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO agent_status (event_type,message,details) VALUES (?,?,?)', (event_type, message, details))
        conn.commit()
        conn.close()

    def get_email_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM email_logs ORDER BY sent_at DESC LIMIT ?', (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_agent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM agent_status ORDER BY status_time DESC LIMIT ?', (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # ── User management ───────────────────────────────────────────────────────

    def register_user(self, email: str, name: str = None) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO registered_users (email,name,is_active,role) VALUES (?,?,1,'user')", (email, name))
            conn.commit()
            logger.info(f'New user registered: {email}')
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM registered_users WHERE email = ? LIMIT 1', (email.strip().lower(),))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def create_or_update_user_account(self, email: str, name: str = None, password_hash: str = None) -> str:
        normalized = email.strip().lower()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, password_hash FROM registered_users WHERE email = ? LIMIT 1', (normalized,))
        existing = cursor.fetchone()
        if not existing:
            cursor.execute("INSERT INTO registered_users (email,name,is_active,role,password_hash) VALUES (?,?,1,'user',?)",
                           (normalized, name, password_hash))
            conn.commit()
            conn.close()
            return 'created'
        user_id, existing_name, existing_hash = existing
        final_name = name if name else existing_name
        final_hash = password_hash if password_hash else existing_hash
        cursor.execute('UPDATE registered_users SET name=?, password_hash=?, role="user", is_active=1 WHERE id=?',
                       (final_name, final_hash, user_id))
        conn.commit()
        conn.close()
        return 'updated'

    def get_user_dashboard_summary(self, email: str) -> Dict[str, Any]:
        normalized = email.strip().lower()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM registered_users WHERE email = ? LIMIT 1', (normalized,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {'registered': False, 'total_emails_received': 0, 'login_count': 0,
                    'last_email_sent': None, 'last_login_at': None, 'member_since': None, 'is_active': False}
        cursor.execute('SELECT COUNT(*) FROM user_login_events WHERE email = ?', (normalized,))
        login_events = cursor.fetchone()[0]
        u = dict(row)
        conn.close()
        return {
            'registered': True,
            'total_emails_received': u.get('total_emails_received') or 0,
            'login_count': max(u.get('login_count') or 0, login_events),
            'last_email_sent': u.get('last_email_sent'),
            'last_login_at': u.get('last_login_at'),
            'member_since': u.get('registered_at'),
            'is_active': bool(u.get('is_active')),
            'program_notifications': bool(u.get('program_notifications', 1)),
        }

    def get_all_active_users(self) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT email FROM registered_users WHERE is_active = 1 ORDER BY registered_at ASC')
        emails = [r[0] for r in cursor.fetchall()]
        conn.close()
        return emails

    def get_program_subscribers(self) -> List[str]:
        """Users who want program notifications."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT email FROM registered_users WHERE is_active=1 AND COALESCE(program_notifications,1)=1')
        emails = [r[0] for r in cursor.fetchall()]
        conn.close()
        return emails

    def enable_user_program_notifications(self, email: str, name: str = None) -> bool:
        """Ensure user exists, is active, and has program notifications enabled."""
        normalized = email.strip().lower()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM registered_users WHERE email = ? LIMIT 1', (normalized,))
        row = cursor.fetchone()
        if not row:
            final_name = name or normalized.split('@')[0].replace('.', ' ').title()
            cursor.execute("INSERT INTO registered_users (email,name,is_active,role,program_notifications) VALUES (?,?,1,'user',1)",
                           (normalized, final_name))
        else:
            final_name = name if name else row[1]
            cursor.execute("UPDATE registered_users SET name=?, is_active=1, program_notifications=1 WHERE email=?",
                           (final_name, normalized))
        conn.commit()
        conn.close()
        return True

    def update_user_email_sent(self, email: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE registered_users SET last_email_sent=CURRENT_TIMESTAMP, total_emails_received=total_emails_received+1 WHERE email=?', (email,))
        conn.commit()
        conn.close()

    def deactivate_user(self, email: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE registered_users SET is_active=0 WHERE email=?', (email,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def get_registered_users(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM registered_users ORDER BY registered_at DESC LIMIT ?', (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_user_count(self) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM registered_users WHERE is_active=1')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    # ── Visit / login tracking ────────────────────────────────────────────────

    def record_user_login(self, email: str, source: str = 'portal') -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user_login_events (email,source) VALUES (?,?)', (email.strip().lower(), source))
        cursor.execute('UPDATE registered_users SET last_login_at=CURRENT_TIMESTAMP, login_count=COALESCE(login_count,0)+1 WHERE email=?',
                       (email.strip().lower(),))
        conn.commit()
        conn.close()

    def record_site_visit(self, page: str, ip_address: str = None, user_agent: str = None, email: str = None) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO site_visits (page,ip_address,user_agent,email) VALUES (?,?,?,?)',
                       (page or '/', ip_address or 'unknown', (user_agent or '')[:250],
                        email.strip().lower() if email else None))
        conn.commit()
        conn.close()

    def get_visitor_stats(self) -> Dict[str, int]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('SELECT COUNT(*) FROM site_visits')
        total = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(DISTINCT ip_address) FROM site_visits')
        unique = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM site_visits WHERE visit_time >= ?', (month_start,))
        monthly = cursor.fetchone()[0]
        conn.close()
        return {'total_visits': total, 'unique_visitors': unique, 'monthly_visits': monthly}

    def get_monthly_login_stats(self) -> Dict[str, int]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('SELECT COUNT(*) FROM user_login_events WHERE login_time >= ?', (month_start,))
        monthly = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(DISTINCT email) FROM user_login_events WHERE login_time >= ?', (month_start,))
        users = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM registered_users WHERE is_active=1')
        active = cursor.fetchone()[0]
        conn.close()
        return {'monthly_logins': monthly, 'users_this_month': users, 'active_users': active}

    def get_recent_user_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''SELECT email, source AS action, login_time AS event_time FROM user_login_events
            UNION ALL SELECT email, 'signup' AS action, registered_at AS event_time FROM registered_users
            ORDER BY event_time DESC LIMIT ?''', (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # ── User activity log ─────────────────────────────────────────────────────

    def log_user_activity(self, email: str, action: str, detail: str = None, page: str = None) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user_activity_log (email,action,detail,page) VALUES (?,?,?,?)',
                       (email.strip().lower(), action, detail, page))
        conn.commit()
        conn.close()

    def get_user_activity_log(self, email: str, limit: int = 100) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_activity_log WHERE email=? ORDER BY logged_at DESC LIMIT ?',
                       (email.strip().lower(), limit))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_user_activity_stats(self, email: str) -> Dict[str, Any]:
        normalized = email.strip().lower()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(*) FROM user_activity_log WHERE email=?', (normalized,))
        total = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM user_activity_log WHERE email=? AND date(logged_at)=?', (normalized, today))
        today_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM user_activity_log WHERE email=? AND date(logged_at)>=?', (normalized, week_ago))
        week_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(DISTINCT date(logged_at)) FROM user_activity_log WHERE email=?', (normalized,))
        active_days = cursor.fetchone()[0]
        cursor.execute('SELECT action, COUNT(*) as cnt FROM user_activity_log WHERE email=? GROUP BY action ORDER BY cnt DESC LIMIT 5', (normalized,))
        top_actions = [{'action': r[0], 'count': r[1]} for r in cursor.fetchall()]
        cursor.execute('SELECT COUNT(*) FROM email_logs WHERE recipient=? AND status="success"', (normalized,))
        emails_received = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM user_login_events WHERE email=?', (normalized,))
        total_logins = cursor.fetchone()[0]
        conn.close()
        return {
            'total_actions': total, 'today_actions': today_count, 'week_actions': week_count,
            'active_days': active_days, 'top_actions': top_actions,
            'emails_received': emails_received, 'total_logins': total_logins,
        }

    def get_user_daily_progress(self, email: str) -> Dict[str, Any]:
        """Get detailed daily progress for the user dashboard tracking feature."""
        normalized = email.strip().lower()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(*) FROM user_activity_log WHERE email=? AND date(logged_at)=?', (normalized, today))
        total_today = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM user_activity_log WHERE email=? AND date(logged_at)=? AND action='page_visit'", (normalized, today))
        pages_today = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM user_activity_log WHERE email=? AND date(logged_at)=? AND action IN ('articles_view','dashboard_view')", (normalized, today))
        reads_today = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM user_activity_log WHERE email=? AND date(logged_at)=? AND action='programs_view'", (normalized, today))
        programs_today = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM user_login_events WHERE email=? AND date(login_time)=?", (normalized, today))
        logins_today = cursor.fetchone()[0]
        cursor.execute('SELECT action, COUNT(*) as cnt FROM user_activity_log WHERE email=? AND date(logged_at)=? GROUP BY action ORDER BY cnt DESC', (normalized, today))
        today_breakdown = [{'action': r[0], 'count': r[1]} for r in cursor.fetchall()]
        cursor.execute('SELECT MIN(logged_at) FROM user_activity_log WHERE email=? AND date(logged_at)=?', (normalized, today))
        first_action = cursor.fetchone()[0]
        cursor.execute('SELECT MAX(logged_at) FROM user_activity_log WHERE email=? AND date(logged_at)=?', (normalized, today))
        last_action = cursor.fetchone()[0]
        conn.close()
        return {
            'total_actions': total_today, 'pages_visited': pages_today,
            'articles_read': reads_today, 'programs_explored': programs_today,
            'logins': logins_today, 'breakdown': today_breakdown,
            'first_action': first_action, 'last_action': last_action,
            'date': today,
        }

    def get_user_weekly_summary(self, email: str) -> List[Dict[str, Any]]:
        """Get per-day activity counts for the last 7 days for chart display."""
        normalized = email.strip().lower()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        days = []
        for i in range(6, -1, -1):
            d = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            cursor.execute('SELECT COUNT(*) FROM user_activity_log WHERE email=? AND date(logged_at)=?', (normalized, d))
            count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM user_login_events WHERE email=? AND date(login_time)=?', (normalized, d))
            logins = cursor.fetchone()[0]
            day_label = (datetime.now() - timedelta(days=i)).strftime('%a')
            days.append({'date': d, 'label': day_label, 'actions': count, 'logins': logins})
        conn.close()
        return days

    # ── Admin user monitoring ─────────────────────────────────────────────────

    def get_all_users_with_stats(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''SELECT u.*,
            (SELECT COUNT(*) FROM user_login_events l WHERE l.email=u.email) AS login_events,
            (SELECT COUNT(*) FROM user_activity_log a WHERE a.email=u.email) AS activity_count,
            (SELECT COUNT(*) FROM email_logs e WHERE e.recipient=u.email AND e.status="success") AS emails_received
            FROM registered_users u ORDER BY u.registered_at DESC''')
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_user_full_activity(self, email: str, limit: int = 200) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT action, detail, page, logged_at AS event_time, 'activity' AS source FROM user_activity_log WHERE email=?
            UNION ALL
            SELECT source AS action, NULL AS detail, NULL AS page, login_time AS event_time, 'login' AS source FROM user_login_events WHERE email=?
            UNION ALL
            SELECT 'email_received' AS action, subject AS detail, NULL AS page, sent_at AS event_time, 'email' AS source FROM email_logs WHERE recipient=? AND status='success'
            ORDER BY event_time DESC LIMIT ?''', (email, email, email, limit))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_admin_dashboard_stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute('SELECT COUNT(*) FROM registered_users WHERE is_active=1')
        active_users = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM registered_users WHERE date(registered_at)=?', (today,))
        new_today = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM user_login_events WHERE date(login_time)=?', (today,))
        logins_today = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM user_activity_log WHERE logged_at >= ?', (week_ago,))
        week_activity = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM student_programs WHERE is_active=1')
        active_programs = cursor.fetchone()[0]
        conn.close()
        return {
            'active_users': active_users, 'new_users_today': new_today,
            'logins_today': logins_today, 'week_activity': week_activity,
            'active_programs': active_programs,
        }

    # ── Student programs ──────────────────────────────────────────────────────

    def add_student_program(self, title: str, company: str, description: str,
                             registration_url: str, deadline: str = None,
                             launch_date: str = None, category: str = 'program',
                             notify_before_days: int = 7) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO student_programs
            (title,company,description,registration_url,deadline,launch_date,category,notify_before_days)
            VALUES (?,?,?,?,?,?,?,?)''',
            (title, company, description, registration_url, deadline, launch_date, category, notify_before_days))
        prog_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f'Added program: {title}')
        return prog_id

    def get_active_programs(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM student_programs WHERE is_active=1 ORDER BY created_at DESC LIMIT ?', (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_all_programs(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM student_programs ORDER BY created_at DESC LIMIT ?', (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_programs_to_notify(self) -> List[Dict[str, Any]]:
        """Programs whose launch_date is within notify_before_days and haven't been notified yet."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM student_programs
            WHERE is_active=1 AND notified_at IS NULL AND launch_date IS NOT NULL
            AND date(launch_date) <= date('now', '+' || notify_before_days || ' days')
            AND date(launch_date) >= date('now')''')
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def mark_program_notified(self, program_id: int) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE student_programs SET notified_at=CURRENT_TIMESTAMP WHERE id=?', (program_id,))
        conn.commit()
        conn.close()

    def delete_program(self, program_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE student_programs SET is_active=0 WHERE id=?', (program_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def seed_default_programs(self) -> None:
        """Seed real-world student programs if the table is empty."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM student_programs')
        if cursor.fetchone()[0] == 0:
            programs = [
                {
                    'title': 'Google Developer Student Clubs (GDSC)',
                    'company': 'Google',
                    'description': 'University-based community groups for students interested in Google developer technologies. Gain leadership and technical skills.',
                    'registration_url': 'https://developers.google.com/community/gdsc',
                    'category': 'program',
                    'launch_date': f'{datetime.now().year}-08-15'
                },
                {
                    'title': 'Google Summer of Code (GSoC)',
                    'company': 'Google',
                    'description': 'A global, online program focused on bringing new contributors into open source software development.',
                    'registration_url': 'https://summerofcode.withgoogle.com/',
                    'category': 'internship',
                    'launch_date': f'{datetime.now().year + 1}-03-01'
                },
                {
                    'title': 'Microsoft Imagine Cup',
                    'company': 'Microsoft',
                    'description': 'Global student technology competition focused on finding solutions to real-world problems using Microsoft technologies.',
                    'registration_url': 'https://imaginecup.microsoft.com/',
                    'category': 'competition',
                    'launch_date': f'{datetime.now().year}-10-01'
                },
                {
                    'title': 'AWS Academy & Educate',
                    'company': 'Amazon',
                    'description': 'Provides students with resources for building skills in the cloud, including free training and AWS credits.',
                    'registration_url': 'https://aws.amazon.com/education/awseducate/',
                    'category': 'certification',
                    'launch_date': f'{datetime.now().year}-09-01'
                },
                {
                    'title': "NASA L'SPACE Academy",
                    'company': 'NASA',
                    'description': 'Free, online, interactive program for STEM students to gain project-based experience in space exploration.',
                    'registration_url': 'https://www.lspace.asu.edu/',
                    'category': 'program',
                    'launch_date': f'{datetime.now().year}-08-20'
                }
            ]
            for p in programs:
                cursor.execute('''INSERT INTO student_programs
                    (title,company,description,registration_url,launch_date,category)
                    VALUES (?,?,?,?,?,?)''',
                    (p['title'], p['company'], p['description'], p['registration_url'], p['launch_date'], p['category']))
            conn.commit()
            logger.info("Seeded default student programs.")
        conn.close()

    # ── Contact messages ──────────────────────────────────────────────────────

    def record_contact_message(self, name, email, subject, message) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO contact_messages (name,email,subject,message) VALUES (?,?,?,?)', (name, email, subject, message))
        conn.commit()
        msg_id = cursor.lastrowid
        conn.close()
        return msg_id

    def get_contact_messages(self, limit: int = 100, status: str = None) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if status:
            cursor.execute('SELECT * FROM contact_messages WHERE status=? ORDER BY submitted_at DESC LIMIT ?', (status, limit))
        else:
            cursor.execute('SELECT * FROM contact_messages ORDER BY submitted_at DESC LIMIT ?', (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # ── Digest run tracking ───────────────────────────────────────────────────

    def has_daily_digest_run(self, run_date: Optional[str] = None) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        date_key = run_date or datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT 1 FROM daily_digest_runs WHERE run_date=? LIMIT 1', (date_key,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def record_daily_digest_run(self, recipient_count, success_count, article_count, status='success') -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        run_date = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('INSERT INTO daily_digest_runs (run_date,recipient_count,success_count,article_count,status) VALUES (?,?,?,?,?)',
                       (run_date, recipient_count, success_count, article_count, status))
        conn.commit()
        conn.close()

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_statistics(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM news_articles')
        total_articles = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM news_articles WHERE fetched_at >= ?', ((datetime.now()-timedelta(days=7)).isoformat(),))
        week = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM news_articles WHERE fetched_at >= ?', ((datetime.now()-timedelta(days=30)).isoformat(),))
        month = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM email_logs')
        total_emails = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM email_logs WHERE status="success"')
        success_emails = cursor.fetchone()[0]
        cursor.execute('SELECT sent_at FROM email_logs ORDER BY sent_at DESC LIMIT 1')
        last_e = cursor.fetchone()
        login_stats = self.get_monthly_login_stats()
        visitor_stats = self.get_visitor_stats()
        conn.close()
        return {
            'total_articles': total_articles, 'articles_last_week': week,
            'articles_last_month': month, 'total_emails': total_emails,
            'successful_emails': success_emails,
            'last_email_sent': last_e[0] if last_e else None,
            'monthly_logins': login_stats['monthly_logins'],
            'users_this_month': login_stats['users_this_month'],
            'active_users': login_stats['active_users'],
            'total_visits': visitor_stats['total_visits'],
            'unique_visitors': visitor_stats['unique_visitors'],
            'monthly_visits': visitor_stats['monthly_visits'],
        }
