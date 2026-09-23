"""Authoritative grading and durable assessment state."""
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import uuid
import json
import secrets

from . import repository as repo, runtime
from .content import EXERCISES, QUIZZES, MODULES

EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix='python_practice')
ASSESSMENT_CODES = ['temperature','leap','histogram','ratio','json-api','test-isolation','csv','identifier','wallet','study-report']
ASSESSMENT_QUIZZES = [f'q-{i}-2' for i in range(10)]


def normalized(text):
    # Preserve meaningful spaces and blank lines; tolerate platform line endings
    # and a single final newline only.
    text = text.replace('\r\n','\n')
    return text[:-1] if text.endswith('\n') else text


def grade(exercise, code, cancel):
    results = []
    for index, test in enumerate(exercise['tests']):
        if cancel.is_set():
            return dict(status='stopped', score=0, tests=results)
        result = runtime.execute(code, test['stdin'], test['files'], test['argv'], cancel)
        equal = normalized(result['stdout'])==normalized(test['expected'])
        if exercise.get('comparison')=='json':
            try:
                equal = json.loads(result['stdout'])==json.loads(test['expected'])
            except (ValueError, TypeError):
                equal = False
        passed = result['status']=='ok' and equal
        feedback = dict(name=f'{"Hidden" if test["hidden"] else "Example"} test {index+1}', passed=passed,
                        status='passed' if passed else ('incorrect_output' if result['status']=='ok' else result['status']))
        # Never include hidden input, expected values, or learner stdout/stderr:
        # a learner could deliberately echo the hidden input via an exception.
        if not test['hidden']:
            feedback.update(input=test['stdin'],expected=test['expected'],actual=result['stdout'],stderr=result['stderr'])
        results.append(feedback)
    score = sum(r['passed'] for r in results)/len(results)
    return dict(status='passed' if score==1 else 'needs_work', score=score, tests=results)


def exam_result(exam, cancel):
    topics = {m['id']:dict(title=m['title'],earned=0,total=0) for m in MODULES}
    items = []
    for id in exam['quizzes']:
        quiz = QUIZZES[id]
        answer = exam['answers'].get(id)
        earned = int(answer==quiz['answer'])
        topics[quiz['module']]['earned'] += earned
        topics[quiz['module']]['total'] += 1
        items.append(dict(id=id,earned=earned,answer=quiz['answer'],selected=answer,explanation=quiz['explanation']))
    for id in exam['codes']:
        exercise = EXERCISES[id]
        code = exam['answers'].get(id, '')
        result = grade(exercise, code, cancel) if code.strip() else dict(score=0,status='unanswered',tests=[])
        topics[exercise['module']]['earned'] += result['score']
        topics[exercise['module']]['total'] += 1
        items.append(dict(id=id,code=code,earned=result['score'],**{k:v for k,v in result.items() if k!='score'}))
    earned = sum(t['earned'] for t in topics.values())
    total = len(exam['quizzes'])+len(exam['codes'])
    return dict(id=exam['id'],score=round(100*earned/total),earned=earned,total=total,topics=topics,items=items,
                finished=time.time(),timed=bool(exam['deadline']),revise=[t['title'] for t in topics.values() if t['earned']<t['total']])


def launch(email, job):
    EXECUTOR.submit(work, email, job)


def work(email, job):
    cancel = threading.Event()
    done = threading.Event()
    def monitor():
        heartbeat = time.monotonic()
        while not done.wait(.3):
            try:
                if repo.get_job(email,job['id']).get('cancelled'):
                    cancel.set()
                    return
                if time.monotonic() - heartbeat >= 10:
                    repo.update_job(email, job['id'], {})
                    heartbeat = time.monotonic()
            except Exception:
                cancel.set()
                return
    watcher = threading.Thread(target=monitor,daemon=True)
    watcher.start()
    try:
        kind = job['kind']
        if kind=='exam':
            result = exam_result(job['exam'],cancel)
        else:
            exercise = EXERCISES[job['exercise']]
            if kind=='run':
                result = runtime.execute(job['code'],job['stdin'],exercise['files'],job.get('argv',exercise['argv']),cancel)
            else:
                result = grade(exercise,job['code'],cancel)
        if cancel.is_set():
            repo.update_job(email,job['id'],dict(status='stopped',result=dict(result,status='stopped')))
            if kind=='exam':
                with repo.state(email) as state:
                    if state['active_exam'] and state['active_exam']['id']==job['exam']['id']:
                        state['active_exam']['status']='active'
            return
        if kind in {'submit','exam'}:
            with repo.state(email) as state:
                if kind=='submit':
                    record = dict(exercise=job['exercise'],code=job['code'],result=result,at=time.time())
                    state['submissions']=(state['submissions']+[record])[-100:]
                    if result['score']==1:
                        state['completed'][job['exercise']]=time.time()
                else:
                    state['exams']=(state['exams']+[result])[-20:]
                    if state['active_exam'] and state['active_exam']['id']==job['exam']['id']:
                        state['active_exam']=None
        repo.update_job(email,job['id'],dict(status='done',result=result))
    except Exception:
        import logging
        logging.getLogger(__name__).exception('Practice runner failed for job %s',job['id'])
        repo.update_job(email,job['id'],dict(status='error',message='Execution could not finish. Your code is saved. Please retry.'))
        if job['kind']=='exam':
            with repo.state(email) as state:
                if state['active_exam'] and state['active_exam']['id']==job['exam']['id']:
                    state['active_exam']['status']='active'
    finally:
        done.set()
        watcher.join()


def new_exam(timed):
    now=time.time()
    # Keep full topic coverage while allowing a fresh assessment on each attempt.
    codes = [secrets.choice([e['id'] for e in EXERCISES.values()
                            if e['module']==m['id'] and e['mode']=='practice'
                            and e['difficulty']!='Beginner']) for m in MODULES]
    quizzes = [secrets.choice([q['id'] for q in QUIZZES.values() if q['module']==m['id']]) for m in MODULES]
    return dict(id=str(uuid.uuid4()),started=now,deadline=now+5400 if timed else None,
                codes=codes,quizzes=quizzes,answers={},flags=[],inputs={},status='active')
