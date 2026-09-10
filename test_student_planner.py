"""Offline regression tests: no database connections, schedulers, or email sends."""

import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from flask import Flask
from psycopg2 import OperationalError

from student_planner import repository, validation
from student_planner.calendar import build_calendar, escape_text, fold_line
from student_planner.routes import planner_bp


class PlannerRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'student-planner-test-only'
        self.app.testing = True
        self.app.register_blueprint(planner_bp)
        self.client = self.app.test_client()

    def login(self, email='student@example.com'):
        with self.client.session_transaction() as session:
            session['role'] = 'user'
            session['user_email'] = email

    def csrf_headers(self):
        with patch('student_planner.routes.repository.snapshot', return_value={
            'applications': [], 'tasks': [],
        }):
            response = self.client.get('/api/user/planner')
        self.assertEqual(200, response.status_code)
        return {'X-CSRF-Token': response.get_json()['csrf_token']}

    def test_all_api_reads_require_login(self):
        for path in ('/api/user/planner', '/api/user/opportunities', '/api/user/planner/calendar.ics'):
            with self.subTest(path=path):
                self.assertEqual(401, self.client.get(path).status_code)

    def test_role_without_student_identity_cannot_read_planner(self):
        with self.client.session_transaction() as session:
            session['role'] = 'user'
        self.assertEqual(401, self.client.get('/api/user/planner').status_code)

    def test_all_mutations_require_login(self):
        for collection in ('applications', 'tasks'):
            for method, suffix in (('POST', ''), ('PATCH', '/1'), ('DELETE', '/1')):
                with self.subTest(collection=collection, method=method):
                    response = self.client.open('/api/user/planner/' + collection + suffix,
                                                method=method, json={})
                    self.assertEqual(401, response.status_code)

    def test_all_mutations_require_csrf_token(self):
        self.login()
        for collection in ('applications', 'tasks'):
            for method, suffix in (('POST', ''), ('PATCH', '/1'), ('DELETE', '/1')):
                with self.subTest(collection=collection, method=method):
                    response = self.client.open('/api/user/planner/' + collection + suffix,
                                                method=method, json={})
                    self.assertEqual(403, response.status_code)

    def test_invalid_csrf_token_is_rejected(self):
        self.login()
        self.csrf_headers()
        response = self.client.post('/api/user/planner/applications', json={},
                                    headers={'X-CSRF-Token': 'not-the-session-token'})
        self.assertEqual(403, response.status_code)

    @patch('student_planner.routes.repository.snapshot')
    def test_planner_is_scoped_to_signed_in_student(self, snapshot):
        self.login()
        snapshot.return_value = {'applications': [], 'tasks': []}
        response = self.client.get('/api/user/planner?user_email=someoneelse@example.com')
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.get_json()['csrf_token'])
        self.assertEqual([], response.get_json()['applications'])
        snapshot.assert_called_once_with('student@example.com')

    def test_admin_role_cannot_read_student_private_data(self):
        self.login()
        with self.client.session_transaction() as session:
            session['role'] = 'admin'
        self.assertEqual(401, self.client.get('/api/user/planner').status_code)

    def test_cross_origin_mutation_rejected_even_with_valid_token(self):
        self.login()
        headers = self.csrf_headers()
        for origin in ('https://attacker.example', 'https://localhost.attacker.example',
                       'https://localhost', 'null', 'https://['):
            with self.subTest(origin=origin):
                response = self.client.post('/api/user/planner/tasks', json={'title': 'Read'},
                                            headers={**headers, 'Origin': origin})
                self.assertEqual(403, response.status_code)

    def test_non_ascii_csrf_token_is_rejected_without_server_error(self):
        self.login()
        self.csrf_headers()
        response = self.client.post('/api/user/planner/tasks', json={'title': 'Read'},
                                    headers={'X-CSRF-Token': 'caf\u00e9'})
        self.assertEqual(403, response.status_code)

    def test_mutation_invalid_json_and_unknown_fields_rejected_without_storage_write(self):
        self.login()
        headers = self.csrf_headers()
        with patch('student_planner.routes.repository.create') as create:
            for data in ('{', 'null', '[]', '{}', '{"title":"Read","email":"other@example.com"}'):
                with self.subTest(data=data):
                    response = self.client.post('/api/user/planner/tasks', data=data,
                                                content_type='application/json', headers=headers)
                    self.assertEqual(400, response.status_code)
            create.assert_not_called()

    def test_create_for_both_collections_uses_only_session_owner(self):
        self.login()
        headers = {**self.csrf_headers(), 'Origin': 'http://localhost'}
        for collection, kind in (('applications', 'application'), ('tasks', 'task')):
            with self.subTest(collection=collection), patch('student_planner.routes.repository.create') as create:
                create.return_value = {'id': 9, 'title': 'Read'}
                response = self.client.post('/api/user/planner/' + collection + '?email=other@example.com',
                                            json={'title': 'Read'}, headers=headers)
                self.assertEqual(201, response.status_code)
                self.assertEqual(9, response.get_json()['item']['id'])
                create.assert_called_once_with('student@example.com', kind,
                                               validation.payload({'title': 'Read'}, kind))

    def test_patch_for_both_collections_uses_only_session_owner(self):
        self.login()
        headers = self.csrf_headers()
        for collection, kind in (('applications', 'application'), ('tasks', 'task')):
            with self.subTest(collection=collection), patch('student_planner.routes.repository.update') as update:
                update.return_value = {'id': 9, 'title': 'Edited'}
                response = self.client.patch('/api/user/planner/' + collection + '/9?email=other@example.com',
                                             json={'title': 'Edited'}, headers=headers)
                self.assertEqual(200, response.status_code)
                update.assert_called_once_with('student@example.com', kind, 9, {'title': 'Edited'})

    def test_delete_for_both_collections_uses_only_session_owner(self):
        self.login()
        headers = self.csrf_headers()
        for collection, kind in (('applications', 'application'), ('tasks', 'task')):
            with self.subTest(collection=collection), patch('student_planner.routes.repository.delete') as delete:
                response = self.client.delete('/api/user/planner/' + collection + '/9?email=other@example.com',
                                              headers=headers)
                self.assertEqual(200, response.status_code)
                delete.assert_called_once_with('student@example.com', kind, 9)

    def test_invalid_mutation_ids_rejected_without_database_call(self):
        self.login()
        headers = self.csrf_headers()
        with patch('student_planner.routes.repository.update', return_value={}) as update, \
                patch('student_planner.routes.repository.delete') as delete:
            for item_id in ('0', '2147483648', '999999999999999999999999999999'):
                for collection in ('applications', 'tasks'):
                    for method in ('PATCH', 'DELETE'):
                        with self.subTest(item_id=item_id, collection=collection, method=method):
                            response = self.client.open('/api/user/planner/' + collection + '/' + item_id,
                                                        method=method, json={'title': 'Read'}, headers=headers)
                            self.assertEqual(400, response.status_code)
            update.assert_not_called()
            delete.assert_not_called()

    def test_empty_or_owner_overriding_patch_never_reaches_database(self):
        self.login()
        headers = self.csrf_headers()
        with patch('student_planner.routes.repository.update') as update:
            for data in ({}, {'email': 'other@example.com'}, {'program_id': 7}, {'id': 9}, {'status': []}):
                with self.subTest(data=data):
                    response = self.client.patch('/api/user/planner/applications/1', json=data, headers=headers)
                    self.assertEqual(400, response.status_code)
            update.assert_not_called()

    def test_missing_or_other_users_item_returns_404(self):
        self.login()
        headers = self.csrf_headers()
        for method, function in (('PATCH', 'update'), ('DELETE', 'delete')):
            with self.subTest(method=method), patch('student_planner.routes.repository.' + function,
                                                   side_effect=LookupError('Item not found.')):
                response = self.client.open('/api/user/planner/tasks/99', method=method,
                                            json={'title': 'Changed'}, headers=headers)
                self.assertEqual(404, response.status_code)

    def test_storage_failure_is_503_and_does_not_leak_secrets_in_response_or_log(self):
        self.login()
        secret = 'postgresql://private:password@server/db student confidential notes'
        with patch('student_planner.routes.repository.snapshot', side_effect=OperationalError(secret)):
            with self.assertLogs(self.app.logger, level='ERROR') as log:
                response = self.client.get('/api/user/planner')
        self.assertEqual(503, response.status_code)
        self.assertNotIn(secret, response.get_data(as_text=True))
        self.assertNotIn(secret, ' '.join(log.output))
        self.assertIn('OperationalError', ' '.join(log.output))
        self.assertIn('no-store', response.headers['Cache-Control'])

    def test_failed_save_returns_503_never_a_success_confirmation(self):
        self.login()
        headers = self.csrf_headers()
        with patch('student_planner.routes.repository.create', side_effect=OperationalError('private details')):
            with self.assertLogs(self.app.logger, level='ERROR'):
                response = self.client.post('/api/user/planner/tasks', json={'title': 'Read'}, headers=headers)
        self.assertEqual(503, response.status_code)
        self.assertNotEqual('success', response.get_json().get('status'))
        self.assertNotIn('private details', response.get_data(as_text=True))

    def test_opportunity_filters_are_validated_before_read(self):
        self.login()
        with patch('student_planner.routes.repository.opportunities') as opportunities:
            for query in ('page=0', 'page=-1', 'page=1.5', 'page=100001', 'page=999999999', 'page=%C2%B2',
                          'page=NaN', 'within=8', 'sort=unsafe', 'q=' + 'x' * 101,
                          'company=' + 'x' * 201, 'category=' + 'x' * 101):
                with self.subTest(query=query):
                    self.assertEqual(400, self.client.get('/api/user/opportunities?' + query).status_code)
            opportunities.assert_not_called()

    @patch('student_planner.routes.repository.opportunities')
    def test_opportunity_filters_and_owner_pass_to_repository(self, opportunities):
        self.login()
        opportunities.return_value = {'items': [], 'total': 0}
        response = self.client.get('/api/user/opportunities?q= AI &company=Example&category=Course&within=7&sort=newest&page=2')
        self.assertEqual(200, response.status_code)
        opportunities.assert_called_once_with('student@example.com', 'AI', 'Example', 'Course', 7, 'newest', 2)
        self.assertIn('no-store', response.headers['Cache-Control'])

    @patch('student_planner.routes.repository.snapshot')
    def test_calendar_response_is_private_download_and_owner_scoped(self, snapshot):
        self.login()
        snapshot.return_value = {'applications': [], 'tasks': []}
        response = self.client.get('/api/user/planner/calendar.ics?email=other@example.com')
        self.assertEqual(200, response.status_code)
        snapshot.assert_called_once_with('student@example.com')
        self.assertEqual('text/calendar', response.mimetype)
        self.assertIn('attachment;', response.headers['Content-Disposition'])
        self.assertIn('no-store', response.headers['Cache-Control'])
        self.assertIn('BEGIN:VCALENDAR\r\n', response.get_data(as_text=True))


class PlannerValidationTests(unittest.TestCase):
    def test_application_defaults_and_trimmed_values(self):
        self.assertEqual({'title': 'Scholarship', 'company': '', 'notes': '', 'registration_url': '',
                          'deadline': None, 'status': 'saved', 'checklist': []},
                         validation.payload({'title': '  Scholarship  '}, 'application'))

    def test_task_defaults_and_partial_update_do_not_overwrite_other_fields(self):
        self.assertEqual({'title': 'Read', 'due_date': None, 'completed': False},
                         validation.payload({'title': 'Read'}, 'task'))
        self.assertEqual({'completed': True}, validation.payload({'completed': True}, 'task', partial=True))
        self.assertEqual({'deadline': None}, validation.payload({'deadline': ''}, 'application', partial=True))

    def test_titles_require_nonempty_text_with_200_character_limit(self):
        for value in (None, False, 3, [], {}, '', ' \n\t ', 'x' * 201, 'bad\x00title'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validation.payload({'title': value}, 'task')
        self.assertEqual('x' * 200, validation.payload({'title': 'x' * 200}, 'task')['title'])

    def test_company_notes_and_url_length_limits(self):
        for field, limit in (('company', 120), ('notes', 4000)):
            with self.subTest(field=field):
                self.assertEqual('x' * limit, validation.payload({field: 'x' * limit}, 'application', True)[field])
                with self.assertRaises(ValueError):
                    validation.payload({field: 'x' * (limit + 1)}, 'application', True)
        with self.assertRaises(ValueError):
            validation.safe_url('https://example.com/' + 'x' * 2000)

    def test_dates_are_strict_calendar_dates_with_bounds(self):
        for value in ('2026-2-01', '2026-02-30', '2026-01-01T10:00:00', '1999-12-31', '2101-01-01',
                      '2026-13-01', ' 2026-09-09', 20260909, True, [], '0000-01-01'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validation.date_value(value)
        for value in ('2000-01-01', '2100-12-31', '2028-02-29'):
            self.assertEqual(value, validation.date_value(value))
        self.assertIsNone(validation.date_value(None))
        self.assertIsNone(validation.date_value(''))

    def test_urls_reject_executable_credentials_whitespace_and_malformed_links(self):
        for value in ('javascript:alert(1)', 'data:text/html,test', '//example.com', '/local',
                      'https://user:pass@example.com', 'https://user@example.com', 'https://',
                      'https://example.com:bad', 'https://example.com:99999', 'https://[broken',
                      'https://example.com/a b', 'https://example.com/a\nb', 'https://example.com\\evil',
                      'https://example.com/a\x7fb'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validation.safe_url(value)
        for value in ('https://example.com/path?q=one#section', 'http://example.com:8080/path', ''):
            self.assertEqual(value, validation.safe_url(value))

    def test_statuses_completion_and_checklist_are_strict(self):
        for value in ('approved', True, 1, {}, [], None):
            with self.subTest(status=value), self.assertRaises(ValueError):
                validation.payload({'status': value}, 'application', True)
        for status in validation.STATUSES:
            self.assertEqual(status, validation.payload({'status': status}, 'application', True)['status'])
        for value in ('false', 0, 1, None, []):
            with self.subTest(completed=value), self.assertRaises(ValueError):
                validation.payload({'completed': value}, 'task', True)
        for value in ('cv', ['unknown'], [1], [True], {}, None, ['cv'] * 5):
            with self.subTest(checklist=value), self.assertRaises(ValueError):
                validation.payload({'checklist': value}, 'application', True)
        self.assertEqual(['cv', 'documents'], validation.payload(
            {'checklist': ['cv', 'cv', 'documents']}, 'application', True)['checklist'])

    def test_program_id_strict_positive_integer_and_exclusive_create_field(self):
        for value in (True, False, 0, -1, '1', 1.5, None, 2147483648):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validation.payload({'program_id': value}, 'application')
        self.assertEqual({'program_id': 12}, validation.payload({'program_id': 12}, 'application'))
        for data in ({'program_id': 1, 'notes': 'overwrite'}, {'email': 'other@example.com'}, {}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                validation.payload(data, 'application')
        with self.assertRaises(ValueError):
            validation.payload({'program_id': 1}, 'application', True)

    def test_json_nonobjects_and_unknown_fields_are_rejected(self):
        for kind in ('task', 'application'):
            for data in (None, [], 'text', 1, {}, {'title': 'Read', 'email': 'attacker@example.com'}):
                with self.subTest(kind=kind, data=data), self.assertRaises(ValueError):
                    validation.payload(data, kind)


class PlannerRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.connection_patch = patch('student_planner.repository.safe_connect', return_value=self.conn)
        self.connection_patch.start()
        self.addCleanup(self.connection_patch.stop)
        self.email = 'student@example.com'

    def test_transaction_commits_and_closes(self):
        with repository.transaction() as cursor:
            self.assertIs(self.cursor, cursor)
        self.conn.commit.assert_called_once_with()
        self.conn.rollback.assert_not_called()
        self.conn.close.assert_called_once_with()

    def test_transaction_rolls_back_and_closes_on_query_error(self):
        with self.assertRaises(OperationalError):
            with repository.transaction():
                raise OperationalError('offline simulated failure')
        self.conn.commit.assert_not_called()
        self.conn.rollback.assert_called_once_with()
        self.conn.close.assert_called_once_with()

    def test_transaction_rolls_back_and_closes_on_commit_error(self):
        self.conn.commit.side_effect = OperationalError('offline commit failure')
        with self.assertRaises(OperationalError):
            with repository.transaction():
                pass
        self.conn.rollback.assert_called_once_with()
        self.conn.close.assert_called_once_with()

    def test_snapshot_scopes_both_queries_and_serializes_dates(self):
        self.cursor.fetchall.side_effect = [[{'id': 1, 'deadline': date(2026, 9, 10)}],
                                            [{'id': 2, 'updated_at': datetime(2026, 9, 9, 12, 0)}]]
        result = repository.snapshot(self.email)
        for call in self.cursor.execute.call_args_list:
            self.assertIn('WHERE email=%s', call.args[0])
            self.assertEqual((self.email,), call.args[1])
            self.assertNotIn(self.email, call.args[0])
        self.assertEqual('2026-09-10', result['applications'][0]['deadline'])
        self.assertEqual('2026-09-09T12:00:00', result['tasks'][0]['updated_at'])

    def test_create_both_collections_locks_owner_counts_and_binds_input(self):
        for kind, table in (('task', 'student_study_tasks'), ('application', 'student_applications')):
            with self.subTest(kind=kind):
                self.cursor.reset_mock()
                title = "Robert'); DROP TABLE users;--"
                self.cursor.fetchone.side_effect = [{'email': self.email}, {'count': 0}, {'id': 7, 'title': title}]
                result = repository.create(self.email, kind, {'title': title})
                self.assertEqual(title, result['title'])
                calls = self.cursor.execute.call_args_list
                self.assertIn('FOR UPDATE', calls[0].args[0])
                self.assertEqual((self.email,), calls[0].args[1])
                self.assertIn('COUNT(*)', calls[1].args[0])
                self.assertEqual((self.email,), calls[1].args[1])
                self.assertIn('INSERT INTO ' + table, calls[2].args[0])
                self.assertEqual([self.email, title], calls[2].args[1])
                self.assertNotIn(title, calls[2].args[0])

    def test_create_rejects_inactive_owner_without_insert(self):
        self.cursor.fetchone.return_value = None
        with self.assertRaisesRegex(ValueError, 'not active'):
            repository.create(self.email, 'task', {'title': 'Read'})
        self.assertEqual(1, self.cursor.execute.call_count)
        self.conn.rollback.assert_called_once_with()

    def test_create_cap_is_enforced_for_both_collections(self):
        for kind in ('task', 'application'):
            with self.subTest(kind=kind):
                self.cursor.reset_mock()
                self.cursor.fetchone.side_effect = [{'email': self.email}, {'count': repository.LIMIT}]
                with self.assertRaisesRegex(ValueError, str(repository.LIMIT)):
                    repository.create(self.email, kind, {'title': 'Read'})
                self.assertFalse(any('INSERT' in call.args[0] for call in self.cursor.execute.call_args_list))

    def test_repeated_program_save_returns_existing_without_overwriting_notes_or_cap_check(self):
        existing = {'id': 5, 'program_id': 7, 'notes': 'My private preparation',
                    'status': 'preparing', 'checklist': ['cv']}
        self.cursor.fetchone.side_effect = [{'email': self.email}, existing]
        result = repository.create(self.email, 'application', {'program_id': 7})
        self.assertEqual(existing, result)
        self.assertEqual(2, self.cursor.execute.call_count)
        select = self.cursor.execute.call_args_list[1]
        self.assertIn('WHERE email=%s AND program_id=%s', select.args[0])
        self.assertEqual((self.email, 7), select.args[1])
        self.assertFalse(any('UPDATE' in call.args[0].split('FROM')[0] or 'INSERT' in call.args[0]
                             for call in self.cursor.execute.call_args_list))

    def test_program_create_requires_active_nonexpired_program_and_sanitizes_link(self):
        program = {'program_id': 7, 'title': 'x' * 210, 'company': 'y' * 130,
                   'registration_url': 'javascript:alert(1)', 'deadline': date(2026, 12, 1)}
        self.cursor.fetchone.side_effect = [{'email': self.email}, None, program, {'count': 0}, {'id': 5}]
        self.assertEqual({'id': 5}, repository.create(self.email, 'application', {'program_id': 7}))
        query = self.cursor.execute.call_args_list[2]
        self.assertIn('is_active=TRUE', query.args[0])
        self.assertIn('deadline >= CURRENT_DATE', query.args[0])
        self.assertEqual((7,), query.args[1])
        insert = self.cursor.execute.call_args_list[-1]
        self.assertEqual([self.email, 7, 'x' * 200, 'y' * 120, '', date(2026, 12, 1)], insert.args[1])

    def test_missing_program_is_not_inserted(self):
        self.cursor.fetchone.side_effect = [{'email': self.email}, None, None]
        with self.assertRaises(LookupError):
            repository.create(self.email, 'application', {'program_id': 7})
        self.assertFalse(any('INSERT' in call.args[0] for call in self.cursor.execute.call_args_list))

    def test_update_both_collections_owner_scoped_and_values_parameterized(self):
        for kind, table in (('task', 'student_study_tasks'), ('application', 'student_applications')):
            with self.subTest(kind=kind):
                self.cursor.reset_mock()
                self.cursor.fetchone.return_value = {'id': 8, 'title': 'Updated'}
                repository.update(self.email, kind, 8, {'title': 'Updated'})
                sql, params = self.cursor.execute.call_args.args
                self.assertIn('UPDATE ' + table, sql)
                self.assertIn('WHERE email=%s AND id=%s', sql)
                self.assertEqual(['Updated', self.email, 8], params)
                self.assertNotIn('Updated', sql)

    def test_checklist_is_stored_as_json_parameter(self):
        self.cursor.fetchone.return_value = {'id': 8}
        repository.update(self.email, 'application', 8, {'checklist': ['cv', 'documents']})
        self.assertEqual(['["cv", "documents"]', self.email, 8], self.cursor.execute.call_args.args[1])

    def test_delete_both_collections_owner_scoped(self):
        for kind, table in (('task', 'student_study_tasks'), ('application', 'student_applications')):
            with self.subTest(kind=kind):
                self.cursor.reset_mock()
                self.cursor.fetchone.return_value = {'id': 8}
                repository.delete(self.email, kind, 8)
                sql, params = self.cursor.execute.call_args.args
                self.assertIn('DELETE FROM ' + table, sql)
                self.assertIn('WHERE email=%s AND id=%s', sql)
                self.assertEqual((self.email, 8), params)

    def test_mutating_missing_or_other_users_items_rolls_back(self):
        self.cursor.fetchone.return_value = None
        for function, args in ((repository.update, (self.email, 'task', 8, {'title': 'Other'})),
                               (repository.delete, (self.email, 'application', 8))):
            with self.subTest(function=function.__name__), self.assertRaises(LookupError):
                function(*args)
        self.assertEqual(2, self.conn.rollback.call_count)
        self.assertEqual(2, self.conn.close.call_count)

    def test_opportunities_bound_filters_owner_join_pagination_and_unique_options(self):
        self.cursor.fetchone.return_value = {'count': 15}
        self.cursor.fetchall.side_effect = [[{'id': 7, 'deadline': date(2026, 9, 10), 'application_id': 2}],
                                            [{'company': 'B', 'category': 'Course'},
                                             {'company': 'A', 'category': 'Course'},
                                             {'company': None, 'category': ''}]]
        result = repository.opportunities(self.email, '100%_\\', 'Example', 'Course', 7, 'newest', 2)
        calls = self.cursor.execute.call_args_list
        pattern = '%100\\%\\_\\\\%'
        self.assertEqual([pattern] * 3 + ['Example', 'Course', 7], calls[0].args[1])
        self.assertIn('a.email=%s', calls[1].args[0])
        self.assertIn('p.created_at DESC, p.id DESC', calls[1].args[0])
        self.assertEqual([self.email] + [pattern] * 3 + ['Example', 'Course', 7, 12], calls[1].args[1])
        self.assertEqual(['A', 'B'], result['companies'])
        self.assertEqual(['Course'], result['categories'])
        self.assertEqual(15, result['total'])
        self.assertEqual(2, result['page'])
        self.assertEqual(12, result['page_size'])
        self.assertEqual('2026-09-10', result['items'][0]['deadline'])

    def test_schema_is_additive_and_protects_private_tables(self):
        self.cursor.fetchone.return_value = {'exists': 1}
        repository.ensure_schema(self.conn)
        statements = [call.args[0] for call in self.cursor.execute.call_args_list]
        self.assertFalse(any('DROP ' in statement or 'TRUNCATE ' in statement for statement in statements))
        for table in ('student_applications', 'student_study_tasks'):
            self.assertTrue(any('CREATE TABLE IF NOT EXISTS ' + table in sql for sql in statements))
            self.assertIn('ALTER TABLE ' + table + ' ENABLE ROW LEVEL SECURITY', statements)
            for role in ('PUBLIC', 'anon', 'authenticated'):
                self.assertIn('REVOKE ALL ON ' + table + ' FROM ' + role, statements)
        self.assertTrue(any('UNIQUE(email, program_id)' in sql for sql in statements))


class PlannerCalendarTests(unittest.TestCase):
    def test_fold_line_respects_utf8_75_octets_and_preserves_unicode(self):
        for original in ('SUMMARY:' + 'a' * 180, 'SUMMARY:' + '\u5b66\u751f\U0001f393' * 40, '', 'a' * 75):
            with self.subTest(original=original):
                folded = fold_line(original)
                lines = folded.split('\r\n')
                self.assertTrue(all(len(line.encode('utf-8')) <= 75 for line in lines))
                self.assertTrue(all(line.startswith(' ') for line in lines[1:]))
                self.assertEqual(original, folded.replace('\r\n ', ''))

    def test_escape_text_prevents_new_properties_and_escapes_punctuation(self):
        escaped = escape_text('A\\B;C,D\r\nBEGIN:VEVENT\rATTENDEE:evil\nEND:VEVENT')
        self.assertEqual('A\\\\B\\;C\\,D\\nBEGIN:VEVENT\\nATTENDEE:evil\\nEND:VEVENT', escaped)
        self.assertNotIn('\r', escaped)
        self.assertNotIn('\n', escaped)

    def test_calendar_only_contains_upcoming_actionable_deadlines_and_unfinished_tasks(self):
        applications = [{'id': index, 'title': status, 'deadline': '2026-09-09', 'status': status}
                        for index, status in enumerate(validation.STATUSES, 1)]
        applications.extend([{'id': 20, 'title': 'Past', 'deadline': '2026-09-08', 'status': 'saved'},
                             {'id': 21, 'title': 'No date', 'deadline': None, 'status': 'saved'}])
        tasks = [{'id': 1, 'title': 'Today', 'due_date': '2026-09-09', 'completed': False},
                 {'id': 2, 'title': 'Done', 'due_date': '2026-09-10', 'completed': True},
                 {'id': 3, 'title': 'Past task', 'due_date': '2026-09-08', 'completed': False},
                 {'id': 4, 'title': 'No date', 'due_date': None, 'completed': False},
                 {'id': 5, 'title': 'Future', 'due_date': '2026-12-31', 'completed': False}]
        calendar = build_calendar({'applications': applications, 'tasks': tasks}, today=date(2026, 9, 9))
        self.assertEqual(4, calendar.count('BEGIN:VEVENT\r\n'))
        for expected in ('application-1', 'application-2', 'task-1', 'task-5'):
            self.assertIn('UID:' + expected + '@novabrief.tech\r\n', calendar)
        for excluded in ('application-3', 'application-4', 'application-5', 'application-6', 'application-20',
                         'application-21', 'task-2', 'task-3', 'task-4'):
            self.assertNotIn('UID:' + excluded + '@novabrief.tech', calendar)
        self.assertIn('DTSTART;VALUE=DATE:20261231\r\nDTEND;VALUE=DATE:20270101', calendar)
        self.assertEqual(4, calendar.count('CLASS:PRIVATE'))

    def test_calendar_uids_stable_content_escaped_and_private_notes_excluded(self):
        data = {'applications': [{'id': 19, 'title': 'Scholarship\r\nATTENDEE:evil@example.com',
                                   'deadline': '2026-09-10', 'status': 'saved',
                                   'notes': 'Private financial details',
                                   'registration_url': 'https://example.com/?private=secret'}], 'tasks': []}
        first = build_calendar(data, today=date(2026, 9, 9))
        second = build_calendar(data, today=date(2026, 9, 9))
        for calendar in (first, second):
            self.assertIn('UID:application-19@novabrief.tech\r\n', calendar)
            self.assertNotIn('\r\nATTENDEE:', calendar)
            self.assertEqual(1, calendar.count('BEGIN:VEVENT\r\n'))
            self.assertNotIn('Private financial details', calendar)
            self.assertNotIn('private=secret', calendar)
            self.assertTrue(calendar.endswith('END:VCALENDAR\r\n'))
            self.assertTrue(all(len(line.encode('utf-8')) <= 75 for line in calendar.split('\r\n')))

    def test_empty_calendar_is_valid_snapshot_without_events(self):
        calendar = build_calendar({'applications': [], 'tasks': []}, today=date(2026, 9, 9))
        self.assertTrue(calendar.startswith('BEGIN:VCALENDAR\r\nVERSION:2.0\r\n'))
        self.assertNotIn('BEGIN:VEVENT', calendar)
        self.assertTrue(calendar.endswith('END:VCALENDAR\r\n'))


if __name__ == '__main__':
    unittest.main()
