from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
from functools import wraps
from database import NewsDatabase
import os

seo_bp = Blueprint('seo', __name__, template_folder='templates')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('admin_login_page'))
        return f(*args, **kwargs)
    return decorated_function

@seo_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('seo_dashboard.html')

def init_seo_db():
    try:
        db = NewsDatabase()
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS keyword_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT, position INTEGER, change INTEGER, volume INTEGER)''')
        conn.commit()
        conn.close()
    except Exception:
        pass

init_seo_db()

@seo_bp.route('/keywords')
@admin_required
def keywords():
    try:
        db = NewsDatabase()
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM keyword_tracking")
        kws = [dict(row) for row in cursor.fetchall()]
        conn.close()
    except Exception:
        kws = []
    return render_template('seo_keywords.html', keywords=kws)


@seo_bp.route('/content')
@admin_required
def content_assistant():
    return render_template('seo_content.html')


@seo_bp.route('/api/generate', methods=['POST'])
@admin_required
def generate_content():
    data = request.get_json() or {}
    keyword = (data.get('keyword') or 'AI Technology').strip()
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return jsonify({'status': 'error', 'html': 'Gemini API key is missing. Please configure it in your environment variables.'})

    try:
        import google.generativeai as genai
        import markdown
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
You are an elite, highly experienced SEO Agent and Content Strategist. Your goal is to take a website to the top of Google search results and drive massive organic traffic. 

The user wants to target the following topic/keyword: "{keyword}"

Please generate a comprehensive, highly optimized SEO strategy in markdown format. 
Structure your response exactly like this:

### 🎯 Primary & Secondary Keywords
List the absolute best primary keyword and 5 high-converting, low-competition secondary/long-tail keywords related to the topic. Explain briefly why these keywords will rank easily.

### 📝 SEO Meta Tags
Provide a compelling Meta Title (under 60 characters) and Meta Description (under 160 characters) engineered for a high Click-Through Rate (CTR).

### 📑 Optimized Content Outline
Provide an H1, H2, and H3 structure for an article that will outrank competitors.

### ✍️ Draft Article (Intro & First Section)
Write the first 2-3 paragraphs of the article. Use NLP-friendly terms, keep sentences concise, and make it highly engaging to reduce bounce rate.

Do not include any generic filler text, just the highly professional SEO output.
"""
        response = model.generate_content(prompt)
        
        # Convert markdown to HTML for the dashboard
        html_output = markdown.markdown(response.text)
        
        # Wrap it in Tailwind styling so it looks beautiful on the admin dashboard
        styled_html = f'''
        <div class="text-left space-y-4 text-slate-700 prose prose-slate max-w-none">
            {html_output.replace('h3', 'h3 class="text-lg font-bold text-slate-800 mt-6 border-b pb-1"').replace('h2', 'h2 class="text-xl font-bold text-blue-700 mt-8 mb-2"').replace('p', 'p class="leading-relaxed mb-4"').replace('ul', 'ul class="list-disc pl-5 space-y-1 mb-4"')}
        </div>
        '''
        
        return jsonify({'status': 'success', 'html': styled_html})
        
    except Exception as e:
        return jsonify({'status': 'error', 'html': f'<div class="text-red-500 font-bold">Error generating SEO content: {str(e)}</div>'})

