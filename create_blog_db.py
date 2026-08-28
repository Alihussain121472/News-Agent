import os
import psycopg2

with open('.env', 'r') as f:
    for line in f:
        if line.startswith('DATABASE_URL='):
            os.environ['DATABASE_URL'] = line.strip().split('=', 1)[1]

from database import safe_connect

conn = safe_connect()
cursor = conn.cursor()
try:
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blog_articles (
        id SERIAL PRIMARY KEY,
        slug VARCHAR(255) UNIQUE NOT NULL,
        title VARCHAR(255) NOT NULL,
        content TEXT NOT NULL,
        meta_description TEXT,
        keywords TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    conn.commit()
    print("Created blog_articles table successfully.")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
