import os
import unittest
from datetime import datetime
from urllib.parse import parse_qs, urlparse
from unittest.mock import MagicMock, patch

from flask import Flask

from analytics_revenue_portal.adsense_service import (
    READONLY_SCOPE,
    build_authorization_url,
    decrypt_refresh_token,
    encrypt_refresh_token,
    fetch_daily_report,
)
from analytics_revenue_portal.routes import analytics_bp


def empty_revenue_snapshot(days=90):
    return {
        'today_earnings': 0.0,
        'month_earnings': 0.0,
        'previous_month_earnings': 0.0,
        'month_impressions': 0,
        'month_clicks': 0,
        'month_page_views': 0,
        'page_rpm': 0.0,
        'ctr': 0.0,
        'series': [{'date': '2026-08-31', 'estimated_earnings': 0.0, 'impressions': 0, 'clicks': 0, 'page_views': 0}],
    }


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.ok = status_code < 400

    def json(self):
        return self.payload


class AdSenseServiceTests(unittest.TestCase):
    def test_refresh_token_is_encrypted_at_rest(self):
        with patch.dict(os.environ, {'SECRET_KEY': 'a-stable-secret-key-that-is-longer-than-32-characters'}, clear=False):
            encrypted = encrypt_refresh_token('google-refresh-token')
            self.assertNotIn('google-refresh-token', encrypted)
            self.assertEqual('google-refresh-token', decrypt_refresh_token(encrypted))

    def test_authorization_url_uses_read_only_scope_and_pkce(self):
        with patch.dict(os.environ, {
            'GOOGLE_ADSENSE_CLIENT_ID': 'client-id',
            'GOOGLE_ADSENSE_CLIENT_SECRET': 'client-secret',
        }, clear=False):
            url = build_authorization_url('https://example.com/callback', 'state-value', 'challenge-value')
        params = parse_qs(urlparse(url).query)
        self.assertEqual([READONLY_SCOPE], params['scope'])
        self.assertEqual(['S256'], params['code_challenge_method'])
        self.assertEqual(['offline'], params['access_type'])

    @patch('analytics_revenue_portal.adsense_service.requests.get')
    def test_daily_report_parses_verified_adsense_metrics(self, get):
        get.return_value = FakeResponse({
            'headers': [
                {'name': 'DATE'},
                {'name': 'ESTIMATED_EARNINGS', 'currencyCode': 'USD'},
                {'name': 'IMPRESSIONS'}, {'name': 'CLICKS'}, {'name': 'PAGE_VIEWS'},
            ],
            'rows': [{'cells': [
                {'value': '2026-08-30'}, {'value': '12.34'}, {'value': '900'}, {'value': '12'}, {'value': '650'},
            ]}],
        })

        rows, currency = fetch_daily_report('access-token', 'accounts/pub-123', days=7)

        self.assertEqual('USD', currency)
        self.assertEqual('2026-08-30', rows[0]['date'])
        self.assertEqual(900, rows[0]['impressions'])
        self.assertEqual('12.34', str(rows[0]['estimated_earnings']))
        request_headers = get.call_args.kwargs['headers']
        self.assertEqual('Bearer access-token', request_headers['Authorization'])


class RevenueRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__, template_folder='templates')
        self.app.secret_key = 'test-secret'
        self.app.testing = True
        self.app.register_blueprint(analytics_bp, url_prefix='/analytics')
        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session['role'] = 'admin'

    @patch('analytics_revenue_portal.routes.adsense_repository.revenue_snapshot', side_effect=empty_revenue_snapshot)
    @patch('analytics_revenue_portal.routes.connection_status')
    @patch('analytics_revenue_portal.routes.NewsDatabase')
    def test_revenue_page_has_privacy_control_and_real_oauth_connection(self, database, status, _snapshot):
        status.return_value = {'configured': False, 'connected': False, 'account': None}
        db = database.return_value
        db.get_ad_stats.return_value = {'today_impressions': 0}
        db.get_visitor_stats.return_value = {'monthly_visits': 0}

        response = self.client.get('/analytics/revenue')
        html = response.get_data(as_text=True)

        self.assertEqual(200, response.status_code)
        self.assertIn('Hide revenue', html)
        self.assertIn('Connect Google AdSense', html)
        self.assertIn('read-only AdSense reporting permission', html)
        self.assertNotIn('Service Account JSON', html)

    @patch('analytics_revenue_portal.routes.connection_status', return_value={'configured': True, 'connected': False, 'account': None})
    def test_connect_starts_google_oauth(self, _status):
        with patch.dict(os.environ, {
            'GOOGLE_ADSENSE_CLIENT_ID': 'client-id',
            'GOOGLE_ADSENSE_CLIENT_SECRET': 'client-secret',
        }, clear=False):
            response = self.client.get('/analytics/adsense/connect')

        self.assertEqual(302, response.status_code)
        self.assertEqual('accounts.google.com', urlparse(response.location).hostname)
        with self.client.session_transaction() as session:
            self.assertIn('adsense_oauth', session)

    @patch('analytics_revenue_portal.routes.sync_connection')
    def test_sync_rejects_cross_origin_request(self, sync):
        response = self.client.post('/analytics/api/adsense/sync', json={}, headers={'Origin': 'https://attacker.example'})
        self.assertEqual(403, response.status_code)
        sync.assert_not_called()

    @patch('analytics_revenue_portal.routes.exchange_code')
    def test_callback_rejects_invalid_oauth_state(self, exchange):
        with self.client.session_transaction() as session:
            session['adsense_oauth'] = {
                'state': 'expected', 'verifier': 'verifier',
                'redirect_uri': 'http://localhost/analytics/adsense/callback',
                'created_at': int(datetime.now().timestamp()),
            }
        response = self.client.get('/analytics/adsense/callback?state=wrong&code=code')
        self.assertEqual(302, response.status_code)
        self.assertIn('connection=invalid_state', response.location)
        exchange.assert_not_called()


if __name__ == '__main__':
    unittest.main()
