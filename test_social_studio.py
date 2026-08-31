import unittest
from unittest.mock import patch

from flask import Flask

from social_media_agent.routes import social_bp


class SocialStudioIntegrationTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__, template_folder='templates')
        app.config.update(TESTING=True, SECRET_KEY='test-only-secret')

        @app.route('/admin/login', endpoint='admin_login_page')
        def admin_login_page():
            return 'login'

        app.register_blueprint(social_bp, url_prefix='/social')
        self.client = app.test_client()

    def sign_in(self):
        with self.client.session_transaction() as session:
            session['role'] = 'admin'

    def test_agent_page_and_status_are_available_to_admin(self):
        self.sign_in()
        page = self.client.get('/social/dashboard')
        status = self.client.get('/social/api/studio-status')

        self.assertEqual(page.status_code, 200)
        self.assertIn(b'NovaBrief Social Studio', page.data)
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.get_json()['version'], '1.1.1')

    def test_launch_requires_admin(self):
        response = self.client.post('/social/api/launch-studio')
        self.assertEqual(response.status_code, 401)

    @patch('social_media_agent.routes._open_windows_app')
    def test_launch_rejects_a_different_origin(self, open_app):
        self.sign_in()
        response = self.client.post(
            '/social/api/launch-studio',
            headers={'Origin': 'https://example.com'},
            base_url='http://localhost',
        )

        self.assertEqual(response.status_code, 403)
        open_app.assert_not_called()

    @patch('social_media_agent.routes._open_windows_app')
    def test_admin_can_launch_the_detected_agent(self, open_app):
        self.sign_in()
        response = self.client.post(
            '/social/api/launch-studio',
            headers={'Origin': 'http://localhost'},
            base_url='http://localhost',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['status'], 'success')
        open_app.assert_called_once()


if __name__ == '__main__':
    unittest.main()
