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


def _social_studio_candidates():
    """Return trusted local Social Studio launch targets in priority order."""
    configured_app = (os.getenv('SOCIAL_STUDIO_EXE') or '').strip()
    configured_setup = (os.getenv('SOCIAL_STUDIO_INSTALLER') or '').strip()
    local_app_data = Path(os.getenv('LOCALAPPDATA') or Path.home() / 'AppData' / 'Local')
    desktop_root = Path.home() / 'OneDrive' / 'Desktop' / 'social media expert'

    app_candidates = [
        Path(configured_app) if configured_app else None,
        local_app_data / 'Programs' / 'NovaBrief Social Studio' / 'NovaBrief Social Studio.exe',
        desktop_root / 'release' / 'win-unpacked' / 'NovaBrief Social Studio.exe',
    ]
    setup_candidates = [
        Path(configured_setup) if configured_setup else None,
        desktop_root / 'release' / f'NovaBrief-Social-Studio-Setup-{SOCIAL_STUDIO_VERSION}.exe',
    ]
    return (
        next((path for path in app_candidates if path and path.is_file()), None),
        next((path for path in setup_candidates if path and path.is_file()), None),
    )


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


def _open_windows_app(path):
    if os.name != 'nt':
        raise OSError('Social Studio can only be opened from the Windows version of Nova OS.')
    creation_flags = getattr(subprocess, 'DETACHED_PROCESS', 0) | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
    subprocess.Popen(
        [str(path)],
        cwd=str(path.parent),
        close_fds=True,
        creationflags=creation_flags,
    )


@social_bp.route('/dashboard')
@admin_required
def dashboard():
    app_path, setup_path = _social_studio_candidates()
    return render_template(
        'social_dashboard.html',
        studio_version=SOCIAL_STUDIO_VERSION,
        studio_ready=bool(app_path),
        setup_ready=bool(setup_path),
    )


@social_bp.route('/api/studio-status')
@admin_required
def studio_status():
    app_path, setup_path = _social_studio_candidates()
    return jsonify({
        'status': 'ready' if app_path else 'setup_required',
        'version': SOCIAL_STUDIO_VERSION,
        'can_launch': bool(app_path),
        'can_install': bool(setup_path),
    })


@social_bp.route('/api/launch-studio', methods=['POST'])
@admin_required
def launch_studio():
    if not _same_origin():
        return jsonify({'status': 'error', 'message': 'This action must be started from Nova OS.'}), 403
    app_path, _ = _social_studio_candidates()
    if not app_path:
        return jsonify({'status': 'error', 'message': 'Social Studio is not installed yet. Run setup first.'}), 404
    try:
        _open_windows_app(app_path)
        return jsonify({'status': 'success', 'message': 'NovaBrief Social Studio is opening.'})
    except OSError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@social_bp.route('/api/install-studio', methods=['POST'])
@admin_required
def install_studio():
    if not _same_origin():
        return jsonify({'status': 'error', 'message': 'This action must be started from Nova OS.'}), 403
    _, setup_path = _social_studio_candidates()
    if not setup_path:
        return jsonify({'status': 'error', 'message': 'The Social Studio 1.1.1 setup file was not found.'}), 404
    try:
        _open_windows_app(setup_path)
        return jsonify({'status': 'success', 'message': 'Social Studio setup is opening.'})
    except OSError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500
