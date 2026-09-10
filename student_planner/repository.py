"""Parameterized, owner-scoped storage; no database connections on import."""
from contextlib import contextmanager
from datetime import date, datetime
import json

from psycopg2.extras import RealDictCursor
from database import safe_connect

APP_FIELDS = 'id, program_id, title, company, registration_url, deadline, status, notes, checklist, created_at, updated_at'
TASK_FIELDS = 'id, title, due_date, completed, created_at, updated_at'
TABLES = {'application': ('student_applications', APP_FIELDS), 'task': ('student_study_tasks', TASK_FIELDS)}
LIMIT = 200


def ensure_schema(conn):
    """Additive schema, called by the app's existing startup migration transaction."""
    with conn.cursor() as cursor:
        # Multiple web workers can boot at once; serialize this additive migration.
        cursor.execute('SELECT pg_advisory_xact_lock(20260909, 1)')
        cursor.execute('''CREATE TABLE IF NOT EXISTS student_applications (
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL REFERENCES registered_users(email) ON DELETE CASCADE,
            program_id INTEGER REFERENCES student_programs(id) ON DELETE SET NULL,
            title VARCHAR(200) NOT NULL, company VARCHAR(120) NOT NULL DEFAULT '',
            registration_url TEXT NOT NULL DEFAULT '', deadline DATE,
            status TEXT NOT NULL DEFAULT 'saved'
                CHECK (status IN ('saved','preparing','submitted','interview','offer','closed')),
            notes TEXT NOT NULL DEFAULT '', checklist JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(email, program_id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS student_study_tasks (
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL REFERENCES registered_users(email) ON DELETE CASCADE,
            title VARCHAR(200) NOT NULL, due_date DATE, completed BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
        for table in ('student_applications', 'student_study_tasks'):
            # Flask verifies its own sessions; there is no direct browser Data API access.
            cursor.execute(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY')
            cursor.execute(f'REVOKE ALL ON {table} FROM PUBLIC')
            for role in ('anon', 'authenticated'):
                cursor.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', (role,))
                if cursor.fetchone():
                    cursor.execute(f'REVOKE ALL ON {table} FROM {role}')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_apps_owner_deadline ON student_applications(email, deadline)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_apps_program ON student_applications(program_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_tasks_owner_due ON student_study_tasks(email, due_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_program_deadline ON student_programs(deadline, id) WHERE is_active=TRUE')


@contextmanager
def transaction():
    conn = safe_connect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def serialize(row):
    if row is None:
        return None
    return {key: value.isoformat() if isinstance(value, (datetime, date)) else value
            for key, value in dict(row).items()}


def snapshot(email):
    with transaction() as cursor:
        cursor.execute(f'SELECT {APP_FIELDS} FROM student_applications WHERE email=%s ORDER BY deadline ASC NULLS LAST, id DESC', (email,))
        applications = [serialize(row) for row in cursor.fetchall()]
        cursor.execute(f'SELECT {TASK_FIELDS} FROM student_study_tasks WHERE email=%s ORDER BY completed, due_date ASC NULLS LAST, id DESC', (email,))
        return {'applications': applications, 'tasks': [serialize(row) for row in cursor.fetchall()]}


def create(email, kind, data):
    table, fields = TABLES[kind]
    with transaction() as cursor:
        # Serialize creates per student so double clicks cannot race the record limit.
        cursor.execute('SELECT email FROM registered_users WHERE email=%s AND is_active=TRUE FOR UPDATE', (email,))
        if not cursor.fetchone():
            raise ValueError('Your account is not active. Please sign in again or contact support.')
        program_id = data.get('program_id')
        if program_id:
            cursor.execute(f'SELECT {APP_FIELDS} FROM student_applications WHERE email=%s AND program_id=%s', (email, program_id))
            existing = cursor.fetchone()
            if existing:
                return serialize(existing)
            cursor.execute('''SELECT id AS program_id, title, company, registration_url, deadline
                FROM student_programs WHERE id=%s AND is_active=TRUE
                AND (deadline IS NULL OR deadline >= CURRENT_DATE)''', (program_id,))
            program = cursor.fetchone()
            if not program:
                raise LookupError('This program is no longer available. Refresh the program list.')
            data = dict(program)
            # Provider links originate outside the planner. Never store executable URLs.
            from .validation import safe_url
            try:
                data['registration_url'] = safe_url(data.get('registration_url') or '')
            except ValueError:
                data['registration_url'] = ''
            data['title'] = (data['title'] or 'Student program')[:200]
            data['company'] = (data['company'] or '')[:120]
        cursor.execute(f'SELECT COUNT(*) AS count FROM {table} WHERE email=%s', (email,))
        if cursor.fetchone()['count'] >= LIMIT:
            raise ValueError(f'Your planner holds up to {LIMIT} {"applications" if kind == "application" else "study tasks"}. Remove finished records to add more.')
        columns = ['email'] + list(data)
        values = [email] + [json.dumps(value) if key == 'checklist' else value for key, value in data.items()]
        cursor.execute(f'INSERT INTO {table} ({", ".join(columns)}) VALUES ({", ".join(["%s"] * len(columns))}) RETURNING {fields}', values)
        return serialize(cursor.fetchone())


def update(email, kind, item_id, data):
    table, fields = TABLES[kind]
    # Keys only come from the validation allowlist; all values are bound parameters.
    with transaction() as cursor:
        values = [json.dumps(value) if key == 'checklist' else value for key, value in data.items()]
        cursor.execute(f'UPDATE {table} SET {", ".join(key + "=%s" for key in data)}, updated_at=CURRENT_TIMESTAMP WHERE email=%s AND id=%s RETURNING {fields}', values + [email, item_id])
        item = cursor.fetchone()
        if not item:
            raise LookupError('This planner item was not found. Refresh your planner.')
        return serialize(item)


def delete(email, kind, item_id):
    table, _ = TABLES[kind]
    with transaction() as cursor:
        cursor.execute(f'DELETE FROM {table} WHERE email=%s AND id=%s RETURNING id', (email, item_id))
        if not cursor.fetchone():
            raise LookupError('This planner item was not found. Refresh your planner.')


def opportunities(email, query='', company='', category='', within=None, sort='deadline', page=1):
    conditions = ['p.is_active=TRUE', '(p.deadline IS NULL OR p.deadline >= CURRENT_DATE)']
    params = []
    if query:
        # Search literally, including percent and underscore characters.
        pattern = '%' + query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        conditions.append('(p.title ILIKE %s OR p.company ILIKE %s OR p.description ILIKE %s)')
        params.extend([pattern] * 3)
    for field, value in [('company', company), ('category', category)]:
        if value:
            conditions.append(f'p.{field}=%s')
            params.append(value)
    if within:
        conditions.append('p.deadline <= CURRENT_DATE + %s')
        params.append(within)
    where = ' AND '.join(conditions)
    order = 'p.created_at DESC, p.id DESC' if sort == 'newest' else 'p.deadline ASC NULLS LAST, p.id DESC'
    with transaction() as cursor:
        cursor.execute(f'SELECT COUNT(*) AS count FROM student_programs p WHERE {where}', params)
        total = cursor.fetchone()['count']
        cursor.execute(f'''SELECT p.id,p.title,p.company,p.description,p.registration_url,p.deadline,p.category,
            a.id AS application_id FROM student_programs p
            LEFT JOIN student_applications a ON a.program_id=p.id AND a.email=%s
            WHERE {where} ORDER BY {order} LIMIT 12 OFFSET %s''', [email] + params + [(page - 1) * 12])
        items = [serialize(row) for row in cursor.fetchall()]
        cursor.execute('''SELECT DISTINCT company, category FROM student_programs
            WHERE is_active=TRUE AND (deadline IS NULL OR deadline >= CURRENT_DATE)''')
        options = cursor.fetchall()
        return {'items': items, 'total': total, 'page': page, 'page_size': 12,
                'companies': sorted({row['company'] for row in options if row['company']}),
                'categories': sorted({row['category'] for row in options if row['category']})}
