import hmac
import secrets
import time
from urllib.parse import urlsplit

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session
from psycopg2 import Error as DatabaseError

from . import repository as repo, runtime, service
from .content import EXERCISES, QUIZZES, catalog

practice_bp = Blueprint('python_practice',__name__)


@practice_bp.before_request
def protect():
    if session.get('role')!='user' or not session.get('user_email'):
        if request.path.startswith('/api/'):
            return jsonify(message='Please sign in to continue.'),401
        return redirect('/user/login')
    if request.method=='POST':
        token=session.get('practice_csrf','')
        supplied=request.headers.get('X-CSRF-Token','')
        origin=request.headers.get('Origin')
        same_origin = not origin or (urlsplit(origin).scheme==request.scheme and urlsplit(origin).netloc==request.host)
        if not token or not hmac.compare_digest(token.encode(),supplied.encode()) or not same_origin:
            return jsonify(message='Session verification failed. Refresh and retry.'),403


@practice_bp.after_request
def private(response):
    response.headers['Cache-Control']='private, no-store'
    return response


@practice_bp.errorhandler(ValueError)
def invalid(exc):
    return jsonify(message=str(exc)),400


@practice_bp.errorhandler(LookupError)
def missing(exc):
    return jsonify(message=str(exc)),404


@practice_bp.errorhandler(DatabaseError)
def database_error(exc):
    current_app.logger.error('Practice database unavailable: %s',type(exc).__name__)
    return jsonify(message='Progress storage is unavailable. Your save has not been confirmed. Please retry.'),503


def payload():
    data=request.get_json(silent=True)
    if not isinstance(data,dict): raise ValueError('A JSON object is required.')
    return data


def text(value, limit=40000):
    if not isinstance(value,str) or len(value)>limit: raise ValueError(f'Text must be at most {limit} characters.')
    return value


def exercise(id):
    if id not in EXERCISES: raise LookupError('Exercise not found.')
    return EXERCISES[id]


@practice_bp.get('/user/python')
def hub():
    return render_template('python_practice.html', user_name=session.get('user_name','Learner'))


@practice_bp.get('/python')
@practice_bp.get('/dashboard/python')
def hub_alias():
    return redirect('/user/python')


@practice_bp.get('/api/python/bootstrap')
def bootstrap():
    session.setdefault('practice_csrf',secrets.token_urlsafe(32))
    return jsonify(**catalog(),state=repo.snapshot(session['user_email']),csrf=session['practice_csrf'],
                   server_time=time.time(),runtime_ready=runtime.available())


@practice_bp.post('/api/python/draft/<id>')
def draft(id):
    exercise(id)
    data=payload()
    code=text(data.get('code'))
    stdin=text(data.get('stdin',''),8000)
    with repo.state(session['user_email']) as state:
        state['drafts'][id]=dict(code=code,stdin=stdin,updated=time.time())
        state['last_exercise']=id
    return jsonify(saved=True)


@practice_bp.post('/api/python/solution/<id>')
def solution(id):
    item=exercise(id)
    if repo.snapshot(session['user_email'])['active_exam']:
        raise ValueError('Finish your Grand Test before revealing practice solutions.')
    return jsonify(code=item['solution'],explanation=item['explanation'])


@practice_bp.post('/api/python/jobs')
def start_job():
    if not runtime.available(): return jsonify(message='Python runtime is not installed. Ask the site administrator to run the practice setup.'),503
    data=payload()
    kind=data.get('kind')
    if kind not in {'run','submit'}: raise ValueError('Choose Run or Submit.')
    item=exercise(data.get('exercise',''))
    code=text(data.get('code'))
    stdin=text(data.get('stdin',''),8000)
    argv=data.get('argv',item['argv'])
    if not isinstance(argv,list) or len(argv)>20 or any(not isinstance(a,str) or len(a)>200 for a in argv):
        raise ValueError('Use at most 20 command-line arguments, each at most 200 characters.')
    email=session['user_email']
    with repo.state(email) as state:
        state['drafts'][item['id']]=dict(code=code,stdin=stdin,updated=time.time())
        state['last_exercise']=item['id']
    job=repo.create_job(email,dict(kind=kind,exercise=item['id'],code=code,stdin=stdin,argv=argv))
    service.launch(email,job)
    return jsonify(id=job['id']),202


@practice_bp.get('/api/python/jobs/<id>')
def job_status(id):
    job=repo.get_job(session['user_email'],id)
    return jsonify(**{k:job[k] for k in ('id','status','result','message') if k in job})


@practice_bp.post('/api/python/jobs/<id>/stop')
def stop_job(id):
    job=repo.get_job(session['user_email'],id)
    if job['kind']=='exam': raise ValueError('Final assessment grading cannot be stopped; it will finish automatically.')
    repo.update_job(session['user_email'],id,dict(cancelled=True))
    return jsonify(stopping=True)


@practice_bp.post('/api/python/quiz')
def submit_quiz():
    data=payload()
    module=data.get('module')
    answers=data.get('answers')
    if module not in [str(i) for i in range(10)] or not isinstance(answers,dict): raise ValueError('Choose a quiz module and answers.')
    selected=[q for q in QUIZZES.values() if q['module']==module]
    if set(answers)!=set(q['id'] for q in selected): raise ValueError('Answer every question before submitting.')
    if any(type(answers[q['id']]) is not int or not 0<=answers[q['id']]<len(q['options']) for q in selected): raise ValueError('Choose valid answers.')
    details=[dict(id=q['id'],correct=answers[q['id']]==q['answer'],answer=q['answer'],selected=answers[q['id']],explanation=q['explanation']) for q in selected]
    result=dict(module=module,score=sum(d['correct'] for d in details),total=len(details),details=details,at=time.time())
    with repo.state(session['user_email']) as state:
        if state['active_exam']: raise ValueError('Finish your Grand Test before submitting a practice quiz.')
        state['quiz_results']=(state['quiz_results']+[result])[-100:]
    return jsonify(result=result)


@practice_bp.post('/api/python/exam/start')
def start_exam():
    data=payload()
    if type(data.get('timed')) is not bool: raise ValueError('Choose timed or untimed.')
    with repo.state(session['user_email']) as state:
        if not state['active_exam']: state['active_exam']=service.new_exam(data['timed'])
        exam=state['active_exam']
    return jsonify(exam=exam,server_time=time.time())


@practice_bp.post('/api/python/exam/answer')
def save_answer():
    data=payload()
    with repo.state(session['user_email']) as state:
        exam=state['active_exam']
        if not exam or exam['id']!=data.get('exam'): raise ValueError('This assessment is no longer active.')
        if exam['status']!='active' or (exam['deadline'] and time.time()>=exam['deadline']): raise ValueError('The assessment is closed for answers. Submit it to view results.')
        id=data.get('id')
        if id in exam['codes']: answer=text(data.get('answer'))
        elif id in exam['quizzes']:
            answer=data.get('answer')
            if type(answer) is not int or not 0<=answer<len(QUIZZES[id]['options']): raise ValueError('Choose a valid answer.')
        else: raise ValueError('Question is not part of this assessment.')
        exam['answers'][id]=answer
    return jsonify(saved=True)


@practice_bp.post('/api/python/exam/finish')
def finish_exam():
    if not runtime.available(): return jsonify(message='The Python runtime is unavailable. Saved assessment answers are preserved.'),503
    email=session['user_email']
    # Keep this state lock through job reservation to prevent two grading jobs.
    with repo.state(email) as state:
        exam=state['active_exam']
        if not exam: raise ValueError('No active assessment.')
        if exam['status']=='grading':
            existing=repo.get_job(email,exam['job'])
            if existing['status'] not in {'error','stopped'}: return jsonify(id=exam['job']),202
        job=repo.create_job(email,dict(kind='exam',exam=exam.copy()))
        exam.update(status='grading',job=job['id'])
    service.launch(email,job)
    return jsonify(id=job['id']),202
