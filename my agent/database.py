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
        """Safely add missing columns to an existing SQLite table."""
        cursor = conn.cursor()
        cursor.execute(f'PRAGMA table_info({table_name})')
        existing = {row[1] for row in cursor.fetchall()}

        for column in columns:
            column_name = column.split()[0].strip()
            if column_name not in existing:
                cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column}')
                logger.info(f'Added missing column {column_name} to {table_name}')

    def init_database(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT,
                source TEXT,
                url TEXT,
                published TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                why_important TEXT,
                future_change TEXT,
                why_care TEXT,
                sent_in_email BOOLEAN DEFAULT 1
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                recipient TEXT NOT NULL,
                subject TEXT,
                article_count INTEGER,
                status TEXT,
                error_message TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                message TEXT,
                details TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS registered_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                last_email_sent TIMESTAMP,
                total_emails_received INTEGER DEFAULT 0,
                last_login_at TIMESTAMP,
                login_count INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_digest_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                recipient_count INTEGER,
                success_count INTEGER,
                article_count INTEGER,
                status TEXT DEFAULT 'success'
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_login_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                source TEXT DEFAULT 'portal',
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS site_visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                page TEXT,
                ip_address TEXT,
                user_agent TEXT,
                email TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'new',
                response TEXT,
                responded_at TIMESTAMP
            )
        ''')

        self._ensure_table_columns(conn, 'registered_users', ['last_login_at TIMESTAMP', 'login_count INTEGER DEFAULT 0', 'password_hash TEXT', 'role TEXT DEFAULT "user"'])
        self._ensure_table_columns(conn, 'daily_digest_runs', ['run_date TEXT', 'sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP', 'recipient_count INTEGER', 'success_count INTEGER', 'article_count INTEGER', 'status TEXT DEFAULT "success"'])
        self._ensure_table_columns(conn, 'user_login_events', ['email TEXT', 'source TEXT DEFAULT "portal"', 'login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP'])
        self._ensure_table_columns(conn, 'site_visits', ['visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP', 'page TEXT', 'ip_address TEXT', 'user_agent TEXT', 'email TEXT'])

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_fetched_at ON news_articles(fetched_at DESC)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sent_at ON email_logs(sent_at DESC)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_email ON registered_users(email)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_active_users ON registered_users(is_active)
        ''')

        conn.commit()
        conn.close()
        logger.info(f'Database initialized at {self.db_path}')

    def save_news_article(self, article: Dict[str, Any]) -> int:
        """Save a single news article to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO news_articles
            (title, summary, source, url, published, why_important, future_change, why_care, sent_in_email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            article.get('title', ''),
            article.get('summary', ''),
            article.get('source', ''),
            article.get('url', ''),
            article.get('published', ''),
            article.get('why_important', ''),
            article.get('future_change', ''),
            article.get('why_care', ''),
            article.get('sent_in_email', True)
        ))

        article_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return article_id

    def save_news_batch(self, articles: List[Dict[str, Any]]) -> int:
        """Save multiple news articles at once."""
        count = 0
        for article in articles:
            self.save_news_article(article)
            count += 1
        logger.info(f'Saved {count} articles to database')
        return count

    def log_email_sent(self, recipient: str, subject: str, article_count: int,
                       status: str = 'success', error_message: str = None):
        """Log an email sending event."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO email_logs (recipient, subject, article_count, status, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (recipient, subject, article_count, status, error_message))

        conn.commit()
        conn.close()

    def log_agent_event(self, event_type: str, message: str, details: str = None):
        """Log agent activity."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO agent_status (event_type, message, details)
            VALUES (?, ?, ?)
        ''', (event_type, message, details))

        conn.commit()
        conn.close()

    def get_recent_articles(self, limit: int = 50, days: int = None) -> List[Dict[str, Any]]:
        """Get recent articles, optionally filtered by days."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            cursor.execute('''
                SELECT * FROM news_articles
                WHERE fetched_at >= ?
                ORDER BY fetched_at DESC
                LIMIT ?
            ''', (cutoff_date.isoformat(), limit))
        else:
            cursor.execute('''
                SELECT * FROM news_articles
                ORDER BY fetched_at DESC
                LIMIT ?
            ''', (limit,))

        articles = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return articles

    def get_articles_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get articles within a specific date range."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM news_articles
            WHERE fetched_at BETWEEN ? AND ?
            ORDER BY fetched_at DESC
        ''', (start_date, end_date))

        articles = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return articles

    def get_email_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get email sending history."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM email_logs
            ORDER BY sent_at DESC
            LIMIT ?
        ''', (limit,))

        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs

    def get_agent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get agent activity logs."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM agent_status
            ORDER BY status_time DESC
            LIMIT ?
        ''', (limit,))

        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs

    def record_user_login(self, email: str, source: str = 'portal') -> None:
        """Track a portal or subscription login event for analytics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO user_login_events (email, source, login_time)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (email.strip().lower(), source))

        cursor.execute('''
            UPDATE registered_users
            SET last_login_at = CURRENT_TIMESTAMP,
                login_count = COALESCE(login_count, 0) + 1
            WHERE email = ?
        ''', (email.strip().lower(),))

        conn.commit()
        conn.close()

    def record_site_visit(self, page: str, ip_address: str = None, user_agent: str = None, email: str = None) -> None:
        """Record a general site visit for dashboard analytics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO site_visits (page, ip_address, user_agent, email)
            VALUES (?, ?, ?, ?)
        ''', (page or '/', ip_address or 'unknown', (user_agent or '')[:250], (email or '').strip().lower() if email else None))

        conn.commit()
        conn.close()

    def get_visitor_stats(self) -> Dict[str, int]:
        """Get overall and monthly web traffic metrics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('SELECT COUNT(*) FROM site_visits')
        total_visits = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT ip_address) FROM site_visits')
        unique_visitors = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM site_visits WHERE visit_time >= ?', (current_month_start,))
        monthly_visits = cursor.fetchone()[0]

        conn.close()

        return {
            'total_visits': total_visits,
            'unique_visitors': unique_visitors,
            'monthly_visits': monthly_visits,
        }

    def get_recent_user_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return recent site activity including user signups and logins."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT email, source AS action, login_time AS event_time
            FROM user_login_events
            UNION ALL
            SELECT email, 'signup' AS action, registered_at AS event_time
            FROM registered_users
            ORDER BY event_time DESC
            LIMIT ?
        ''', (limit,))

        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_monthly_login_stats(self) -> Dict[str, int]:
        """Return monthly login analytics for the dashboard."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
            SELECT COUNT(*) FROM user_login_events
            WHERE login_time >= ?
        ''', (current_month_start,))
        monthly_logins = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(DISTINCT email) FROM user_login_events
            WHERE login_time >= ?
        ''', (current_month_start,))
        users_this_month = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM registered_users WHERE is_active = 1')
        active_users = cursor.fetchone()[0]

        conn.close()

        return {
            'monthly_logins': monthly_logins,
            'users_this_month': users_this_month,
            'active_users': active_users,
        }

    def has_daily_digest_run(self, run_date: Optional[str] = None) -> bool:
        """Return True if the digest has already been sent for the current day."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        date_key = run_date or datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT 1 FROM daily_digest_runs
            WHERE run_date = ?
            LIMIT 1
        ''', (date_key,))

        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def record_daily_digest_run(self, recipient_count: int, success_count: int, article_count: int, status: str = 'success') -> None:
        """Persist that the daily digest already ran for this date."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        run_date = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT INTO daily_digest_runs (run_date, recipient_count, success_count, article_count, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (run_date, recipient_count, success_count, article_count, status))

        conn.commit()
        conn.close()

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM news_articles')
        total_articles = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM news_articles WHERE fetched_at >= ?',
                      ((datetime.now() - timedelta(days=7)).isoformat(),))
        articles_last_week = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM news_articles WHERE fetched_at >= ?',
                      ((datetime.now() - timedelta(days=30)).isoformat(),))
        articles_last_month = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM email_logs')
        total_emails = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM email_logs WHERE status = "success"')
        successful_emails = cursor.fetchone()[0]

        cursor.execute('SELECT sent_at FROM email_logs ORDER BY sent_at DESC LIMIT 1')
        last_email_result = cursor.fetchone()
        last_email = last_email_result[0] if last_email_result else None

        login_stats = self.get_monthly_login_stats()
        visitor_stats = self.get_visitor_stats()
        conn.close()

        return {
            'total_articles': total_articles,
            'articles_last_week': articles_last_week,
            'articles_last_month': articles_last_month,
            'total_emails': total_emails,
            'successful_emails': successful_emails,
            'last_email_sent': last_email,
            'monthly_logins': login_stats['monthly_logins'],
            'users_this_month': login_stats['users_this_month'],
            'active_users': login_stats['active_users'],
            'total_visits': visitor_stats['total_visits'],
            'unique_visitors': visitor_stats['unique_visitors'],
            'monthly_visits': visitor_stats['monthly_visits'],
        }

    def cleanup_old_articles(self, months: int = 3):
        """Delete articles older than specified months."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=months * 30)

        cursor.execute('''
            DELETE FROM news_articles
            WHERE fetched_at < ?
        ''', (cutoff_date.isoformat(),))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f'Cleaned up {deleted_count} articles older than {months} months')
        return deleted_count

    def search_articles(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search articles by title or summary."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        search_pattern = f'%{query}%'
        cursor.execute('''
            SELECT * FROM news_articles
            WHERE title LIKE ? OR summary LIKE ?
            ORDER BY fetched_at DESC
            LIMIT ?
        ''', (search_pattern, search_pattern, limit))

        articles = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return articles

    def register_user(self, email: str, name: str = None) -> bool:
        """Register a new user for daily email subscriptions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO registered_users (email, name, is_active, role)
                VALUES (?, ?, 1, 'user')
            ''', (email, name))
            conn.commit()
            logger.info(f'New user registered: {email}')
            return True
        except sqlite3.IntegrityError:
            logger.warning(f'User already exists: {email}')
            return False
        finally:
            conn.close()

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Fetch a user row by email."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM registered_users WHERE email = ? LIMIT 1', (email.strip().lower(),))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def create_or_update_user_account(self, email: str, name: str, password_hash: str) -> str:
        """
        Create a new user account or set password for an existing subscription-only user.
        Returns: created | updated | exists
        """
        normalized_email = email.strip().lower()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id, password_hash FROM registered_users WHERE email = ? LIMIT 1', (normalized_email,))
        existing = cursor.fetchone()

        if not existing:
            cursor.execute('''
                INSERT INTO registered_users (email, name, is_active, role, password_hash)
                VALUES (?, ?, 1, 'user', ?)
            ''', (normalized_email, name, password_hash))
            conn.commit()
            conn.close()
            return 'created'

        user_id, existing_password_hash = existing
        if existing_password_hash:
            conn.close()
            return 'exists'

        cursor.execute('''
            UPDATE registered_users
            SET name = COALESCE(?, name),
                password_hash = ?,
                role = 'user',
                is_active = 1
            WHERE id = ?
        ''', (name, password_hash, user_id))
        conn.commit()
        conn.close()
        return 'updated'

    def get_user_dashboard_summary(self, email: str) -> Dict[str, Any]:
        """Get user-specific dashboard metrics."""
        normalized_email = email.strip().lower()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT email, name, registered_at, is_active, total_emails_received, last_email_sent, login_count, last_login_at
            FROM registered_users
            WHERE email = ?
            LIMIT 1
        ''', (normalized_email,))
        user_row = cursor.fetchone()

        if not user_row:
            conn.close()
            return {
                'registered': False,
                'total_emails_received': 0,
                'login_count': 0,
                'last_email_sent': None,
                'last_login_at': None,
                'member_since': None,
                'is_active': False,
            }

        cursor.execute('SELECT COUNT(*) FROM user_login_events WHERE email = ?', (normalized_email,))
        login_events = cursor.fetchone()[0]

        user = dict(user_row)
        conn.close()

        return {
            'registered': True,
            'total_emails_received': user.get('total_emails_received') or 0,
            'login_count': max(user.get('login_count') or 0, login_events),
            'last_email_sent': user.get('last_email_sent'),
            'last_login_at': user.get('last_login_at'),
            'member_since': user.get('registered_at'),
            'is_active': bool(user.get('is_active')),
        }

    def get_all_active_users(self) -> List[str]:
        """Get all active registered user emails for daily digest."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT email FROM registered_users
            WHERE is_active = 1
            ORDER BY registered_at ASC
        ''')

        emails = [row[0] for row in cursor.fetchall()]
        conn.close()
        return emails

    def update_user_email_sent(self, email: str):
        """Update user's last email sent timestamp and count."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE registered_users
            SET last_email_sent = CURRENT_TIMESTAMP,
                total_emails_received = total_emails_received + 1
            WHERE email = ?
        ''', (email,))

        conn.commit()
        conn.close()

    def deactivate_user(self, email: str) -> bool:
        """Deactivate a user (stop sending emails)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE registered_users
            SET is_active = 0
            WHERE email = ?
        ''', (email,))

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        if affected > 0:
            logger.info(f'User deactivated: {email}')
            return True
        return False

    def get_registered_users(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all registered users with their statistics."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM registered_users
            ORDER BY registered_at DESC
            LIMIT ?
        ''', (limit,))

        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users

    def get_user_count(self) -> int:
        """Get total number of registered users."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM registered_users WHERE is_active = 1')
        count = cursor.fetchone()[0]

        conn.close()
        return count

    def record_contact_message(self, name: str, email: str, subject: str, message: str) -> int:
        """Record a contact form submission."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO contact_messages (name, email, subject, message)
            VALUES (?, ?, ?, ?)
        ''', (name, email, subject, message))

        conn.commit()
        message_id = cursor.lastrowid
        conn.close()

        logger.info(f'Contact message recorded: {message_id} from {email}')
        return message_id

    def get_contact_messages(self, limit: int = 100, status: str = None) -> List[Dict[str, Any]]:
        """Get contact form submissions."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if status:
            cursor.execute('''
                SELECT * FROM contact_messages
                WHERE status = ?
                ORDER BY submitted_at DESC
                LIMIT ?
            ''', (status, limit))
        else:
            cursor.execute('''
                SELECT * FROM contact_messages
                ORDER BY submitted_at DESC
                LIMIT ?
            ''', (limit,))

        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return messages
