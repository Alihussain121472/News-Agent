"""App wiring checks with all database/mail startup dependencies isolated."""
import importlib
import os
import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from database import NewsDatabase


class StudentIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.dict(os.environ, {'ENABLE_IN_PROCESS_SCHEDULER': 'false',
                                     'FLASK_ENV': 'development',
                                     'SECRET_KEY': 'isolated-student-integration-test'}, clear=True), \
                patch('dotenv.load_dotenv'), patch('database.NewsDatabase'), \
                patch('socket.socket.connect', side_effect=AssertionError('Network is forbidden in this test')):
            cls.web = importlib.import_module('web_server')
        cls.web.app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)

    def setUp(self):
        self.client = self.web.app.test_client()
        with self.client.session_transaction() as session:
            session.update(role='user', user_email='planner-test@example.com', user_name="Student </script>")

    def test_dashboard_renders_student_workflows_and_safe_identity(self):
        with patch.object(self.web, 'db'), patch.object(self.web.VISITOR_EXECUTOR, 'submit'):
            response = self.client.get('/user/dashboard?tab=planner')
        self.assertEqual(200, response.status_code)
        html = response.get_data(as_text=True)
        for marker in ('My Planner', 'Application tracker', 'Study tasks', 'Download calendar',
                       'applicationForm', 'taskForm', 'opportunityFilters', '/static/js/student-tools.js'):
            self.assertIn(marker, html)
        self.assertNotIn("const USER_NAME = 'Student </script>'", html)

    def test_planner_routes_are_registered_in_main_app(self):
        with patch('student_planner.routes.repository.snapshot', return_value={'applications': [], 'tasks': []}):
            response = self.client.get('/api/user/planner')
        self.assertEqual(200, response.status_code)
        self.assertIn('csrf_token', response.get_json())

    def test_both_avatar_initials_are_rendered_for_each_user(self):
        from bs4 import BeautifulSoup
        for name, email, initial, label in [
                ('Syed Ali', 'syed@example.com', 'S', 'Syed Ali'),
                ('Amna', 'amna@example.com', 'A', 'Amna'),
                ('Nova Admin', 'syed@example.com', 'S', 'My account')]:
            with self.subTest(name=name):
                with self.client.session_transaction() as session:
                    session.update(user_name=name, user_email=email)
                with patch.object(self.web, 'db'), patch.object(self.web.VISITOR_EXECUTOR, 'submit'):
                    response = self.client.get('/user/dashboard')
                html = BeautifulSoup(response.get_data(as_text=True), 'html.parser')
                self.assertEqual(initial, html.select_one('#headerAvatar').get_text(strip=True))
                self.assertEqual(initial, html.select_one('#avatarInitial').get_text(strip=True))
                self.assertEqual(label, html.select_one('#headerName').get_text(strip=True))
                self.assertEqual(label, html.select_one('#sidebarName').get_text(strip=True))

    def test_active_programs_use_real_database_rows_and_iso_dates(self):
        conn = MagicMock()
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [{'id': 91, 'title': 'Admin created program', 'deadline': date(2026, 10, 2)}]
        with patch('database.safe_connect', return_value=conn):
            records = NewsDatabase.__new__(NewsDatabase).get_active_programs(20)
        self.assertEqual('2026-10-02', records[0]['deadline'])
        self.assertEqual(91, records[0]['id'])
        sql, params = cursor.execute.call_args.args
        self.assertIn('is_active=TRUE', sql)
        self.assertIn('deadline >= CURRENT_DATE', sql)
        self.assertEqual((20,), params)
        conn.close.assert_called_once()

    def test_admin_program_toggle_has_working_database_method(self):
        conn = MagicMock()
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.rowcount = 1
        with patch('database.safe_connect', return_value=conn):
            changed = NewsDatabase.__new__(NewsDatabase).toggle_program_active(7, False)
        self.assertTrue(changed)
        self.assertEqual((False, 7), cursor.execute.call_args.args[1])
        conn.commit.assert_called_once()
        conn.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
