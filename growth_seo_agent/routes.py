import os
from functools import wraps
from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for
from database import safe_connect

seo_bp = Blueprint('seo', __name__, template_folder='templates')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('admin_login_page'))
        return f(*args, **kwargs)
    return decorated_function

def ensure_keyword_table():
    conn = safe_connect()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS seo_keywords (
        id SERIAL PRIMARY KEY, keyword TEXT UNIQUE NOT NULL,
        position INTEGER, previous_position INTEGER, search_volume INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

@seo_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('seo_dashboard.html')

@seo_bp.route('/content')
@admin_required
def content_studio():
    return render_template('seo_content.html')

@seo_bp.route('/keywords')
@admin_required
def keywords():
    import psycopg2.extras
    ensure_keyword_table()
    conn = safe_connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('SELECT * FROM seo_keywords ORDER BY created_at DESC')
    rows = []
    for row in cursor.fetchall():
        item = dict(row)
        current, previous = item.get('position'), item.get('previous_position')
        item['change'] = (previous - current) if current and previous else 0
        item['volume'] = item.get('search_volume') or 0
        rows.append(item)
    conn.close()
    return render_template('seo_keywords.html', keywords=rows)

@seo_bp.route('/api/keywords', methods=['POST'])
@admin_required
def add_keyword():
    data = request.get_json(silent=True) or request.form.to_dict()
    keyword = (data.get('keyword') or '').strip()
    if not keyword:
        return jsonify({'status': 'error', 'message': 'Keyword is required.'}), 400
    try:
        position = int(data['position']) if data.get('position') else None
        volume = int(data.get('search_volume') or 0)
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Position and volume must be numbers.'}), 400
    ensure_keyword_table()
    conn = safe_connect()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO seo_keywords (keyword, position, previous_position, search_volume)
        VALUES (%s, %s, %s, %s) ON CONFLICT (keyword) DO UPDATE SET
        previous_position=seo_keywords.position, position=EXCLUDED.position,
        search_volume=EXCLUDED.search_volume, updated_at=CURRENT_TIMESTAMP''',
        (keyword, position, position, volume))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Keyword saved.'})

@seo_bp.route('/generate_content', methods=['POST'])
@admin_required
def generate_content():
    data = request.get_json(silent=True) or {}
    keyword = (data.get('keyword') or 'AI Technology').strip()
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return jsonify({'status': 'error', 'html': 'Gemini API key is missing. Please configure it in your environment variables.'}), 503
    try:
        import google.generativeai as genai
        import markdown
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        prompt = f'''Create a concise SEO plan for Nova Brief targeting "{keyword}". Include one primary and five long-tail keywords, an optimized title and meta description, Organization schema and Search Console advice, and three blog titles. Return clean Markdown.'''
        response = model.generate_content(prompt)
        return jsonify({'status': 'success', 'html': f'<div class="prose prose-slate max-w-none">{markdown.markdown(response.text)}</div>'})
    except Exception as exc:
        return jsonify({'status': 'error', 'html': f'Unable to generate SEO content: {str(exc)}'}), 500
