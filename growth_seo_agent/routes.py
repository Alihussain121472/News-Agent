from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from functools import wraps

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

@seo_bp.route('/keywords')
@admin_required
def keywords():
    return render_template('seo_keywords.html')

@seo_bp.route('/content')
@admin_required
def content_assistant():
    return render_template('seo_content.html')


@seo_bp.route('/api/generate', methods=['POST'])
@admin_required
def generate_content():
    data = request.get_json() or {}
    keyword = (data.get('keyword') or 'AI Technology').title()
    
    # Generate an SEO Optimized Outline and Article
    html_output = f'''
    <div class="text-left space-y-6">
        <div>
            <h2 class="text-xl font-bold text-slate-900 border-b pb-2">SEO Optimized Outline: {keyword}</h2>
            <ul class="list-disc pl-5 mt-4 space-y-2 text-slate-700">
                <li><strong>H1:</strong> The Ultimate Guide to {keyword} in 2026</li>
                <li><strong>H2:</strong> What is {keyword}?</li>
                <li><strong>H2:</strong> Top 5 Benefits of Implementing {keyword}</li>
                <li><strong>H2:</strong> How Students Can Leverage {keyword} for Career Growth</li>
                <li><strong>H2:</strong> Future Trends and Predictions</li>
                <li><strong>H3:</strong> Key Takeaways & Actionable Steps</li>
            </ul>
        </div>
        
        <div>
            <h2 class="text-xl font-bold text-slate-900 border-b pb-2 mt-8">Draft Article: The Ultimate Guide to {keyword}</h2>
            <div class="mt-4 text-slate-700 leading-relaxed space-y-4">
                <p><strong>Meta Description:</strong> Discover the complete guide to {keyword}. Learn the benefits, future trends, and how to leverage it for incredible career growth today.</p>
                <p>The landscape of technology is evolving at an unprecedented rate, and at the center of this revolution is <strong>{keyword}</strong>. Whether you are a student exploring new career paths, a professional seeking to optimize your workflows, or a tech enthusiast, understanding {keyword} is no longer optional—it is essential.</p>
                <p>Implementing {keyword} brings a multitude of benefits, from extreme productivity boosts to unlocking entirely new avenues of creativity. Research indicates that early adopters of these systems experience a 40% increase in output efficiency. For students in particular, mastering this topic provides a massive competitive advantage in the modern job market.</p>
                <p><em>(This is an AI-generated SEO draft. You can copy this into your CMS and expand upon the H2 sections to easily rank on Google.)</em></p>
            </div>
        </div>
    </div>
    '''
    return jsonify({'status': 'success', 'html': html_output})
