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
    cursor.execute("SELECT * FROM user_preferences LIMIT 1")
    print("Table user_preferences exists.")
except Exception as e:
    print(f"Error: {e}")
conn.close()
