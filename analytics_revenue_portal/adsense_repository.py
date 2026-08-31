from contextlib import contextmanager
from datetime import date, timedelta
from decimal import Decimal

import psycopg2.extras

from database import safe_connect


@contextmanager
def _connection(dict_rows=False):
    connection = safe_connect()
    cursor_factory = psycopg2.extras.RealDictCursor if dict_rows else None
    cursor = connection.cursor(cursor_factory=cursor_factory)
    try:
        yield connection, cursor
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def ensure_schema():
    with _connection() as (connection, cursor):
        cursor.execute('''CREATE TABLE IF NOT EXISTS adsense_connections (
            id INTEGER PRIMARY KEY,
            account_name TEXT NOT NULL,
            account_display_name TEXT,
            currency_code TEXT,
            encrypted_refresh_token TEXT NOT NULL,
            connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_synced_at TIMESTAMP,
            last_error TEXT
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS adsense_daily_metrics (
            report_date DATE PRIMARY KEY,
            account_name TEXT NOT NULL,
            currency_code TEXT NOT NULL DEFAULT 'USD',
            estimated_earnings NUMERIC(18, 6) NOT NULL DEFAULT 0,
            impressions BIGINT NOT NULL DEFAULT 0,
            clicks BIGINT NOT NULL DEFAULT 0,
            page_views BIGINT NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        connection.commit()


def save_connection(account, encrypted_refresh_token):
    ensure_schema()
    with _connection(dict_rows=True) as (connection, cursor):
        cursor.execute('''INSERT INTO adsense_connections
            (id, account_name, account_display_name, currency_code, encrypted_refresh_token, last_error)
            VALUES (1, %s, %s, %s, %s, NULL)
            ON CONFLICT (id) DO UPDATE SET
                account_name=EXCLUDED.account_name,
                account_display_name=EXCLUDED.account_display_name,
                currency_code=EXCLUDED.currency_code,
                encrypted_refresh_token=EXCLUDED.encrypted_refresh_token,
                updated_at=CURRENT_TIMESTAMP,
                last_error=NULL
            RETURNING *''', (
                account['name'], account.get('displayName') or account['name'],
                account.get('currencyCode') or 'USD', encrypted_refresh_token,
            ))
        row = dict(cursor.fetchone())
        connection.commit()
        return row


def get_connection(include_token=False):
    ensure_schema()
    with _connection(dict_rows=True) as (_, cursor):
        fields = '*' if include_token else '''id, account_name, account_display_name, currency_code,
            connected_at, updated_at, last_synced_at, last_error'''
        cursor.execute(f'SELECT {fields} FROM adsense_connections WHERE id=1')
        row = cursor.fetchone()
        return dict(row) if row else None


def record_sync(account_name, currency_code, rows):
    ensure_schema()
    with _connection() as (connection, cursor):
        for row in rows:
            cursor.execute('''INSERT INTO adsense_daily_metrics
                (report_date, account_name, currency_code, estimated_earnings, impressions, clicks, page_views)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (report_date) DO UPDATE SET
                    account_name=EXCLUDED.account_name,
                    currency_code=EXCLUDED.currency_code,
                    estimated_earnings=EXCLUDED.estimated_earnings,
                    impressions=EXCLUDED.impressions,
                    clicks=EXCLUDED.clicks,
                    page_views=EXCLUDED.page_views,
                    updated_at=CURRENT_TIMESTAMP''', (
                        row['date'], account_name, currency_code, row['estimated_earnings'],
                        row['impressions'], row['clicks'], row['page_views'],
                    ))
        cursor.execute('''UPDATE adsense_connections SET last_synced_at=CURRENT_TIMESTAMP,
            last_error=NULL, currency_code=%s, updated_at=CURRENT_TIMESTAMP WHERE id=1''', (currency_code,))
        connection.commit()


def record_sync_error(message):
    ensure_schema()
    with _connection() as (connection, cursor):
        cursor.execute('''UPDATE adsense_connections SET last_error=%s,
            updated_at=CURRENT_TIMESTAMP WHERE id=1''', (str(message)[:1000],))
        connection.commit()


def disconnect():
    ensure_schema()
    with _connection() as (connection, cursor):
        cursor.execute('DELETE FROM adsense_connections WHERE id=1')
        deleted = cursor.rowcount > 0
        connection.commit()
        return deleted


def revenue_snapshot(days=90):
    ensure_schema()
    days = max(7, min(int(days), 365))
    today = date.today()
    month_start = today.replace(day=1)
    previous_month_end = month_start - timedelta(days=1)
    previous_month_start = previous_month_end.replace(day=1)
    series_start = today - timedelta(days=days - 1)

    with _connection(dict_rows=True) as (_, cursor):
        cursor.execute('''SELECT
            COALESCE(SUM(estimated_earnings) FILTER (WHERE report_date=%s), 0) AS today_earnings,
            COALESCE(SUM(estimated_earnings) FILTER (WHERE report_date >= %s), 0) AS month_earnings,
            COALESCE(SUM(estimated_earnings) FILTER (WHERE report_date BETWEEN %s AND %s), 0) AS previous_month_earnings,
            COALESCE(SUM(impressions) FILTER (WHERE report_date >= %s), 0) AS month_impressions,
            COALESCE(SUM(clicks) FILTER (WHERE report_date >= %s), 0) AS month_clicks,
            COALESCE(SUM(page_views) FILTER (WHERE report_date >= %s), 0) AS month_page_views
            FROM adsense_daily_metrics''', (
                today, month_start, previous_month_start, previous_month_end,
                month_start, month_start, month_start,
            ))
        totals = dict(cursor.fetchone())
        cursor.execute('''SELECT report_date, estimated_earnings, impressions, clicks, page_views,
            currency_code FROM adsense_daily_metrics WHERE report_date >= %s ORDER BY report_date''', (series_start,))
        stored = {row['report_date']: dict(row) for row in cursor.fetchall()}

    zero = Decimal('0')
    series = []
    for offset in range(days):
        report_date = series_start + timedelta(days=offset)
        row = stored.get(report_date, {})
        series.append({
            'date': report_date.isoformat(),
            'estimated_earnings': float(row.get('estimated_earnings') or zero),
            'impressions': int(row.get('impressions') or 0),
            'clicks': int(row.get('clicks') or 0),
            'page_views': int(row.get('page_views') or 0),
        })

    month_earnings = totals.get('month_earnings') or zero
    page_views = int(totals.get('month_page_views') or 0)
    impressions = int(totals.get('month_impressions') or 0)
    clicks = int(totals.get('month_clicks') or 0)
    return {
        'today_earnings': float(totals.get('today_earnings') or zero),
        'month_earnings': float(month_earnings),
        'previous_month_earnings': float(totals.get('previous_month_earnings') or zero),
        'month_impressions': impressions,
        'month_clicks': clicks,
        'month_page_views': page_views,
        'page_rpm': float((month_earnings * 1000 / page_views) if page_views else zero),
        'ctr': float((Decimal(clicks) * 100 / impressions) if impressions else zero),
        'series': series,
    }
