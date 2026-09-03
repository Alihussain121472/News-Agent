import re
from datetime import datetime

with open('database.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add daily_visits to get_visitor_stats
old_func = """    def get_visitor_stats(self) -> Dict[str, int]:
        conn = safe_connect()
        cursor = conn.cursor()
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('SELECT COUNT(*) FROM site_visits')
        total = _fetch_val(cursor)
        cursor.execute('SELECT COUNT(DISTINCT ip_address) FROM site_visits')
        unique = _fetch_val(cursor)
        cursor.execute('SELECT COUNT(*) FROM site_visits WHERE visit_time >= %s', (month_start,))
        monthly = _fetch_val(cursor)
        conn.close()
        return {'total_visits': total, 'unique_visitors': unique, 'monthly_visits': monthly}"""

new_func = """    def get_visitor_stats(self) -> Dict[str, int]:
        conn = safe_connect()
        cursor = conn.cursor()
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('SELECT COUNT(*) FROM site_visits')
        total = _fetch_val(cursor)
        cursor.execute('SELECT COUNT(DISTINCT ip_address) FROM site_visits')
        unique = _fetch_val(cursor)
        cursor.execute('SELECT COUNT(*) FROM site_visits WHERE visit_time >= %s', (month_start,))
        monthly = _fetch_val(cursor)
        cursor.execute('SELECT COUNT(*) FROM site_visits WHERE visit_time >= %s', (today_start,))
        daily = _fetch_val(cursor)
        conn.close()
        return {'total_visits': total, 'unique_visitors': unique, 'monthly_visits': monthly, 'daily_visits': daily}
        
    def get_daily_history(self) -> list:
        conn = safe_connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('''
            SELECT DATE(visit_time) as date, COUNT(*) as visits 
            FROM site_visits 
            GROUP BY DATE(visit_time) 
            ORDER BY date DESC LIMIT 30
        ''')
        history = cursor.fetchall()
        
        # Also get support requests history
        cursor.execute('''
            SELECT DATE(submitted_at) as date, COUNT(*) as requests 
            FROM contact_messages 
            GROUP BY DATE(submitted_at) 
            ORDER BY date DESC LIMIT 30
        ''')
        requests = {str(r['date']): r['requests'] for r in cursor.fetchall()}
        
        conn.close()
        
        result = []
        for row in history:
            d_str = str(row['date'])
            result.append({
                'date': d_str,
                'visits': row['visits'],
                'requests': requests.get(d_str, 0)
            })
        return result
"""

text = text.replace(old_func, new_func)

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(text)
