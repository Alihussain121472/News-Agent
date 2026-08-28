import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute("DELETE FROM registered_users WHERE email='test12345@example.com'")
conn.commit()
print("Test user deleted.")
