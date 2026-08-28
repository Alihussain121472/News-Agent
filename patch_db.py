import os

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add new tables to the create_tables method
create_tables_sql = '''        cursor.execute(\'\'\'CREATE TABLE IF NOT EXISTS user_preferences (
            email TEXT PRIMARY KEY,
            companies TEXT,
            fields TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)\'\'\')
        cursor.execute(\'\'\'CREATE TABLE IF NOT EXISTS saved_articles (
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL,
            article_id INTEGER NOT NULL,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(email, article_id))\'\'\')
'''
if 'CREATE TABLE IF NOT EXISTS user_preferences' not in content:
    content = content.replace("cursor.execute('''CREATE TABLE IF NOT EXISTS site_visits", create_tables_sql + "\n        cursor.execute('''CREATE TABLE IF NOT EXISTS site_visits")

# Add new methods at the end of the file
new_methods = '''

    # -- Features: Preferences & Memory Vault --
    def save_user_preferences(self, email: str, companies: str, fields: str):
        conn = safe_connect()
        cursor = conn.cursor()
        cursor.execute(\'\'\'
            INSERT INTO user_preferences (email, companies, fields, updated_at) 
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (email) DO UPDATE SET companies = EXCLUDED.companies, fields = EXCLUDED.fields, updated_at = CURRENT_TIMESTAMP
        \'\'\', (email, companies, fields))
        conn.commit()
        conn.close()

    def get_user_preferences(self, email: str):
        conn = safe_connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT companies, fields FROM user_preferences WHERE email=%s', (email,))
        row = cursor.fetchone()
        conn.close()
        if row: return to_dict(row)
        return {'companies': '', 'fields': ''}

    def save_article(self, email: str, article_id: int):
        conn = safe_connect()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO saved_articles (email, article_id) VALUES (%s, %s) ON CONFLICT DO NOTHING', (email, article_id))
            conn.commit()
        except Exception:
            conn.rollback()
        conn.close()

    def delete_saved_article(self, email: str, article_id: int):
        conn = safe_connect()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM saved_articles WHERE email=%s AND article_id=%s', (email, article_id))
        conn.commit()
        conn.close()

    def get_saved_articles(self, email: str):
        conn = safe_connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Only return articles saved within the last month (Rule 2)
        month_ago = (datetime.now() - timedelta(days=30)).isoformat()
        cursor.execute(\'\'\'
            SELECT n.*, s.saved_at 
            FROM news_articles n 
            JOIN saved_articles s ON n.id = s.article_id 
            WHERE s.email = %s AND s.saved_at >= %s
            ORDER BY s.saved_at DESC
        \'\'\', (email, month_ago))
        rows = [to_dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def cleanup_saved_articles(self, days: int = 30):
        conn = safe_connect()
        cursor = conn.cursor()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute('DELETE FROM saved_articles WHERE saved_at < %s', (cutoff,))
        conn.commit()
        conn.close()
        
    def get_articles_by_date(self, target_date: str, limit: int = 50):
        conn = safe_connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # target_date in YYYY-MM-DD
        cursor.execute(\'\'\'
            SELECT * FROM news_articles 
            WHERE date(fetched_at) = %s 
            ORDER BY fetched_at DESC LIMIT %s
        \'\'\', (target_date, limit))
        rows = [to_dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
'''
if 'def save_user_preferences' not in content:
    content += new_methods

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated database.py")
