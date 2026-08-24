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
    topics = [
        "How AI is revolutionizing student productivity.",
        "Top 5 certifications you need from Google and Microsoft this year.",
        "Why learning AI automation is the ultimate career cheat code.",
        "Breaking: New student programs launched by big tech companies.",
        "The future of work: How to prepare while still in college."
    ]
    hashtags = ["#AI", "#StudentSuccess", "#TechNews", "#FutureOfWork", "#CareerGrowth"]
    
    generated = 0
    for _ in range(3):
        topic = random.choice(topics)
        tag = random.choice(hashtags)
        post_content = f"🚀 {topic}\n\nDon't get left behind in the AI revolution. Check out our latest breakdown on Nova Brief and discover how you can leverage this to accelerate your career today! 💡👇\n\nLink in bio.\n\n{tag} #NovaBrief"
        
        # Save to database (Assuming db has a method, if not we will just use raw sqlite)
        import sqlite3
        try:
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO social_posts (campaign_id, platform, post_content, scheduled_time, status)
                              VALUES (?, ?, ?, datetime('now', '+1 day'), ?)''',
                           (1, random.choice(['Twitter', 'LinkedIn']), post_content, 'draft'))
            conn.commit()
            conn.close()
            generated += 1
        except Exception as e:
            pass
            
    return jsonify({'status': 'success', 'message': f'Successfully generated {generated} professional AI social media posts. They are saved in your drafts.'})

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

