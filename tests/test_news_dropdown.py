import unittest
from unittest.mock import patch, MagicMock
from web_server import app

class TestNewsTop10Dropdown(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_public_news_more_than_10_articles(self):
        # Generate 15 mock articles
        mock_articles = [
            {
                'id': i,
                'title': f'Tech News Title {i}',
                'summary': f'Summary of article {i}',
                'source': 'TechCrunch',
                'url': f'https://example.com/{i}',
                'published_at': '2026-10-25 12:00:00',
                'news_topics': ['AI', 'Tech'],
                'companies': ['Google'],
                'why_important': 'Big deal',
                'why_care': 'Read this'
            }
            for i in range(1, 16)
        ]

        with patch('web_server.db.get_recent_articles', return_value=mock_articles):
            response = self.app.get('/news')
            self.assertEqual(response.status_code, 200)
            html = response.data.decode('utf-8')

            # Verify initial news feed container
            self.assertIn('id="initialNewsFeed"', html)
            # Verify See More News dropdown button is present
            self.assertIn('id="toggleMoreNewsBtn"', html)
            self.assertIn('See More News', html)
            self.assertIn('+5 More Briefings', html)
            # Verify expandable feed
            self.assertIn('id="moreNewsFeed"', html)
            self.assertIn('toggleMoreNews()', html)

            # Check that top 10 articles are in initialNewsFeed
            initial_chunk = html.split('id="initialNewsFeed"')[1].split('id="seeMoreNewsContainer"')[0]
            for i in range(1, 11):
                self.assertIn(f'Tech News Title {i}', initial_chunk)
            # Check that article 11-15 are NOT in initialNewsFeed
            for i in range(11, 16):
                self.assertNotIn(f'Tech News Title {i}', initial_chunk)

            # Check that articles 11-15 ARE in moreNewsFeed
            more_chunk = html.split('id="moreNewsFeed"')[1]
            for i in range(11, 16):
                self.assertIn(f'Tech News Title {i}', more_chunk)

    def test_public_news_less_than_or_equal_to_10_articles(self):
        # Generate 7 mock articles
        mock_articles = [
            {
                'id': i,
                'title': f'Small Feed Title {i}',
                'summary': f'Summary of article {i}',
                'source': 'The Verge',
                'url': f'https://example.com/{i}',
                'published_at': '2026-10-25 12:00:00',
                'news_topics': ['Gadgets'],
                'companies': ['Apple'],
                'why_important': '',
                'why_care': ''
            }
            for i in range(1, 8)
        ]

        with patch('web_server.db.get_recent_articles', return_value=mock_articles):
            response = self.app.get('/news')
            self.assertEqual(response.status_code, 200)
            html = response.data.decode('utf-8')

            self.assertIn('id="initialNewsFeed"', html)
            # When <= 10 articles, See More dropdown should not appear
            self.assertNotIn('id="toggleMoreNewsBtn"', html)
            self.assertNotIn('id="moreNewsFeed"', html)

    def test_user_dashboard_template_contains_top10_and_dropdown(self):
        with open('templates/user_dashboard.html', 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn('top10 = arts.slice(0, 10)', content)
        self.assertIn('remaining = arts.slice(10)', content)
        self.assertIn('id="userPrimaryFeed"', content)
        self.assertIn('id="userSeeMoreContainer"', content)
        self.assertIn('id="userToggleMoreBtn"', content)
        self.assertIn('id="userMoreFeed"', content)
        self.assertIn('function toggleUserMoreNews()', content)

if __name__ == '__main__':
    unittest.main()
