import os
from functools import wraps
from pathlib import Path
import subprocess
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


import requests
import json

@social_bp.route('/api/generate', methods=['POST'])
@admin_required
def generate_social_content():
    data = request.get_json() or {}
    topic = data.get('topic', '').strip()
    
    if not topic:
        return jsonify({'status': 'error', 'message': 'Topic or URL is required.'}), 400
        
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
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Topic/Content:\n{topic}"}
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"}
    }
    
    try:
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        result_text = resp.json()['choices'][0]['message']['content'].strip()
        
        # Parse JSON
        result = json.loads(result_text)
        return jsonify({'status': 'success', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to generate content: {str(e)}'}), 500
