"""Authenticated student APIs; existing account cookies are the authority."""
import hmac
import secrets
from datetime import datetime
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from flask import Blueprint, Response, current_app, jsonify, request, session
from psycopg2 import Error as DatabaseError

from . import repository
from .calendar import build_calendar
from .validation import payload, text

planner_bp = Blueprint('student_planner', __name__)


def csrf_token():
    if not session.get('planner_csrf'):
        session['planner_csrf'] = secrets.token_urlsafe(32)
    return session['planner_csrf']


@planner_bp.before_request
def protect_planner():
    if session.get('role') != 'user' or not session.get('user_email'):
        return jsonify(message='Please sign in to use your student planner.'), 401
    if request.method in {'POST', 'PATCH', 'DELETE'}:
        expected = session.get('planner_csrf', '')
        supplied = request.headers.get('X-CSRF-Token', '')
        origin = request.headers.get('Origin')
        try:
            same_origin = not origin or (urlsplit(origin).scheme == request.scheme and
                                         urlsplit(origin).netloc == request.host)
        except ValueError:
            same_origin = False
        if (not expected or not hmac.compare_digest(expected.encode('utf-8'), supplied.encode('utf-8'))
                or not same_origin):
            return jsonify(message='Your session could not be verified. Refresh this page and try again.'), 403


@planner_bp.after_request
def private_response(response):
    response.headers['Cache-Control'] = 'private, no-store'
    return response


@planner_bp.errorhandler(ValueError)
def invalid_input(error):
    return jsonify(message=str(error)), 400


@planner_bp.errorhandler(LookupError)
def missing_item(error):
    return jsonify(message=str(error)), 404


@planner_bp.errorhandler(DatabaseError)
def storage_unavailable(error):
    # Never log SQL parameters, student notes or connection secrets.
    current_app.logger.error('Student planner storage failure (%s)', type(error).__name__)
    return jsonify(message='Your planner could not connect to storage. Please retry; no successful save has been confirmed.'), 503


@planner_bp.get('/api/user/planner')
def get_planner():
    return jsonify(**repository.snapshot(session['user_email']), csrf_token=csrf_token())


@planner_bp.get('/api/user/opportunities')
def get_opportunities():
    query = text(request.args.get('q', ''), 'Search', 100)
    company = text(request.args.get('company', ''), 'Organization', 200)
    category = text(request.args.get('category', ''), 'Category', 100)
    within = request.args.get('within', '')
    sort = request.args.get('sort', 'deadline')
    page = request.args.get('page', '1')
    if not page.isascii() or not page.isdigit() or len(page) > 6 or not 1 <= int(page) <= 100000:
        raise ValueError('Choose a valid results page.')
    if within not in {'', '7', '30'} or sort not in {'deadline', 'newest'}:
        raise ValueError('Choose a valid deadline filter and sort order.')
    return jsonify(**repository.opportunities(session['user_email'], query, company, category,
                                              int(within) if within else None, sort, int(page)),
                   csrf_token=csrf_token())


@planner_bp.route('/api/user/planner/applications', methods=['POST'])
def create_application():
    data = payload(request.get_json(silent=True), 'application')
    return jsonify(status='success', item=repository.create(session['user_email'], 'application', data)), 201


@planner_bp.route('/api/user/planner/tasks', methods=['POST'])
def create_task():
    data = payload(request.get_json(silent=True), 'task')
    return jsonify(status='success', item=repository.create(session['user_email'], 'task', data)), 201


def mutate(kind, item_id):
    if not 0 < item_id <= 2147483647:
        raise ValueError('Please select a valid planner item.')
    if request.method == 'DELETE':
        repository.delete(session['user_email'], kind, item_id)
        return jsonify(status='success')
    data = payload(request.get_json(silent=True), kind, partial=True)
    return jsonify(status='success', item=repository.update(session['user_email'], kind, item_id, data))


@planner_bp.route('/api/user/planner/applications/<int:item_id>', methods=['PATCH', 'DELETE'])
def application(item_id):
    return mutate('application', item_id)


@planner_bp.route('/api/user/planner/tasks/<int:item_id>', methods=['PATCH', 'DELETE'])
def task(item_id):
    return mutate('task', item_id)


@planner_bp.get('/api/user/planner/calendar.ics')
def calendar_download():
    data = repository.snapshot(session['user_email'])
    calendar = build_calendar(data, today=datetime.now(ZoneInfo('Asia/Karachi')).date())
    return Response(calendar, mimetype='text/calendar', headers={
        'Content-Disposition': 'attachment; filename="novabrief-student-planner.ics"'})
