import os
import re

with open('web_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

route_code = '''
@app.route('/blog/<slug>')
def view_article(slug):
    db = NewsDatabase()
    conn = safe_connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM blog_articles WHERE slug = %s", (slug,))
    article = cursor.fetchone()
    conn.close()
    
    if not article:
        return "Article not found", 404
        
    return render_template('article_view.html', article=article)
'''

if '@app.route(\'/blog/<slug>\')' not in content:
    # insert before @app.route('/api/subscribe')
    content = content.replace("@app.route('/api/subscribe')", route_code + "\n@app.route('/api/subscribe')")
    
    with open('web_server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added /blog/<slug> route")
else:
    print("Route already exists")
