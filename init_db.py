import os
import psycopg2

with open('.env', 'r') as f:
    for line in f:
        if line.startswith('DATABASE_URL='):
            os.environ['DATABASE_URL'] = line.strip().split('=', 1)[1]

from database import NewsDatabase
db = NewsDatabase()
db._create_tables()
print("Tables created successfully.")
