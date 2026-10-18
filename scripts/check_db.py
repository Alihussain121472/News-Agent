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
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='blog_posts';")
    cols = cursor.fetchall()
    print("Columns in blog_posts:", cols)
except Exception as e:
    print(e)
conn.close()
