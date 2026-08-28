import os

html_files = []
for root, _, files in os.walk('templates'):
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

for root, _, files in os.walk('analytics_revenue_portal/templates'):
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

# We'll just patch base_saas.html, index.html, dashboard.html, user_dashboard.html, and user_login.html since they are the entry points.
targets = [
    'templates/base_saas.html',
    'templates/index.html',
    'templates/dashboard.html',
    'templates/user_dashboard.html',
    'templates/user_login.html',
    'templates/admin_login.html'
]

for t in targets:
    if os.path.exists(t):
        with open(t, 'r', encoding='utf-8') as f:
            content = f.read()
        if '<link rel="manifest"' not in content:
            content = content.replace('</head>', '  <link rel="manifest" href="/static/manifest.json">\n</head>')
            with open(t, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Patched {t}")
