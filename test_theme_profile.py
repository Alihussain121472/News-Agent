"""Offline theme consistency, palette contrast and profile-initial regressions."""
from pathlib import Path
import re
import unittest

from user_identity import display_identity


class ProfileTests(unittest.TestCase):
    def test_personal_names_show_their_own_initial(self):
        for name, initial in [('Syed Ali', 'S'), ('  Sarah  Khan ', 'S'), ('Noor', 'N'),
                              ('Élodie', 'É'), ('يوسف', 'ي')]:
            with self.subTest(name=name):
                profile = display_identity(name, 'different@example.com')
                self.assertEqual(initial, profile['initial'])
                self.assertEqual(' '.join(name.split()), profile['name'])

    def test_generic_admin_label_becomes_my_account_and_uses_email_initial(self):
        profile = display_identity('Nova Admin', 'syed@example.com')
        self.assertEqual({'name': 'My account', 'initial': 'S'}, profile)

    def test_missing_profile_uses_safe_fallback_not_a_fake_name(self):
        self.assertEqual({'name': 'My account', 'initial': '?'}, display_identity(None, None))
        self.assertEqual('A', display_identity('', 'alice@example.com')['initial'])


class ThemeTests(unittest.TestCase):
    pages = ['index', 'user_dashboard', 'user_login', 'user_register', 'forgot_password',
             'reset_password', 'blog_list', 'blog_post', 'privacy', 'terms', 'cookies', 'dashboard']

    def test_public_pages_share_theme_initialization(self):
        for page in self.pages:
            with self.subTest(page=page):
                content = Path(f'templates/{page}.html').read_text(encoding='utf-8-sig')
                self.assertIn('include "theme_head.html"', content)
                self.assertIn('class="nova-site', content)
                self.assertNotIn('prefers-color-scheme', content)
                self.assertNotIn('cdn.tailwindcss.com', content)
                self.assertNotIn("localStorage.getItem('color-theme')", content)
                self.assertIn('data-theme-toggle', content)

    def test_compiled_dark_utilities_use_explicit_class_not_os_preference(self):
        config = Path('tailwind.config.js').read_text()
        css = Path('static/css/tailwind.css').read_text()
        self.assertIn("darkMode: 'class'", config)
        self.assertNotIn('prefers-color-scheme:dark', css.replace(' ', ''))
        self.assertIn('.dark ', css)

    def test_reading_and_accent_colors_have_legible_contrast(self):
        css = Path('static/css/website-theme.css').read_text()
        blocks = re.findall(r'(?:^|\n)(?:html\.dark )?\.nova-site \{([^}]+)\}', css)
        self.assertEqual(2, len(blocks))
        def luminance(color):
            rgb = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
            linear = [value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4 for value in rgb]
            return sum(weight * value for weight, value in zip([.2126, .7152, .0722], linear))
        def contrast(a, b):
            values = sorted([luminance(a), luminance(b)])
            return (values[1] + .05) / (values[0] + .05)
        for block in blocks:
            palette = dict(re.findall(r'--theme-(\w+):\s*(#[0-9a-f]{6})', block))
            for foreground in ['text', 'muted', 'blue', 'green', 'purple', 'red', 'amber']:
                for background in ['surface', 'raised']:
                    with self.subTest(foreground=foreground, background=background, palette=palette['bg']):
                        self.assertGreaterEqual(contrast(palette[foreground], palette[background]), 4.5)
        for endpoint in ['#1d4ed8', '#047857']:
            self.assertGreaterEqual(contrast('#ffffff', endpoint), 4.5)


if __name__ == '__main__':
    unittest.main()
