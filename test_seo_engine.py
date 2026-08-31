import unittest

from growth_seo_agent.engine import audit_site, build_content_brief, inspect_backlink, normalize_site_url


def document(url, body, status=200, content_type='text/html', elapsed_ms=120):
    return {
        'url': url,
        'status': status,
        'headers': {'Content-Type': content_type},
        'text': body,
        'elapsed_ms': elapsed_ms,
        'content_type': content_type,
    }


class SeoEngineTests(unittest.TestCase):
    def test_normalize_site_url(self):
        self.assertEqual('https://example.com', normalize_site_url('example.com/'))
        with self.assertRaises(ValueError):
            normalize_site_url('file:///etc/passwd')

    def test_audit_finds_real_indexability_and_metadata_issues(self):
        pages = {
            'https://example.com': document(
                'https://example.com',
                '<html><head><meta name="robots" content="noindex"></head><body><p>Short page</p></body></html>',
            ),
            'https://example.com/robots.txt': document(
                'https://example.com/robots.txt', 'User-agent: *\nDisallow: /', content_type='text/plain'
            ),
            'https://example.com/sitemap.xml': document(
                'https://example.com/sitemap.xml', '<urlset></urlset>', content_type='application/xml'
            ),
        }

        audit = audit_site('https://example.com', fetcher=lambda url: pages[url])
        keys = {issue['key'] for issue in audit['issues']}

        self.assertTrue({'missing_title', 'missing_description', 'missing_h1', 'noindex', 'robots_blocks_site', 'empty_sitemap'}.issubset(keys))
        self.assertEqual(1, audit['pages_checked'])
        self.assertLess(audit['score'], 100)

    def test_audit_crawls_sitemap_and_detects_duplicate_titles(self):
        healthy_head = '<head><title>Shared title</title><meta name="description" content="Useful description"><meta name="viewport" content="width=device-width"><link rel="canonical" href="{url}"></head>'
        pages = {
            'https://example.com': document('https://example.com', f'<html lang="en">{healthy_head.format(url="https://example.com")}<body><h1>Home</h1><p>{"useful " * 130}</p></body></html>'),
            'https://example.com/robots.txt': document('https://example.com/robots.txt', 'User-agent: *\nAllow: /', content_type='text/plain'),
            'https://example.com/sitemap.xml': document('https://example.com/sitemap.xml', '<urlset><url><loc>https://example.com/about</loc></url></urlset>', content_type='application/xml'),
            'https://example.com/about': document('https://example.com/about', f'<html lang="en">{healthy_head.format(url="https://example.com/about")}<body><h1>About</h1><p>{"original " * 130}</p></body></html>'),
        }

        audit = audit_site('https://example.com', max_pages=10, fetcher=lambda url: pages[url])

        self.assertEqual(2, audit['pages_checked'])
        self.assertEqual(2, sum(issue['key'] == 'duplicate_title' for issue in audit['issues']))

    def test_backlink_monitor_verifies_a_real_link(self):
        result = inspect_backlink(
            'https://publisher.example/resource',
            'https://novabrief.tech',
            fetcher=lambda _: document(
                'https://publisher.example/resource',
                '<a href="https://www.novabrief.tech/guide" rel="nofollow sponsored">NovaBrief guide</a>',
            ),
        )

        self.assertEqual('earned', result['status'])
        self.assertEqual(['nofollow', 'sponsored'], result['attributes'])

    def test_content_brief_is_people_first(self):
        brief = build_content_brief('AI tools for students', 'commercial')
        self.assertIn('compare options', brief['audience_goal'])
        self.assertTrue(any('Avoid keyword repetition' in item for item in brief['quality_checks']))


if __name__ == '__main__':
    unittest.main()
