import unittest

from flask import Flask, render_template
from jinja2 import ChoiceLoader, FileSystemLoader


class ProfessionalUiTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__, template_folder='templates')
        self.app.testing = True
        self.app.jinja_loader = ChoiceLoader([
            FileSystemLoader('templates'),
            FileSystemLoader('analytics_revenue_portal/templates'),
        ])

    def render(self, template, **context):
        with self.app.test_request_context('/'):
            return render_template(template, **context)

    def test_shared_shell_contains_focused_navigation(self):
        html = self.render('analytics_settings.html')
        self.assertIn('Studios', html)
        self.assertIn('Revenue', html)
        self.assertIn('Social Studio', html)
        self.assertIn('SEO Studio', html)
        self.assertIn('Support inbox', html)
        self.assertIn('System operational', html)
        self.assertNotIn('SEO Performance', html)
        self.assertNotIn('AI Insights', html)

    def test_dashboard_renders_real_operational_metrics(self):
        html = self.render(
            'analytics_dashboard.html',
            total_visitors=3834,
            monthly_visitors=420,
            total_users=72,
            leads=16,
            revenue=0,
        )
        self.assertIn('Platform overview', html)
        self.assertIn('Traffic activity', html)
        self.assertIn('3834', html)
        self.assertNotIn('AI Growth Score', html)

    def test_inbox_empty_state_renders(self):
        html = self.render('messages.html', messages=[])
        self.assertIn('Support inbox', html)
        self.assertIn('Inbox Zero', html)


if __name__ == '__main__':
    unittest.main()
