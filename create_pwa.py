import json
import os
from PIL import Image

manifest = {
    "name": "Nova OS Admin",
    "short_name": "Nova OS",
    "description": "AI SaaS Administrative Portal",
    "start_url": "/admin/dashboard",
    "display": "standalone",
    "background_color": "#0f172a",
    "theme_color": "#6366f1",
    "icons": [
        {
            "src": "/static/icon-192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "/static/icon-512.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ]
}

with open('static/manifest.json', 'w') as f:
    json.dump(manifest, f, indent=4)

# Create the PNG icons from the generated logo
img_path = r'C:\Users\DELL\.gemini\antigravity\brain\50657c5c-0966-4e79-b441-1a8d3b266ada\nova_saas_logo_v5_1787689603879.jpg'
if os.path.exists(img_path):
    img = Image.open(img_path).convert('RGBA')
    img.resize((192, 192)).save('static/icon-192.png', 'PNG')
    img.resize((512, 512)).save('static/icon-512.png', 'PNG')
    print('Manifest and icons created successfully.')
else:
    print('Original logo not found.')
