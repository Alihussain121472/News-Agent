import psycopg2
import sys
try:
    conn = psycopg2.connect('')
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
    sys.exit(1)
