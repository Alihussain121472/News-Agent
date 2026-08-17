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
                total_emails_received INTEGER DEFAULT 0
            )
        ''')

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

        conn.close()

        return {
            'total_articles': total_articles,
            'articles_last_week': articles_last_week,
            'articles_last_month': articles_last_month,
            'total_emails': total_emails,
            'successful_emails': successful_emails,
            'last_email_sent': last_email
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
                INSERT INTO registered_users (email, name, is_active)
                VALUES (?, ?, 1)
            ''', (email, name))
            conn.commit()
            logger.info(f'New user registered: {email}')
            return True
        except sqlite3.IntegrityError:
            logger.warning(f'User already exists: {email}')
            return False
        finally:
            conn.close()

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
