import unittest
from datetime import datetime
from unittest.mock import patch

from flask import Flask

from growth_seo_agent.routes import seo_bp


class SeoRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__, template_folder='templates')
        self.app.secret_key = 'test-secret'
        self.app.testing = True
        self.app.register_blueprint(seo_bp, url_prefix='/seo')
        self.client = self.app.test_client()

    def login(self):
        with self.client.session_transaction() as session:
            session['role'] = 'admin'

    def test_api_requires_admin(self):
        response = self.client.get('/seo/api/status')
        self.assertEqual(401, response.status_code)
        self.assertEqual('error', response.get_json()['status'])

    @patch('growth_seo_agent.routes.repository.dashboard_snapshot')
    def test_status_reports_monitoring_state(self, snapshot):
        self.login()
        snapshot.return_value = {
            'config': {'site_url': 'https://example.com', 'enabled': True, 'schedule_hours': 6, 'max_pages': 20},
            'latest_run': {'id': 4, 'status': 'completed', 'completed_at': datetime(2026, 8, 31, 9, 0)},
            'issues': [], 'keywords': [], 'backlinks': [], 'content_opportunities': [], 'runs': [], 'events': [],
        }

        response = self.client.get('/seo/api/status')

        self.assertEqual(200, response.status_code)
        self.assertEqual('active', response.get_json()['status'])
        self.assertEqual('2026-08-31T15:00:00', response.get_json()['next_run_at'])

    @patch('growth_seo_agent.routes.repository.dashboard_snapshot')
    def test_professional_dashboard_renders_every_workflow(self, snapshot):
        self.login()
        snapshot.return_value = {
            'config': {'site_url': 'https://example.com', 'enabled': True, 'schedule_hours': 6, 'max_pages': 20},
            'latest_run': None,
            'issues': [], 'keywords': [], 'backlinks': [], 'content_opportunities': [], 'runs': [], 'events': [],
        }

        response = self.client.get('/seo/dashboard')
        html = response.get_data(as_text=True)

        self.assertEqual(200, response.status_code)
        for label in ('SEO Studio', 'Run audit now', 'Keywords', 'Backlinks', 'Content', 'Settings'):
            self.assertIn(label, html)

    @patch('growth_seo_agent.routes.repository.log_event')
    @patch('growth_seo_agent.routes.repository.update_config')
    def test_config_saves_false_boolean(self, update_config, _log_event):
        self.login()
        update_config.return_value = {'site_url': 'https://example.com', 'enabled': False, 'schedule_hours': 12, 'max_pages': 10}

        response = self.client.post('/seo/api/config', json={
            'site_url': 'example.com', 'enabled': 'false', 'schedule_hours': 12, 'max_pages': 10,
        })

        self.assertEqual(200, response.status_code)
        update_config.assert_called_once_with('https://example.com', False, 12, 10)

    def test_mutation_rejects_cross_origin_request(self):
        self.login()
        response = self.client.post(
            '/seo/api/config',
            json={'site_url': 'https://example.com'},
            headers={'Origin': 'https://attacker.example'},
        )
        self.assertEqual(403, response.status_code)

    @patch('growth_seo_agent.routes.start_seo_cycle', return_value=True)
    def test_manual_audit_starts_in_background(self, start_cycle):
        self.login()
        response = self.client.post('/seo/api/run', json={})
        self.assertEqual(202, response.status_code)
        start_cycle.assert_called_once_with('manual')

    @patch('growth_seo_agent.routes.repository.get_content_opportunity')
    @patch('growth_seo_agent.routes.repository.update_content_status')
    def test_opening_brief_does_not_change_workflow_status(self, update_status, get_opportunity):
        self.login()
        get_opportunity.return_value = {
            'id': 7, 'keyword': 'AI news daily', 'intent': 'informational', 'target_url': '', 'status': 'idea',
        }
        response = self.client.get('/seo/api/content/7/brief')
        self.assertEqual(200, response.status_code)
        self.assertIn('working_title', response.get_json()['brief'])
        update_status.assert_not_called()


if __name__ == '__main__':
    unittest.main()
