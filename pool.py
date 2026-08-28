import os
import re

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

pool_code = '''import threading
from psycopg2.pool import SimpleConnectionPool

_pool = None
_pool_lock = threading.Lock()

class PooledConnection:
    def __init__(self, conn, pool):
        self._conn = conn
        self._pool = pool
    def cursor(self, *args, **kwargs):
        return self._conn.cursor(*args, **kwargs)
    def commit(self):
        self._conn.commit()
    def rollback(self):
        self._conn.rollback()
    def close(self):
        try:
            self._pool.putconn(self._conn)
        except:
            pass

def safe_connect():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                db_url = os.getenv('DATABASE_URL')
                _pool = SimpleConnectionPool(1, 30, db_url)
    return PooledConnection(_pool.getconn(), _pool)
'''

content = re.sub(r'def safe_connect\(\):\s+return psycopg2\.connect\(os\.getenv\(\'DATABASE_URL\'\)\)', pool_code, content)

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Implemented connection pooling")
