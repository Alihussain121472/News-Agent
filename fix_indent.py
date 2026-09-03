import re

with open('database.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad_func = """        def get_daily_contact_count(self) -> int:
        conn = safe_connect()
        cursor = conn.cursor()
        from datetime import datetime
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('SELECT COUNT(*) FROM contact_messages WHERE submitted_at >= %s', (today_start,))
        res = _fetch_val(cursor)
        conn.close()
        return res"""

good_func = """    def get_daily_contact_count(self) -> int:
        conn = safe_connect()
        cursor = conn.cursor()
        from datetime import datetime
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('SELECT COUNT(*) FROM contact_messages WHERE submitted_at >= %s', (today_start,))
        res = _fetch_val(cursor)
        conn.close()
        return res"""

text = text.replace(bad_func, good_func)

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(text)
