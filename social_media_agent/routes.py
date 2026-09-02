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
