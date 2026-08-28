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
    cursor.execute("ALTER TABLE contact_messages ADD COLUMN admin_reply TEXT;")
    cursor.execute("ALTER TABLE contact_messages ADD COLUMN replied_at TIMESTAMP;")
    conn.commit()
    print("Added reply columns successfully.")
except Exception as e:
    print(f"Error (maybe already exists): {e}")
finally:
    conn.close()
