import json
import tempfile
import unittest
from pathlib import Path

from studio_registry import get_agent_studios


class StudioRegistryTests(unittest.TestCase):
    def test_project_studios_are_discovered_in_order(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for folder, payload in {
                'second_agent': {'id': 'second', 'name': 'Second', 'url': '/second', 'icon': 'fa-2', 'order': 20},
                'first_agent': {'id': 'first', 'name': 'First', 'url': '/first', 'icon': 'fa-1', 'order': 10},
            }.items():
                agent_folder = root / folder
                agent_folder.mkdir()
                (agent_folder / 'studio.json').write_text(json.dumps(payload), encoding='utf-8')

            studios = get_agent_studios(root)

        self.assertEqual(['first', 'second'], [studio['id'] for studio in studios])

    def test_invalid_manifests_are_ignored(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            invalid_agent = root / 'invalid_agent'
            invalid_agent.mkdir()
            (invalid_agent / 'studio.json').write_text('{"name": "Missing fields"}', encoding='utf-8')
            unsafe_agent = root / 'unsafe_agent'
            unsafe_agent.mkdir()
            (unsafe_agent / 'studio.json').write_text(json.dumps({
                'id': 'unsafe', 'name': 'Unsafe', 'url': 'https://example.com', 'icon': '../icon',
            }), encoding='utf-8')

            self.assertEqual([], get_agent_studios(root))

    def test_nova_project_exposes_social_and_seo_studios(self):
        studios = get_agent_studios()
        self.assertEqual(['social-studio', 'seo-studio'], [studio['id'] for studio in studios])


if __name__ == '__main__':
    unittest.main()
