import os
import psycopg2
from database import safe_connect

with open('.env', 'r') as f:
    for line in f:
        if line.startswith('DATABASE_URL='):
            os.environ['DATABASE_URL'] = line.strip().split('=', 1)[1]

conn = safe_connect()
cursor = conn.cursor()

try:
    cursor.execute('''
    INSERT INTO blog_posts (title, slug, content, meta_description)
    SELECT title, slug, content, meta_description FROM blog_articles
    ON CONFLICT (slug) DO NOTHING;
    ''')
    conn.commit()
    print("Moved articles to blog_posts successfully.")
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()

conn.close()
