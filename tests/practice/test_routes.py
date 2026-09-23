"""Offline API contracts; no real credentials, emails, or database writes."""
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
import time
import unittest
from unittest.mock import patch

from flask import Flask
from python_practice import routes, repository
from python_practice.content import QUIZZES, EXERCISES


class PracticeRouteTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        self.app = Flask(__name__, template_folder=str(root / 'templates'))
        self.app.config.update(TESTING=True, SECRET_KEY='offline-test-key')
        self.app.register_blueprint(routes.practice_bp)
        self.states, self.jobs = {}, {}
        self.client = self.client_for('learner@example.com')
        replacements = {
            'snapshot': lambda email: deepcopy(self.states.setdefault(email, repository.defaults())),
            'state': self.state,
            'create_job': self.create_job,
            'get_job': self.get_job,
        }
        for name, replacement in replacements.items():
            p = patch.object(routes.repo, name, replacement)
            p.start()
            self.addCleanup(p.stop)
        self.launch = patch.object(routes.service, 'launch').start()
        self.addCleanup(patch.stopall)
        patch.object(routes.runtime, 'available', return_value=True).start()

    def client_for(self, email):
        client = self.app.test_client()
        with client.session_transaction() as session:
            session.update(role='user', user_email=email, practice_csrf='test-token')
        return client

    @contextmanager
    def state(self, email):
        data = deepcopy(self.states.setdefault(email, repository.defaults()))
        yield data
        self.states[email] = data

    def create_job(self, email, data):
        job = dict(data, id=str(len(self.jobs) + 1), status='running')
        self.jobs[email, job['id']] = job
        return job

    def get_job(self, email, id):
        if (email, id) not in self.jobs:
            raise LookupError('Execution not found.')
        return self.jobs[email, id]

    def post(self, path, data, client=None):
        return (client or self.client).post('/api/python/' + path, json=data,
            headers={'X-CSRF-Token': 'test-token'})

    def test_authentication_csrf_and_aliases(self):
        anonymous = self.app.test_client()
        self.assertEqual(401, anonymous.get('/api/python/bootstrap').status_code)
        self.assertEqual('/user/login', anonymous.get('/user/python').location)
        self.assertEqual(200, self.client.get('/user/python').status_code)
        for path in ['/python', '/dashboard/python']:
            self.assertEqual('/user/python', self.client.get(path).location)
        self.assertEqual(403, self.client.post('/api/python/draft/welcome', json={'code': ''}).status_code)
        self.assertEqual(403, self.client.post('/api/python/draft/welcome', json={'code': ''},
            headers={'X-CSRF-Token': 'test-token', 'Origin': 'https://other.example.com'}).status_code)

    def test_draft_survives_new_session_and_remains_private(self):
        self.assertEqual(200, self.post('draft/welcome', {'code': 'print(input())', 'stdin': 'Ada'}).status_code)
        fresh = self.client_for('learner@example.com').get('/api/python/bootstrap')
        self.assertEqual('print(input())', fresh.json['state']['drafts']['welcome']['code'])
        self.assertIn('no-store', fresh.headers['Cache-Control'])
        other = self.client_for('other@example.com').get('/api/python/bootstrap')
        self.assertEqual({}, other.json['state']['drafts'])
        for exercise in fresh.json['exercises']:
            self.assertTrue({'tests', 'solution', 'explanation'}.isdisjoint(exercise))

    def test_quiz_scores_are_server_computed_and_explained(self):
        questions = [q for q in QUIZZES.values() if q['module'] == '0']
        answers = {q['id']: q['answer'] for q in questions}
        result = self.post('quiz', {'module': '0', 'answers': answers}).json['result']
        self.assertEqual(3, result['score'])
        self.assertTrue(all(d['explanation'] for d in result['details']))
        self.assertEqual(1, len(self.states['learner@example.com']['quiz_results']))
        self.assertEqual(400, self.post('quiz', {'module': '0', 'answers': {}}).status_code)

    def test_job_ownership(self):
        job = self.post('jobs', {'kind': 'run', 'exercise': 'welcome', 'code': 'print(1)'}).json
        self.assertEqual(200, self.client.get('/api/python/jobs/' + job['id']).status_code)
        self.assertEqual(404, self.client_for('other@example.com').get('/api/python/jobs/' + job['id']).status_code)

    def test_quiz_resume_retry_and_duplicate_submission(self):
        draft=self.post('quiz/start',{'module':'0'}).json['draft']
        ids=draft['questions']
        answers={id:QUIZZES[id]['answer'] for id in ids}
        answers[ids[0]]=(answers[ids[0]]+1)%len(QUIZZES[ids[0]]['options'])
        self.assertEqual(200,self.post('quiz/draft',{'module':'0','attempt':draft['id'],'answers':answers}).status_code)
        restored=self.client_for('learner@example.com').get('/api/python/bootstrap').json['state']['quiz_drafts']['0']
        self.assertEqual(answers,restored['answers'])
        self.assertEqual(draft['id'],self.post('quiz/start',{'module':'0'}).json['draft']['id'])
        other=self.client_for('other@example.com')
        self.assertEqual(400,self.post('quiz/draft',{'module':'0','attempt':draft['id'],'answers':answers},other).status_code)
        submission={'module':'0','attempt':draft['id'],'answers':answers}
        self.assertEqual(2,self.post('quiz',submission).json['result']['score'])
        self.assertEqual(2,self.post('quiz',submission).json['result']['score'])
        self.assertEqual(1,len(self.states['learner@example.com']['quiz_results']))
        retry=self.post('quiz/start',{'module':'0','mode':'missed'}).json['draft']
        self.assertEqual([ids[0]],retry['questions'])
        self.assertEqual(400,self.post('quiz/draft',{'module':'0','attempt':draft['id'],'answers':answers}).status_code)
        result=self.post('quiz',{'module':'0','attempt':retry['id'],'answers':{ids[0]:QUIZZES[ids[0]]['answer']}}).json['result']
        self.assertEqual((1,1),(result['score'],result['total']))
        self.assertEqual({},self.states['learner@example.com']['quiz_drafts'])

    def test_run_inputs_and_exam_drafts_remain_separate(self):
        draft={'code':'print("practice")','stdin':'practice input','argv':['one','two']}
        self.assertEqual(200,self.post('draft/welcome',draft).status_code)
        saved=self.states['learner@example.com']['drafts']['welcome'].copy()
        self.assertEqual(draft['argv'],saved['argv'])
        exam=self.post('exam/start',{'timed':False}).json['exam']
        id=exam['codes'][0]
        self.assertEqual(200,self.post('draft/'+id,draft).status_code)
        self.assertEqual(202,self.post('jobs',{'kind':'run','exercise':id,'exam':exam['id'],'code':'print(2)','stdin':'exam input','argv':['exam']}).status_code)
        state=self.states['learner@example.com']
        self.assertEqual(draft['code'],state['drafts'][id]['code'])
        self.assertEqual('print(2)',state['active_exam']['answers'][id])
        self.assertEqual(['exam'],state['active_exam']['inputs'][id]['argv'])
        self.assertEqual(400,self.post('jobs',{'kind':'submit','exercise':id,'code':'print(2)'}).status_code)
        self.assertEqual(400,self.post('quiz/start',{'module':'0'}).status_code)

    def test_exam_coverage_flags_and_deadline(self):
        exam=self.post('exam/start',{'timed':True}).json['exam']
        self.assertEqual(set(map(str,range(10))),{EXERCISES[id]['module'] for id in exam['codes']})
        self.assertEqual(set(map(str,range(10))),{QUIZZES[id]['module'] for id in exam['quizzes']})
        flag={'exam':exam['id'],'id':exam['codes'][0],'flagged':True}
        self.assertEqual(200,self.post('exam/flag',flag).status_code)
        restored=self.client_for('learner@example.com').get('/api/python/bootstrap').json['state']['active_exam']
        self.assertEqual([flag['id']],restored['flags'])
        self.assertEqual(400,self.post('exam/flag',flag,self.client_for('other@example.com')).status_code)
        self.states['learner@example.com']['active_exam']['deadline']=time.time()-1
        self.assertEqual(400,self.post('exam/flag',flag).status_code)
        self.assertEqual(400,self.post('jobs',{'kind':'run','exercise':flag['id'],'exam':exam['id'],'code':'print(2)'}).status_code)

    def test_timed_exam_persists_deadline_and_answers(self):
        exam = self.post('exam/start', {'timed': True}).json['exam']
        self.assertEqual(10, len(exam['codes']))
        self.assertEqual(10, len(exam['quizzes']))
        self.assertEqual(200, self.post('exam/answer', {'exam': exam['id'], 'id': exam['codes'][0], 'answer': 'print(20)'}).status_code)
        restored = self.client_for('learner@example.com').get('/api/python/bootstrap').json['state']['active_exam']
        self.assertEqual(exam['deadline'], restored['deadline'])
        self.assertEqual('print(20)', restored['answers'][exam['codes'][0]])
        self.assertEqual(400, self.post('solution/welcome', {}).status_code)
        self.states['learner@example.com']['active_exam']['deadline'] = time.time() - 1
        self.assertEqual(400, self.post('exam/answer', {'exam': exam['id'], 'id': exam['codes'][0], 'answer': 'late'}).status_code)

    def test_grading_reservation_is_idempotent_and_recoverable(self):
        self.post('exam/start', {'timed': False})
        first = self.post('exam/finish', {})
        self.assertEqual(202, first.status_code)
        second = self.post('exam/finish', {})
        self.assertEqual(first.json['id'], second.json['id'])
        self.assertEqual(1, self.launch.call_count)
        self.jobs['learner@example.com', first.json['id']]['status'] = 'error'
        retry = self.post('exam/finish', {})
        self.assertEqual(202, retry.status_code)
        self.assertNotEqual(first.json['id'], retry.json['id'])
        self.assertEqual(2, self.launch.call_count)


if __name__ == '__main__':
    unittest.main()
