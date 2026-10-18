import os
import sys
import psycopg2
from web_server import app
from database import safe_connect

print("--- BACKEND DIAGNOSTICS ---")
# 1. Check Env Vars
required_envs = ['DATABASE_URL', 'EMAIL_USER', 'EMAIL_PASS', 'OPENAI_API_KEY']
for e in required_envs:
    val = os.getenv(e)
    print(f"ENV {e}: {'SET' if val else 'MISSING'}")

# 2. Check Database
try:
    conn = safe_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    print("DATABASE: CONNECTION SUCCESSFUL (Fallback or Real)")
    conn.close()
except Exception as e:
    print(f"DATABASE ERROR: {e}")

# 3. Check Flask Routes
print("\n--- FRONTEND/ROUTES DIAGNOSTICS ---")
routes_to_test = ['/', '/login', '/signup', '/admin', '/analytics/dashboard', '/analytics/messages', '/googleae48116c49ed7429.html', '/sitemap.xml']
with app.test_client() as c:
    with c.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['user_email'] = 'admin@novabrief.tech'
    
    for route in routes_to_test:
        try:
            resp = c.get(route)
            print(f"ROUTE {route}: {resp.status_code}")
        except Exception as e:
            print(f"ROUTE {route}: CRASH - {e}")

# 4. Check Static Files
print("\n--- STATIC ASSETS ---")
assets = ['static/manifest.json', 'static/icon-192.png', 'templates/index.html']
for a in assets:
    print(f"FILE {a}: {'EXISTS' if os.path.exists(a) else 'MISSING'}")

