"""Owner-scoped durable storage using the site's existing PostgreSQL connection."""
from contextlib import contextmanager
import json
import time
import uuid

from psycopg2.extras import RealDictCursor
from database import safe_connect


def ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute('SELECT pg_advisory_xact_lock(20260916, 1)')
        cur.execute('''CREATE TABLE IF NOT EXISTS python_practice_state (
            email TEXT PRIMARY KEY REFERENCES registered_users(email) ON DELETE CASCADE,
            data JSONB NOT NULL DEFAULT '{}'::jsonb,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())''')
        cur.execute('''CREATE TABLE IF NOT EXISTS python_practice_jobs (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL REFERENCES registered_users(email) ON DELETE CASCADE,
            data JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())''')
        cur.execute('CREATE INDEX IF NOT EXISTS python_jobs_owner ON python_practice_jobs(email, created_at)')
        for table in ('python_practice_state', 'python_practice_jobs'):
            cur.execute(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY')
            cur.execute(f'REVOKE ALL ON {table} FROM PUBLIC')
            for role in ('anon', 'authenticated'):
                cur.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', (role,))
                if cur.fetchone():
                    cur.execute(f'REVOKE ALL ON {table} FROM {role}')


@contextmanager
def transaction():
    conn = safe_connect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def defaults():
    return dict(drafts={}, completed={}, submissions=[], quiz_results=[], quiz_drafts={}, exams=[], active_exam=None, last_exercise='welcome')


@contextmanager
def state(email):
    with transaction() as cur:
        cur.execute('INSERT INTO python_practice_state(email) VALUES(%s) ON CONFLICT DO NOTHING', (email,))
        cur.execute('SELECT data FROM python_practice_state WHERE email=%s FOR UPDATE', (email,))
        data = defaults() | cur.fetchone()['data']
        yield data
        cur.execute('UPDATE python_practice_state SET data=%s::jsonb,updated_at=NOW() WHERE email=%s', (json.dumps(data), email))


def snapshot(email):
    with transaction() as cur:
        cur.execute('SELECT data FROM python_practice_state WHERE email=%s', (email,))
        row = cur.fetchone()
        return defaults() | (row['data'] if row else {})


def create_job(email, data):
    with transaction() as cur:
        cur.execute('SELECT pg_advisory_xact_lock(20260916, 2)')
        cur.execute('''SELECT count(*) AS n FROM python_practice_jobs
                       WHERE data->>'status'='running' AND updated_at > NOW()-INTERVAL '120 seconds' ''')
        if cur.fetchone()['n'] >= 4:
            raise ValueError('The Python runners are busy. Please retry shortly.')
        cur.execute('''SELECT count(*) AS n FROM python_practice_jobs WHERE email=%s
                       AND data->>'status'='running' AND updated_at > NOW()-INTERVAL '120 seconds' ''', (email,))
        if cur.fetchone()['n']:
            raise ValueError('You already have a running program. Stop it or wait for it to finish.')
        cur.execute('''SELECT count(*) AS n FROM python_practice_jobs WHERE email=%s
                       AND created_at > NOW()-INTERVAL '10 minutes' ''', (email,))
        if cur.fetchone()['n'] >= 80:
            raise ValueError('Execution limit reached (80 per 10 minutes). Try again shortly.')
        id = str(uuid.uuid4())
        job = data | dict(id=id,status='running',cancelled=False,created=time.time())
        cur.execute('INSERT INTO python_practice_jobs(id,email,data) VALUES(%s,%s,%s::jsonb)', (id,email,json.dumps(job)))
        return job


def get_job(email, id):
    with transaction() as cur:
        cur.execute('SELECT data, updated_at FROM python_practice_jobs WHERE email=%s AND id=%s', (email,id))
        row = cur.fetchone()
        if not row:
            raise LookupError('Execution not found.')
        data = row['data']
        if data['status']=='running' and time.time()-row['updated_at'].timestamp()>120:
            data.update(status='error', message='The runner restarted or timed out. Your code is saved; please retry.')
        return data


def update_job(email, id, values):
    with transaction() as cur:
        cur.execute('UPDATE python_practice_jobs SET data=data || %s::jsonb,updated_at=NOW() WHERE email=%s AND id=%s',
                    (json.dumps(values),email,id))


def cleanup():
    with transaction() as cur:
        cur.execute("DELETE FROM python_practice_jobs WHERE created_at < NOW()-INTERVAL '7 days'")
