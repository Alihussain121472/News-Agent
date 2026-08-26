from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from functools import wraps

social_bp = Blueprint('social', __name__, template_folder='templates')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('admin_login_page'))
        return f(*args, **kwargs)
    return decorated_function

@social_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('social_dashboard.html')

@social_bp.route('/calendar')
@admin_required
def calendar():
    return render_template('social_calendar.html')

def init_social_db():
    db = NewsDatabase()
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS social_campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, status TEXT, platform TEXT, clicks INTEGER DEFAULT 0, leads INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS social_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER, platform TEXT, post_content TEXT, scheduled_time TIMESTAMP, status TEXT)''')
    conn.commit()
    conn.close()

init_social_db()

@social_bp.route('/campaigns')
@admin_required
def campaigns():
    db = NewsDatabase()
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM social_campaigns")
    camps = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    total_campaigns = len(camps)
    total_clicks = sum(c.get('clicks', 0) for c in camps)
    total_leads = sum(c.get('leads', 0) for c in camps)
    
    return render_template('social_campaigns.html', 
        campaigns=camps, 
        total_campaigns=total_campaigns,
        total_clicks=total_clicks,
        total_leads=total_leads
    )


import random

@social_bp.route('/api/generate-posts', methods=['POST'])
@admin_required
def generate_social_posts():
    db = NewsDatabase()
    
    try:
        import google.generativeai as genai
        import os
        api_key = os.getenv('GEMINI_API_KEY')
        
        # Get recent news to base the tweets on
        recent_news = db.get_recent_articles(limit=3)
        news_context = ""
        if recent_news:
            for article in recent_news:
                news_context += f"- {article.get('title')}: {article.get('summary')}\n"
                
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = """You are an expert Social Media Manager for 'Nova Brief', a top-tier tech platform that provides daily AI news and alerts for prestigious student programs (Google, Microsoft, NASA).
            Your goal is to increase our Twitter reach, engagement, and conversion rate.
            Write 3 highly engaging, viral-style Twitter posts. 
            Rules:
            1. Use strong hooks.
            2. Be professional yet punchy.
            3. Use 2-3 relevant hashtags.
            4. Include a call to action to subscribe or visit novabrief.com.
            5. Base at least one post on the following recent news if available:
            """ + news_context + """
            Format your response strictly as 3 posts separated by '|||'. Do not include post numbers or extra text.
            """
            
            response = model.generate_content(prompt)
            raw_posts = response.text.split('|||')
            posts = [p.strip() for p in raw_posts if p.strip()]
        else:
            # Fallback if no API key
            posts = [
                "🚀 The AI revolution is moving faster than ever. Are you keeping up? Subscribe to Nova Brief for a daily 2-minute breakdown of the most critical tech news. Join 1000+ tech leaders today! 👇\n\nnovabrief.com #AI #TechNews #FutureOfWork",
                "🎓 Students: Stop missing out on top-tier internships. We track Google, Microsoft, and NASA programs and send you 1-click apply links *before* the rush. Subscribe to Nova Brief alerts today! 💼✨\n\nnovabrief.com #StudentSuccess #Internships #TechCareers",
                "💡 Fact: The best opportunities go to those who are informed. Nova Brief delivers elite AI intelligence and career alerts directly to your secure inbox every morning. Upgrade your feed. Subscribe free now. 📈🚀\n\nnovabrief.com #NovaBrief #ArtificialIntelligence"
            ]
            
        generated = 0
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        for post_content in posts[:3]:
            try:
                cursor.execute('''INSERT INTO social_posts (campaign_id, platform, post_content, scheduled_time, status)
                                  VALUES (?, ?, ?, datetime('now', '+1 day'), ?)''',
                               (1, 'Twitter', post_content, 'draft'))
                generated += 1
            except Exception:
                pass
                
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': f'Successfully generated {generated} expert-level Twitter posts. They are saved in your drafts.'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to generate posts: {str(e)}'}), 500

@social_bp.route('/api/posts')
@admin_required
def get_posts():
    db = NewsDatabase()
    import sqlite3
    try:
        conn = sqlite3.connect(db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM social_posts ORDER BY id DESC LIMIT 10")
        posts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'posts': posts})
    except Exception:
        return jsonify({'posts': []})

