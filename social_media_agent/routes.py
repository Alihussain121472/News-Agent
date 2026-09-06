import os
from functools import wraps
import json
import webbrowser
import requests
from urllib.parse import urlparse
from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

social_bp = Blueprint('social', __name__, template_folder='templates')
SOCIAL_STUDIO_VERSION = '1.1.1'

def admin_required(handler):
    @wraps(handler)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            if request.path.startswith('/social/api/'):
                return jsonify({'status': 'error', 'message': 'Please log in as an admin first.'}), 401
            return redirect(url_for('admin_login_page'))
        return handler(*args, **kwargs)
    return decorated_function

def _is_cloud_hosted():
    return os.name != 'nt' or 'RENDER' in os.environ


def _same_origin():
    source = request.headers.get('Origin') or request.headers.get('Referer')
    if not source:
        return os.getenv('FLASK_ENV', 'development').strip().lower() != 'production'
    try:
        source_url = urlparse(source)
        app_url = urlparse(request.host_url)
        return source_url.scheme == app_url.scheme and source_url.netloc == app_url.netloc
    except ValueError:
        return False


def _open_windows_app():
    """Open the local Social Studio page for desktop development."""
    webbrowser.open('http://127.0.0.1:5000/social/dashboard')

@social_bp.route('/dashboard')
@admin_required
def dashboard():
    is_cloud = _is_cloud_hosted()
    return render_template(
        'social_dashboard.html',
        studio_version=SOCIAL_STUDIO_VERSION,
        is_cloud=is_cloud,
        studio_ready=False if is_cloud else True, # If local, assume ready since they have it installed
        setup_ready=False
    )


@social_bp.route('/api/studio-status')
@admin_required
def studio_status():
    return jsonify({
        'status': 'ready' if os.environ.get('GROQ_API_KEY') else 'needs_configuration',
        'version': SOCIAL_STUDIO_VERSION,
        'cloud': _is_cloud_hosted(),
        'model': os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile'),
    })


@social_bp.route('/api/launch-studio', methods=['POST'])
@admin_required
def launch_studio():
    if not _same_origin():
        return jsonify({'status': 'error', 'message': 'This action must be started from Nova OS.'}), 403
    if _is_cloud_hosted():
        return jsonify({'status': 'success', 'message': 'Social Studio is available in this browser.'})
    _open_windows_app()
    return jsonify({'status': 'success', 'message': 'Social Studio opened.'})

@social_bp.route('/api/generate', methods=['POST'])
@admin_required
def generate_social_content():
    data = request.get_json(silent=True) or {}
    topic = str(data.get('topic') or '').strip()
    
    if not topic:
        return jsonify({'status': 'error', 'message': 'Topic or URL is required.'}), 400
    if len(topic) > 12000:
        return jsonify({'status': 'error', 'message': 'Topic or content must be 12,000 characters or fewer.'}), 400
        
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        return jsonify({'status': 'error', 'message': 'Groq API Key is not configured.'}), 500
        
    system_prompt = """You are an expert Social Media Manager for NovaBrief Tech. 
Your task is to take the user's topic, article, or URL and generate highly engaging, platform-specific social media posts.

Generate three distinct posts:
1. X (Twitter): Short, punchy, engaging, max 280 characters, 1-2 relevant hashtags.
2. LinkedIn: Professional, insightful, longer form, focusing on career/tech impact, 3-4 hashtags.
3. Facebook/Instagram: Casual, visual-friendly, engaging question to drive comments, emojis, 3-5 hashtags.

Return ONLY a valid JSON object with the keys: "twitter", "linkedin", "facebook" containing the text for each platform. Do not include markdown code blocks around the JSON."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        model_name = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile').strip()
            
        payload = {
            'model': model_name,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': topic}
            ],
            'temperature': 0.7,
            'max_tokens': 800,
            'response_format': {'type': 'json_object'}
        }
        
        resp = requests.post('https://api.groq.com/openai/v1/chat/completions', headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        result_text = resp.json()['choices'][0]['message']['content'].strip()
        result = json.loads(result_text)
        if not isinstance(result, dict) or not all(isinstance(result.get(key), str) for key in ('twitter', 'linkedin', 'facebook')):
            raise ValueError('Groq returned an incomplete social content response.')
        return jsonify({'status': 'success', 'data': result})
    except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as e:
        return jsonify({'status': 'error', 'message': f'Invalid AI response: {e}'}), 502
    except requests.RequestException as e:
        return jsonify({'status': 'error', 'message': f'Groq API request failed: {e}'}), 502
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'API Error: {str(e)}'}), 500
