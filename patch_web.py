import os
import re

with open('web_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace /api/articles
old_api_articles = '''@app.route('/api/articles')
def get_articles():
    limit = request.args.get('limit', 20, type=int)
    return jsonify(db.get_recent_articles(limit=limit))'''

new_api_articles = '''@app.route('/api/articles')
def get_articles():
    limit = request.args.get('limit', 20, type=int)
    target_date = request.args.get('date')
    user_email = session.get('user_email')
    
    if target_date:
        articles = db.get_articles_by_date(target_date, limit=limit)
    else:
        articles = db.get_recent_articles(limit=limit)
        
    # Personalized sorting if email is provided
    if user_email and not target_date:
        prefs = db.get_user_preferences(user_email)
        pref_keywords = (prefs.get('companies', '') + ' ' + prefs.get('fields', '')).lower().split()
        if pref_keywords:
            def score(a):
                s = 0
                text = (a.get('title', '') + ' ' + a.get('summary', '')).lower()
                for k in pref_keywords:
                    if len(k) > 2 and k in text:
                        s += 1
                return s
            articles.sort(key=score, reverse=True)
            
    return jsonify(articles)'''

content = content.replace(old_api_articles, new_api_articles)

new_routes = '''

# -- Preferences & Memory Vault --

@app.route('/api/user/preferences', methods=['GET', 'POST'])
@user_required
def manage_user_preferences():
    email = session.get('user_email')
    if request.method == 'POST':
        data = request.get_json()
        companies = data.get('companies', '')
        fields = data.get('fields', '')
        db.save_user_preferences(email, companies, fields)
        return jsonify({'status': 'success'})
    return jsonify(db.get_user_preferences(email))

@app.route('/api/user/saved-articles', methods=['GET'])
@user_required
def get_user_saved_articles():
    email = session.get('user_email')
    return jsonify(db.get_saved_articles(email))

@app.route('/api/user/saved-articles/<int:article_id>', methods=['POST', 'DELETE'])
@user_required
def manage_saved_article(article_id):
    email = session.get('user_email')
    if request.method == 'POST':
        db.save_article(email, article_id)
        return jsonify({'status': 'success', 'message': 'Article saved.'})
    elif request.method == 'DELETE':
        db.delete_saved_article(email, article_id)
        return jsonify({'status': 'success', 'message': 'Article removed.'})

'''

if '@app.route(\'/api/user/preferences\')' not in content:
    content = content.replace("@app.route('/api/user/activity')", new_routes + "\n@app.route('/api/user/activity')")

with open('web_server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated web_server.py with new routes")
