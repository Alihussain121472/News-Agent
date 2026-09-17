import threading
import unittest

from python_practice.content import EXERCISES, QUIZZES, catalog
from python_practice.runtime import execute, OUTPUT_LIMIT
from python_practice.service import grade, normalized


class RuntimeTests(unittest.TestCase):
    def test_input_and_virtual_files(self):
        result=execute('name = input()\nwith open("a.txt", "w") as f: f.write(name)\nwith open("a.txt") as f: print(f.read())','Ada\n')
        self.assertEqual('ok',result['status'],result)
        self.assertEqual('Ada',normalized(result['stdout']))

    def test_errors_and_timeout(self):
        self.assertEqual('syntax_error',execute('if broken')['status'])
        self.assertEqual('runtime_error',execute('print(1 / 0)')['status'])
        self.assertEqual('timeout',execute('while True: pass')['status'])

    def test_memory_and_output_limits(self):
        result=execute('x = bytearray(200 * 1024 * 1024)')
        self.assertEqual('memory_limit',result['status'],result)
        result=execute('while True: print("x" * 1000)')
        self.assertEqual('output_limit',result['status'],result)
        self.assertLessEqual(len(result['stdout'].encode())+len(result['stderr'].encode()),OUTPUT_LIMIT)

    def test_stop(self):
        cancel=threading.Event()
        timer=threading.Timer(.3,cancel.set)
        timer.start()
        result=execute('while True: pass',cancel=cancel)
        timer.join()
        self.assertEqual('stopped',result['status'],result)

    def test_host_capabilities_not_available(self):
        for code in ['import os\nprint(os.environ["SECRET_KEY"])',
                     'import os\nos.open("/tmp/escape.txt", os.O_CREAT | os.O_WRONLY)',
                     'import socket\nsocket.socket().connect(("example.com", 80))']:
            with self.subTest(code=code):
                self.assertEqual('runtime_error',execute(code)['status'])

    def test_all_reference_solutions_in_actual_sandbox(self):
        for exercise in EXERCISES.values():
            with self.subTest(exercise=exercise['id']):
                result=grade(exercise,exercise['solution'],threading.Event())
                self.assertEqual('passed',result['status'],result)

    def test_bad_solution_is_rejected_and_hidden_values_are_private(self):
        result=grade(EXERCISES['welcome'],'print(input())',threading.Event())
        self.assertEqual('needs_work',result['status'])
        for test in result['tests'][1:]:
            self.assertEqual({'name','passed','status'},set(test))

    def test_catalog_contains_no_answers_or_hidden_tests(self):
        published=catalog()
        self.assertEqual(10,len(published['modules']))
        for item in published['exercises']:
            self.assertTrue({'solution','tests','explanation'}.isdisjoint(item))
        for question in published['quizzes']:
            self.assertTrue({'answer','explanation'}.isdisjoint(question))
        for question in QUIZZES.values():
            self.assertIn(question['answer'],range(len(question['options'])))
            self.assertTrue(question['explanation'])


if __name__=='__main__':
    unittest.main()
