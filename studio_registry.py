import json
from pathlib import Path


REQUIRED_FIELDS = {'id', 'name', 'url', 'icon'}


def get_agent_studios(project_root=None):
    """Discover agent studios from *_agent/studio.json manifests."""
    root = Path(project_root) if project_root else Path(__file__).resolve().parent
    studios = []

    for manifest_path in root.glob('*_agent/studio.json'):
        try:
            studio = json.loads(manifest_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue

        if not isinstance(studio, dict) or not REQUIRED_FIELDS.issubset(studio):
            continue
        if not str(studio['url']).startswith('/') or '/' in str(studio['icon']):
            continue

        studios.append({
            'id': str(studio['id']),
            'name': str(studio['name']),
            'url': str(studio['url']),
            'icon': str(studio['icon']),
            'order': int(studio.get('order', 100)),
        })

    return sorted(studios, key=lambda item: (item['order'], item['name'].lower()))
