import os
import glob

html_files = glob.glob('templates/*.html') + glob.glob('analytics_revenue_portal/templates/*.html')
favicon_tags = '''  <link rel="icon" href="/static/favicon.ico" sizes="any">
  <link rel="icon" href="/static/icon-192.png" type="image/png">
  <link rel="apple-touch-icon" href="/static/apple-touch-icon.png">
'''

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove old favicon tags
    import re
    content = re.sub(r'<link rel="icon"[^>]*>\n?', '', content)
    content = re.sub(r'<link rel="apple-touch-icon"[^>]*>\n?', '', content)
    content = re.sub(r'<link rel="shortcut icon"[^>]*>\n?', '', content)
    
    # Insert new ones right after <title> or <head>
    if '</title>' in content:
        content = content.replace('</title>', '</title>\n' + favicon_tags)
    elif '<head>' in content:
        content = content.replace('<head>', '<head>\n' + favicon_tags)
        
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

print("HTML templates updated with proper SEO favicon tags.")
