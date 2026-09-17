"""Original exercises aligned to the ten CS50P lectures. Server-only answers/tests."""
from copy import deepcopy

VIDEO = 'https://www.youtube.com/watch?v=nLRL_NcnK-4'
_MODULES = [
 ('Functions & variables', 'Turn an idea into a small, precise Python program.', 'input, print, str, int, float, rounding, parameters, return, scope, comments'),
 ('Conditionals', 'Teach your program to make careful decisions.', 'if, elif, else, comparisons, bool, and, or, not, modulo, match'),
 ('Loops', 'Work with collections and repeat with purpose.', 'while, for, range, break, continue, lists, dictionaries, nesting'),
 ('Exceptions', 'Make programs that recover from unexpected input.', 'SyntaxError, ValueError, try, except, else, raise, EOFError'),
 ('Libraries', 'Build on reusable tools and structured data.', 'import, random, statistics, sys.argv, sys.exit, packages, pip, APIs, JSON, __name__'),
 ('Unit testing', 'Prove that your code works at the boundaries.', 'assert, pytest, raises, test discovery, packages, __init__.py, isolated functions'),
 ('File I/O', 'Read, transform, and save useful information.', 'open, with, read, write, append, sorting, CSV, DictReader, DictWriter, lambda, Pillow'),
 ('Regular expressions', 'Find structure in messy text.', 're.search, fullmatch, sub, groups, anchors, character classes, flags, walrus'),
 ('Object-oriented programming', 'Model a system with well-defined objects.', 'tuples, classes, __init__, __str__, properties, decorators, classmethod, staticmethod, inheritance, operator overloading'),
 ('Et cetera', 'Write expressive, reusable Python.', 'sets, globals, constants, type hints, docstrings, argparse, unpacking, args, kwargs, map, filter, comprehensions, enumerate, generators, iterators'),
]
MODULES = [dict(id=str(i), title=t, description=d, topics=topics.split(', '),
                notes=f'https://cs50.harvard.edu/python/notes/{i}/', video=VIDEO)
           for i, (t, d, topics) in enumerate(_MODULES)]
EXERCISES = {}


def add(id, module, title, difficulty, topics, problem, solution, cases, *, lesson='', hint='',
        starter='', mode='practice', files=None, project=False, argv=None):
    tests = []
    for index, case in enumerate(cases):
        stdin, output = case[:2]
        tests.append(dict(stdin=stdin, expected=output, files=case[2] if len(case)>2 else (files or {}),
                          argv=case[3] if len(case)>3 else (argv or []), hidden=index>0))
    EXERCISES[id] = dict(id=id, module=str(module), title=title, difficulty=difficulty, topics=topics.split(', '),
        problem=problem, lesson=lesson, hints=[hint or 'Break the problem into input, transformation, and output.',
        'Try the example first, then check an empty or boundary input.'], starter=starter or '# Read the input, solve the problem, and print the result.\n',
        solution=solution, explanation=lesson+'\n\n'+(hint or 'The reference solution separates reading, computation, and output; other correct approaches are accepted.'),
        tests=tests, examples=[dict(input=tests[0]['stdin'], output=tests[0]['expected'])],
        files=files or {}, argv=argv or [], mode=mode, project=project,
        io='Read standard input exactly as described. Print only the requested result (no input prompts). A final newline is optional.')


add('welcome',0,'A warmer welcome','Beginner','input, print, str, comments',
    'Read a name. Remove surrounding spaces and convert it to title case. Print Welcome, NAME!',
    'name = input().strip().title()\nprint(f"Welcome, {name}!")',
    [('  ada lovelace  \n','Welcome, Ada Lovelace!'),('ALI\n','Welcome, Ali!'),('\n','Welcome, !')],
    lesson='input() returns text. String methods return a new string; an f-string inserts values into text.',
    hint='Chain .strip().title() on the input string.',starter='name = input()\n# Clean up the name before greeting the learner.\nprint(f"Welcome, {name}!")\n')
add('receipt',0,'Split the receipt','Beginner','float, rounding, formatting',
    'Read a nonnegative bill amount, then a positive number of people. Print each person’s share to exactly two decimal places.',
    'bill = float(input())\npeople = int(input())\nprint(f"{bill / people:.2f}")',
    [('25\n4\n','6.25'),('0\n3\n','0.00'),('10\n3\n','3.33')],lesson='Convert numeric text before arithmetic. Formatting with :.2f keeps two decimal places.')
add('temperature',0,'Reusable conversions','Developing','def, parameters, return, scope',
    'Define to_celsius(fahrenheit) and use it to convert one input temperature. Print the result to one decimal place.',
    'def to_celsius(fahrenheit):\n    return (fahrenheit - 32) * 5 / 9\n\nprint(f"{to_celsius(float(input())):.1f}")',
    [('68\n','20.0'),('32\n','0.0'),('-40\n','-40.0')],lesson='A return value lets the caller decide how to display a result.',starter='def to_celsius(fahrenheit):\n    pass\n\nprint(f"{to_celsius(float(input())):.1f}")\n')
add('greeting-function',0,'Default delivery','Developing','default parameters, keyword arguments, print',
    'Read a name and a punctuation string on separate lines. Define greet(name="friend", end="!"). A blank name uses friend. Print Hello, NAME followed by the punctuation.',
    'def greet(name="friend", end="!"):\n    return f"Hello, {name}{end}"\nn = input()\np = input()\nprint(greet(n or "friend", end=p))',
    [('Ada\n!!!\n','Hello, Ada!!!'),('\n?\n','Hello, friend?'),('Lin\n.\n','Hello, Lin.')],lesson='Default parameters make arguments optional. Keyword arguments name the parameter being supplied.')
add('ticket',1,'Choose a ticket','Beginner','if, elif, else, comparisons',
    'Read an integer age. Print invalid for a negative age, child for ages 0–12, teen for 13–17, and adult for 18 or older.',
    'age = int(input())\nif age < 0: print("invalid")\nelif age < 13: print("child")\nelif age < 18: print("teen")\nelse: print("adult")',
    [('16\n','teen'),('-1\n','invalid'),('12\n','child'),('18\n','adult')],lesson='An if/elif chain chooses the first matching branch. Check boundaries carefully.')
add('leap',1,'Calendar logic','Developing','bool, and, or, modulo',
    'Read a positive year. Print leap if divisible by 400, or divisible by 4 but not 100; otherwise print common.',
    'y = int(input())\nprint("leap" if y % 400 == 0 or (y % 4 == 0 and y % 100 != 0) else "common")',
    [('2024\n','leap'),('1900\n','common'),('2000\n','leap'),('2023\n','common')],lesson='Parentheses make combinations of and/or easier to review. Modulo tests divisibility.')
add('command',1,'Command router','Developing','match, case, normalization',
    'Read a command, ignoring case and surrounding spaces. start or go produces running; stop or quit produces stopped; every other command produces unknown.',
    'match input().strip().lower():\n    case "start" | "go": print("running")\n    case "stop" | "quit": print("stopped")\n    case _: print("unknown")',
    [(' Go \n','running'),('QUIT\n','stopped'),('pause\n','unknown')],lesson='match selects a case; | joins alternatives and _ catches everything else.')
add('access',1,'Two keys to entry','Beginner','and, not, bool',
    'Read membership (yes/no), then blocked status (yes/no). Print allowed only for a member who is not blocked; otherwise print denied.',
    'member = input() == "yes"\nblocked = input() == "yes"\nprint("allowed" if member and not blocked else "denied")',
    [('yes\nno\n','allowed'),('yes\nyes\n','denied'),('no\nno\n','denied')],lesson='Boolean variables express a condition clearly and can be composed with and, or, and not.')
add('sum-until',2,'A running total','Beginner','while, break, int',
    'Read integers, one per line, until 0. Print the sum of all preceding values.',
    'total = 0\nwhile True:\n    n = int(input())\n    if n == 0: break\n    total += n\nprint(total)',
    [('3\n4\n0\n','7'),('0\n','0'),('-2\n5\n0\n','3')],lesson='A sentinel marks the end of input. Test the sentinel before adding it to the total.')
add('histogram',2,'Count the words','Developing','dict, for, get, sorted',
    'Read one line of space-separated words. Count words case-insensitively and print word:count lines in alphabetical order. Empty input prints nothing.',
    'counts = {}\nfor word in input().lower().split():\n    counts[word] = counts.get(word, 0) + 1\nfor word in sorted(counts):\n    print(f"{word}:{counts[word]}")',
    [('red Blue red\n','blue:1\nred:2'),('\n',''),('X x x\n','x:3')],lesson='A dictionary connects keys to values; get(key, default) handles a new word.',project=True)
add('grid',2,'Build a number grid','Developing','nested loops, range, list',
    'Read rows then columns (0–8). Print a multiplication grid: row r, column c contains r*c, starting from 1. Separate values with spaces. If either dimension is zero, print nothing.',
    'rows = int(input())\ncols = int(input())\nif cols:\n    for r in range(1, rows+1):\n        print(" ".join(str(r*c) for c in range(1, cols+1)))',
    [('2\n3\n','1 2 3\n2 4 6'),('0\n3\n',''),('3\n0\n',''),('1\n1\n','1')],lesson='The inner loop completes once for every step of the outer loop.')
add('positive',2,'Keep the useful values','Beginner','continue, lists, iteration',
    'Read a space-separated list of integers. Print only positive integers, in their original order, on one space-separated line.',
    'kept = []\nfor n in map(int, input().split()):\n    if n <= 0: continue\n    kept.append(str(n))\nprint(" ".join(kept))',
    [('1 -2 0 4\n','1 4'),('-1 0\n',''),('\n','')],lesson='continue skips the rest of the current iteration without ending the loop.')
add('retry',3,'Ask until it is an integer','Beginner','try, except, ValueError, else',
    'Read lines until an integer is found. Ignore invalid lines. Print twice the first valid integer. At least one valid integer is supplied.',
    'while True:\n    try: n = int(input())\n    except ValueError: continue\n    else:\n        print(n * 2)\n        break',
    [('oops\n3.5\n7\n','14'),('-2\n','-4'),('\nzero\n0\n','0')],lesson='Catch the specific error you expect. The else block runs only when the try block succeeds.')
add('ratio',3,'Divide safely','Developing','ZeroDivisionError, ValueError, exceptions',
    'Read numerator and denominator as text. Print their quotient to two decimals; invalid numeric input prints invalid; zero denominator prints undefined.',
    'a, b = input(), input()\ntry: print(f"{float(a)/float(b):.2f}")\nexcept ValueError: print("invalid")\nexcept ZeroDivisionError: print("undefined")',
    [('9\n2\n','4.50'),('3\n0\n','undefined'),('x\n2\n','invalid')],lesson='Different exceptions deserve different feedback. Avoid a bare except that hides unrelated failures.')
add('bounded',3,'Validate a percentage','Developing','raise, functions, validation',
    'Read an integer percentage. A function must reject values outside 0–100 with ValueError. Print valid for accepted input, invalid for rejected or noninteger input.',
    'def validate(n):\n    if not 0 <= n <= 100: raise ValueError("Out of range")\n    return n\ntry:\n    validate(int(input()))\n    print("valid")\nexcept ValueError: print("invalid")',
    [('100\n','valid'),('-1\n','invalid'),('101\n','invalid'),('a\n','invalid'),('0\n','valid')],lesson='raise makes a function’s contract explicit; callers choose how to recover.')
add('read-eof',3,'Read to the end','Developing','EOFError, while, exceptions',
    'Read all input lines until EOF. Print the number of nonempty lines (whitespace-only lines are empty).',
    'count = 0\nwhile True:\n    try: line = input()\n    except EOFError: break\n    if line.strip(): count += 1\nprint(count)',
    [('a\n\nb\n','2'),('','0'),('  \nx\n','1')],lesson='EOFError means input is exhausted. Handle it separately from invalid content.')
add('statistics',4,'A small data summary','Beginner','import, statistics, mean, median',
    'Read one nonempty line of integers. Use statistics to print mean then median, each to one decimal place, on separate lines.',
    'import statistics\nvalues = list(map(int, input().split()))\nprint(f"{statistics.mean(values):.1f}")\nprint(f"{statistics.median(values):.1f}")',
    [('1 2 9\n','4.0\n2.0'),('2 4\n','3.0\n3.0'),('-3\n','-3.0\n-3.0')],lesson='The standard library offers tested tools. Import modules before using their names.')
add('shuffle',4,'Reproducible randomness','Developing','random, seed, choice',
    'Read an integer seed. Create random.Random(seed) and print five calls to randint(1, 6), separated by spaces.',
    'import random\nrng = random.Random(int(input()))\nprint(*[rng.randint(1, 6) for _ in range(5)])',
    [('1\n','2 5 1 3 1'),('0\n','4 4 1 3 5'),('42\n','6 1 1 6 3')],lesson='A dedicated seeded generator makes simulations reproducible without changing unrelated random state.')
add('json-api',4,'Read an API response','Developing','json, APIs, dictionaries',
    'Read a JSON object with a results list. Print the name of each entry whose active field is true, sorted alphabetically. This is an offline API fixture; network requests are disabled.',
    'import json\ndata = json.loads(input())\nfor name in sorted(item["name"] for item in data["results"] if item.get("active", False)):\n    print(name)',
    [('{"results":[{"name":"Zoe","active":true},{"name":"Ali","active":false}]}\n','Zoe'),('{"results":[]}\n',''),('{"results":[{"name":"B","active":true},{"name":"A","active":true},{"name":"C"}]}\n','A\nB')],lesson='HTTP APIs often return JSON. Decode the response, inspect its shape, then extract values; offline fixtures make tests repeatable.')
add('cli',4,'Command-line greeter','Developing','sys.argv, sys.exit, __name__',
    'Read names from command-line arguments, not input(). Print Hello, NAME for each argument. With no names, print usage: greet NAME. Use a main guard.',
    'import sys\ndef main():\n    if len(sys.argv) == 1: print("usage: greet NAME")\n    for name in sys.argv[1:]: print(f"Hello, {name}")\nif __name__ == "__main__": main()',
    [('', 'Hello, Ada', {}, ['Ada']),('', 'usage: greet NAME', {}, []),('', 'Hello, Ali\nHello, Lin', {}, ['Ali','Lin'])],argv=['Ada'],lesson='sys.argv[0] is the script name. The main guard keeps an imported module from running its command-line workflow.')
add('assertions',5,'Turn cases into assertions','Beginner','assert, boundary testing, functions',
    'Read an integer. Define is_even(n) and assert that it handles 0, -2, and 3 correctly. Then print True or False for the input.',
    'def is_even(n): return n % 2 == 0\nassert is_even(0)\nassert is_even(-2)\nassert not is_even(3)\nprint(is_even(int(input())))',
    [('4\n','True'),('-3\n','False'),('0\n','True')],lesson='Assertions fail loudly when a condition is false. Include zero, negative inputs, and contrasting cases.')
add('test-isolation',5,'Separate logic from display','Developing','unit tests, return, pure functions',
    'Read a JSON list of [price, quantity] pairs. Define total(price, quantity) returning their product. Print a JSON list of totals without prompts or other output.',
    'import json\ndef total(price, quantity): return price * quantity\nprint(json.dumps([total(*pair) for pair in json.loads(input())]))',
    [('[ [3, 4], [0, 5] ]\n','[12, 0]'),('[[7,0],[-2,3]]\n','[0, -6]'),('[]\n','[]')],lesson='Returning results makes logic easy to call from tests. Keep input and printing at the program boundary.')
add('test-exceptions',5,'An exception test harness','Challenging','pytest.raises, exceptions, testing',
    'Read a JSON list of values. For each value, conversion to int either succeeds (print ok) or raises ValueError/TypeError (print rejected). Print one line per case. This models the success and failure cases you would separate into pytest tests.',
    'import json\nfor value in json.loads(input()):\n    try: int(value)\n    except (ValueError, TypeError): print("rejected")\n    else: print("ok")',
    [('["12", "x", null]\n','ok\nrejected\nrejected'),('[]\n',''),('["-3", "3.2", ""]\n','ok\nrejected\nrejected')],lesson='pytest.raises(ValueError) checks an expected exception; a successful case should be tested separately. Catch only the documented exception types.')
add('file-lines',6,'A tidy reading list','Beginner','open, with, read, sorting',
    'Read books.txt. Ignore blank lines and surrounding spaces; print remaining lines sorted alphabetically, keeping duplicates.',
    'with open("books.txt") as file:\n    books = [line.strip() for line in file if line.strip()]\nprint("\\n".join(sorted(books)))',
    [('', 'Dune\nThe Hobbit', {'books.txt':'The Hobbit\n\n Dune \n'}),('', '', {'books.txt':''}),('', 'A\nA\nB', {'books.txt':'B\nA\nA\n'})],files={'books.txt':'The Hobbit\n\n Dune \n'},lesson='with closes a file even when an error occurs. strip removes the newline and surrounding whitespace.')
add('file-write',6,'Save a journal entry','Developing','write, append, context managers',
    'Read one entry from input. Append it plus a newline to journal.txt, then read the whole file and print it without adding another newline.',
    'entry = input()\nwith open("journal.txt", "a") as file: file.write(entry + "\\n")\nwith open("journal.txt") as file: print(file.read(), end="")',
    [('Today I learned loops\n','Started learning\nToday I learned loops\n',{'journal.txt':'Started learning\n'}),('New\n','New\n',{'journal.txt':''}),('\n','A\n\n',{'journal.txt':'A\n'})],files={'journal.txt':'Started learning\n'},lesson='Mode a appends; w replaces existing contents. Exercise files are private, temporary text files inside the sandbox.')
add('csv',6,'A class gradebook','Challenging','csv, DictReader, lambda, sorting',
    'Read grades.csv with name,score columns. Print name:score, ordered by descending integer score and then ascending name. Preserve names containing commas.',
    'import csv\nwith open("grades.csv", newline="") as file: rows = list(csv.DictReader(file))\nfor row in sorted(rows, key=lambda r: (-int(r["score"]), r["name"])):\n    print(f"{row[\'name\']}:{row[\'score\']}")',
    [('', 'Ali:90\nZoe:75',{'grades.csv':'name,score\nZoe,75\nAli,90\n'}),('', 'A:80\nB:80',{'grades.csv':'name,score\nB,80\nA,80\n'}),('', 'Lee, Ada:99',{'grades.csv':'name,score\n"Lee, Ada",99\n'})],files={'grades.csv':'name,score\nZoe,75\nAli,90\n'},lesson='CSV is not just split(","): quoted fields can contain commas. A tuple sorting key combines descending score with ascending name.',project=True)
add('csv-write',6,'Export the roster','Developing','DictWriter, CSV, files',
    'Read a JSON list of objects with name and team. Write roster.csv using csv.DictWriter with that column order and a header, then print the file contents.',
    'import csv, json\nrows = json.loads(input())\nwith open("roster.csv", "w", newline="") as f:\n    w = csv.DictWriter(f, fieldnames=["name", "team"], lineterminator="\\n")\n    w.writeheader()\n    w.writerows(rows)\nwith open("roster.csv") as f: print(f.read(), end="")',
    [('[{"name":"Ada","team":"Blue"}]\n','name,team\nAda,Blue'),('[]\n','name,team'),('[{"name":"A, B","team":"Red"}]\n','name,team\n"A, B",Red')],lesson='DictWriter uses explicit field names and quotes data correctly. Set a consistent line terminator when exporting text.')
add('identifier',7,'Validate an identifier','Beginner','fullmatch, character classes, anchors',
    'Read a string. Print valid only if its first character is an ASCII letter or underscore and remaining characters are ASCII letters, digits, or underscores. Empty input is invalid.',
    'import re\nprint("valid" if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", input()) else "invalid")',
    [('user_12\n','valid'),('12user\n','invalid'),('\n','invalid'),('has space\n','invalid')],lesson='fullmatch validates the entire string; * permits zero or more of the preceding pattern.')
add('extract-date',7,'Extract a date','Developing','search, groups, walrus',
    'Find the first date formatted as exactly four digits, hyphen, two digits, hyphen, two digits in one input line. Print DD/MM/YYYY, or none if missing. Do not validate the calendar date.',
    'import re\nif m := re.search(r"(?<![0-9])([0-9]{4})-([0-9]{2})-([0-9]{2})(?![0-9])", input()):\n    print(f"{m[3]}/{m[2]}/{m[1]}")\nelse: print("none")',
    [('Due 2026-09-16.\n','16/09/2026'),('no date\n','none'),('12026-09-16\n','none')],lesson='Capturing groups retain matched parts. The walrus operator assigns a match while checking whether it exists.')
add('clean-space',7,'Normalize a messy note','Developing','sub, raw strings, whitespace',
    'Read one line. Replace every run of whitespace with one space and trim the ends.',
    'import re\nprint(re.sub(r"\\s+", " ", input()).strip())',
    [('  Learn\t Python   today \n','Learn Python today'),('\n',''),('a   b\n','a b')],lesson='re.sub replaces each match. A raw string keeps backslashes readable in regex patterns.')
add('email-domain',7,'Find a campus address','Challenging','IGNORECASE, escaping, groups',
    'Read a string. Accept only a full address consisting of ASCII letters, digits, dots, underscores or hyphens before @campus.edu, case-insensitively. Print the lowercase username or invalid.',
    'import re\nm = re.fullmatch(r"([A-Za-z0-9._-]+)@campus\\.edu", input(), re.IGNORECASE)\nprint(m[1].lower() if m else "invalid")',
    [('Ada@CAMPUS.EDU\n','ada'),('a@campusXedu\n','invalid'),('@campus.edu\n','invalid'),('x@y@campus.edu\n','invalid')],lesson='Escape a literal dot as \\. and avoid broad .* patterns when validating a known format.')
add('wallet',8,'Model a wallet','Developing','class, __init__, methods, property',
    'Read a JSON list of integer changes to a wallet starting at 0. A change that would make the balance negative is rejected. Print the final balance. Use a Wallet class with a read-only balance property.',
    'import json\nclass Wallet:\n    def __init__(self): self._balance = 0\n    @property\n    def balance(self): return self._balance\n    def change(self, amount):\n        if self._balance + amount >= 0: self._balance += amount\nw = Wallet()\nfor n in json.loads(input()): w.change(n)\nprint(w.balance)',
    [('[10,-3,-20,4]\n','11'),('[]\n','0'),('[-1,2,-2]\n','0')],lesson='Objects keep state and behavior together. A property can expose a value without allowing direct assignment.',project=True)
add('student-class',8,'Construct from a record','Developing','classmethod, staticmethod, __str__',
    'Read name,score on one line. Use Student.from_record to construct an instance. Accept scores 0–100; print NAME (SCORE) or invalid. Strip the name.',
    'class Student:\n    def __init__(self, name, score): self.name, self.score = name, score\n    @staticmethod\n    def valid(score): return 0 <= score <= 100\n    @classmethod\n    def from_record(cls, record):\n        name, score = record.rsplit(",", 1)\n        score = int(score)\n        if not cls.valid(score): raise ValueError()\n        return cls(name.strip(), score)\n    def __str__(self): return f"{self.name} ({self.score})"\ntry: print(Student.from_record(input()))\nexcept ValueError: print("invalid")',
    [(' Ada ,95\n','Ada (95)'),('Ali,101\n','invalid'),('Lin,0\n','Lin (0)'),('bad\n','invalid')],lesson='classmethod receives the class; staticmethod receives neither class nor instance. __str__ controls readable object output.')
add('inheritance',8,'Extend a delivery service','Challenging','inheritance, super, overriding',
    'Read base or express, then an integer distance. Base delivery costs 5 + 2*distance; express adds 10. Define Delivery and ExpressDelivery classes and print the cost.',
    'class Delivery:\n    def __init__(self, distance): self.distance = distance\n    def cost(self): return 5 + 2*self.distance\nclass ExpressDelivery(Delivery):\n    def cost(self): return super().cost() + 10\nkind = input()\ndistance = int(input())\nprint((ExpressDelivery if kind == "express" else Delivery)(distance).cost())',
    [('express\n3\n','21'),('base\n0\n','5'),('express\n0\n','15')],lesson='Inheritance reuses shared behavior. super() calls the parent implementation without hard-coding its name.')
add('vectors',8,'Add two vectors','Challenging','__add__, operator overloading, tuples',
    'Read x y for two integer vectors on separate lines. Define Vector.__add__ and print the coordinates of the sum separated by a space.',
    'class Vector:\n    def __init__(self, x, y): self.x, self.y = x, y\n    def __add__(self, other): return Vector(self.x+other.x, self.y+other.y)\na = Vector(*map(int,input().split()))\nb = Vector(*map(int,input().split()))\nc = a + b\nprint(c.x, c.y)',
    [('1 2\n3 4\n','4 6'),('-1 0\n1 0\n','0 0'),('0 0\n0 0\n','0 0')],lesson='__add__ lets + return a new object. Avoid changing either operand unexpectedly.')
add('sets',9,'A unique guest list','Beginner','set, sorted, comprehensions',
    'Read space-separated names. Print the unique lowercase names in alphabetical order, separated by spaces.',
    'print(" ".join(sorted({name.lower() for name in input().split()})))',
    [('Ali ADA ali\n','ada ali'),('\n',''),('X X\n','x')],lesson='A set removes duplicates. Sort it when output order matters.')
add('comprehensions',9,'Transform a dataset','Developing','map, filter, list comprehension, enumerate',
    'Read space-separated integers. Keep even values, square them, and print index:value with indices starting at 1, one per line.',
    'values = map(int, input().split())\nsquares = [n*n for n in values if n % 2 == 0]\nfor index, value in enumerate(squares, start=1): print(f"{index}:{value}")',
    [('1 2 -4 3\n','1:4\n2:16'),('1 3\n',''),('0 2\n','1:0\n2:4')],lesson='Comprehensions combine transformation and filtering. enumerate pairs each value with an index.')
add('kwargs',9,'Flexible invoice','Challenging','args, kwargs, unpacking, dict comprehension',
    'Read a JSON object containing prices (a list of integers) and discount (an integer, default 0). Define invoice(*prices, discount=0) and print max(0, sum(prices)-discount).',
    'import json\ndef invoice(*prices, discount=0): return max(0, sum(prices)-discount)\ndata = json.loads(input())\noptions = {k:v for k,v in data.items() if k == "discount"}\nprint(invoice(*data["prices"], **options))',
    [('{"prices":[10,20],"discount":5}\n','25'),('{"prices":[]}\n','0'),('{"prices":[3],"discount":9}\n','0')],lesson='* collects or unpacks positional arguments; ** handles keyword arguments. Keyword-only parameters make configuration explicit.')
add('generators',9,'Generate a countdown','Developing','yield, generators, iterators',
    'Read an integer n (0–100). Define countdown(n) yielding n through 1. Print values separated by spaces. For 0, print an empty line.',
    'def countdown(n):\n    while n > 0:\n        yield n\n        n -= 1\nprint(*countdown(int(input())))',
    [('4\n','4 3 2 1'),('0\n',''),('1\n','1')],lesson='yield pauses a generator and preserves its state. Values are produced as the caller requests them.')
add('argparse',9,'A configurable repeater','Challenging','argparse, type hints, docstrings',
    'Use argparse to read --count (integer, default 1) and a positional word. Print the word count times separated by spaces. Count is nonnegative. No standard input is supplied.',
    'import argparse\ndef repeat(word: str, count: int) -> str:\n    """Return a space-separated repetition."""\n    return " ".join([word]*count)\np = argparse.ArgumentParser()\np.add_argument("--count", type=int, default=1)\np.add_argument("word")\na = p.parse_args()\nprint(repeat(a.word, a.count))',
    [('', 'hi hi hi', {}, ['--count','3','hi']),('', 'yes', {}, ['yes']),('', '', {}, ['--count','0','x'])],argv=['--count','3','hi'],lesson='argparse handles named options and conversion. Type hints document intent; they do not enforce types at runtime.')
add('global-counter',9,'Understand shared state','Developing','global, constants, scope',
    'Read a nonnegative integer n. Set STEP = 3 and counter = 0 at module scope. Define increment() to update the global counter by STEP. Call it n times and print counter.',
    'STEP = 3\ncounter = 0\ndef increment():\n    global counter\n    counter += STEP\nfor _ in range(int(input())): increment()\nprint(counter)',
    [('4\n','12'),('0\n','0'),('1\n','3')],lesson='global allows reassignment of a module variable. Uppercase constants are a convention, not an enforced restriction.')
add('study-report',9,'Project: study session report','Challenging','JSON, validation, comprehensions, sorting, functions',
    'Read a JSON list of sessions with topic and minutes. Ignore sessions with minutes <= 0. Sum minutes by topic and print topic:minutes lines alphabetically. Topic matching is case-sensitive.',
    'import json\ndef report(sessions):\n    totals = {}\n    for session in sessions:\n        if session["minutes"] > 0:\n            t = session["topic"]\n            totals[t] = totals.get(t, 0) + session["minutes"]\n    return totals\nfor topic, minutes in sorted(report(json.loads(input())).items()): print(f"{topic}:{minutes}")',
    [('[{"topic":"Loops","minutes":20},{"topic":"Loops","minutes":10},{"topic":"Files","minutes":5}]\n','Files:5\nLoops:30'),('[]\n',''),('[{"topic":"A","minutes":0},{"topic":"B","minutes":-2},{"topic":"A","minutes":1}]\n','A:1')],lesson='Combine parsing, validation, aggregation, and presentation. Keep the calculation in a function that can be unit tested.',project=True)

add('unittest-suite',5,'Write a regression suite','Challenging','unittest, assertions, regression tests',
    'Read correct or buggy. Build a unittest.TestCase for square(n), testing positive, negative and zero inputs. The correct implementation returns n*n; buggy returns n*2. Run the suite in memory and print passed if all tests pass, otherwise caught. Keep the test runner output out of stdout.',
    'import unittest, io\nmode = input()\ndef square(n): return n*n if mode == "correct" else n*2\nclass SquareTests(unittest.TestCase):\n    def test_positive(self): self.assertEqual(square(3), 9)\n    def test_negative(self): self.assertEqual(square(-2), 4)\n    def test_zero(self): self.assertEqual(square(0), 0)\nsuite = unittest.defaultTestLoader.loadTestsFromTestCase(SquareTests)\nresult = unittest.TextTestRunner(stream=io.StringIO()).run(suite)\nprint("passed" if result.wasSuccessful() else "caught")',
    [('correct\n','passed'),('buggy\n','caught')],lesson='A regression suite protects intended behavior. Tests should accept the correct implementation and reject a deliberately broken variant.',
    starter='import unittest, io\nmode = input()\ndef square(n):\n    return n*n if mode == "correct" else n*2\n\nclass SquareTests(unittest.TestCase):\n    def test_positive(self):\n        pass\n    # Add negative and zero cases.\n\nsuite = unittest.defaultTestLoader.loadTestsFromTestCase(SquareTests)\nresult = unittest.TextTestRunner(stream=io.StringIO()).run(suite)\nprint("passed" if result.wasSuccessful() else "caught")\n')
add('pytest-raises',5,'Practice pytest.raises','Developing','pytest, raises, error handling',
    'Read an integer. Define require_positive(n) that raises ValueError if n <= 0 and returns n otherwise. For nonpositive input, use pytest.raises(ValueError) to check the exception and print rejected. Otherwise print the returned number.',
    'import pytest\ndef require_positive(n):\n    if n <= 0: raise ValueError("must be positive")\n    return n\nn = int(input())\nif n <= 0:\n    with pytest.raises(ValueError): require_positive(n)\n    print("rejected")\nelse: print(require_positive(n))',
    [('0\n','rejected'),('-4\n','rejected'),('5\n','5')],lesson='pytest is installed in this sandbox. Its raises context manager checks the exception type and fails if no expected exception occurs. Tests should also include the successful path.')
add('property-setter',8,'Protect an object’s state','Challenging','property, setter, validation',
    'Read a JSON list of integer percentages. Create Progress starting at 0 with a percent property and setter. Reject assignments outside 0–100 by raising ValueError and keep the previous value. After every attempted assignment, print the current percent.',
    'import json\nclass Progress:\n    def __init__(self): self._percent = 0\n    @property\n    def percent(self): return self._percent\n    @percent.setter\n    def percent(self, value):\n        if not 0 <= value <= 100: raise ValueError()\n        self._percent = value\np = Progress()\nfor n in json.loads(input()):\n    try: p.percent = n\n    except ValueError: pass\n    print(p.percent)',
    [('[20,101,50]\n','20\n20\n50'),('[-1,0,100]\n','0\n0\n100'),('[]\n','')],lesson='A setter validates before changing state. Raise an error before assignment so the object remains valid.')
add('map-filter',9,'Build a lazy pipeline','Developing','map, filter, lambda, iterators',
    'Read space-separated integers. Use a pipeline that filters values greater than 10 and then halves them. Print the results with one decimal place in their original order.',
    'numbers = map(int, input().split())\nlarge = filter(lambda n: n > 10, numbers)\nprint(" ".join(f"{n:.1f}" for n in map(lambda n:n/2, large)))',
    [('4 11 20\n','5.5 10.0'),('10\n',''),('\n','')],lesson='map transforms values and filter keeps matching values. Both return lazy iterators; consumption happens when you loop or materialize them.')
add('unpacking',9,'Split a record with unpacking','Developing','tuple, unpacking, starred targets',
    'Read a comma-separated record containing a name and at least one integer score. Unpack the name and scores. Print NAME:MAX where MAX is the largest score. Strip surrounding spaces from the name.',
    'name, *scores = input().split(",")\nprint(f"{name.strip()}:{max(map(int, scores))}")',
    [('Ada,4,7,3\n','Ada:7'),(' Ali ,0\n','Ali:0'),('Lin,-4,-2\n','Lin:-2')],lesson='A starred target collects the remaining values into a list. Tuple unpacking also works with function return values.')

EXERCISES['test-isolation']['comparison'] = 'json'

# Original debugging, missing-code, and logic puzzles, one per lecture.
_PUZZLES = [
 ('p-string',0,'Debug: text is not a number','Read one integer and print that integer plus 1.','n = input()\nprint(n + 1)\n','n = int(input())\nprint(n + 1)', [('4\n','5'),('-1\n','0')],'Convert the input before performing arithmetic.','Debugging'),
 ('p-branch',1,'Debug: boundary birthday','Read an age. Print adult for age 18 or above, otherwise minor.','age = int(input())\nprint("adult" if age > 18 else "minor")\n','age = int(input())\nprint("adult" if age >= 18 else "minor")',[('18\n','adult'),('17\n','minor')],'The boundary belongs in the adult branch.','Logic'),
 ('p-range',2,'Fill: the missing endpoint','Read n >= 0 and print the sum 1 through n inclusive.','n = int(input())\nprint(sum(range(1, ___)))\n','n = int(input())\nprint(sum(range(1, n+1)))',[('4\n','10'),('0\n','0'),('1\n','1')],'range excludes its stop value.','Missing code'),
 ('p-except',3,'Debug: the wrong exception','Read text. Print its integer value or invalid if it is not an integer.','try:\n    print(int(input()))\nexcept TypeError:\n    print("invalid")\n','try:\n    print(int(input()))\nexcept ValueError:\n    print("invalid")',[('oops\n','invalid'),('12\n','12')],'int on nonnumeric text raises ValueError.','Debugging'),
 ('p-json',4,'Fill: decode the response','Read a JSON object and print its title.','import json\ndata = json.___(input())\nprint(data["title"])\n','import json\nprint(json.loads(input())["title"])',[('{"title":"Hello"}\n','Hello'),('{"title":""}\n','')],'loads decodes a string; load reads an open file.','Missing code'),
 ('p-test',5,'Debug: truthiness is not equality','Read two integers. Print pass only when they are equal.','a, b = int(input()), int(input())\nprint("pass" if a and b else "fail")\n','a, b = int(input()), int(input())\nprint("pass" if a == b else "fail")',[('2\n3\n','fail'),('0\n0\n','pass')],'Two truthy values do not have to be equal.','Logic'),
 ('p-file',6,'Debug: preserve a journal','Append the input plus a newline to journal.txt, then print all contents.','with open("journal.txt", "w") as f: f.write(input() + "\\n")\nwith open("journal.txt") as f: print(f.read(), end="")\n','with open("journal.txt", "a") as f: f.write(input() + "\\n")\nwith open("journal.txt") as f: print(f.read(), end="")',[('new\n','old\nnew',{'journal.txt':'old\n'}),('x\n','x',{'journal.txt':''})],'The append mode preserves existing content.','Debugging'),
 ('p-regex',7,'Debug: a dot too far','Print True only if the entire input is exactly a.b.','import re\nprint(bool(re.fullmatch(r"a.b", input())))\n','import re\nprint(bool(re.fullmatch(r"a\\.b", input())))',[('axb\n','False'),('a.b\n','True')],'An unescaped dot matches almost any character.','Debugging'),
 ('p-object',8,'Debug: shared backpacks','Read a word. Add it to the first Bag only; print the length of the second Bag’s items.','class Bag:\n    items = []\na, b = Bag(), Bag()\na.items.append(input())\nprint(len(b.items))\n','class Bag:\n    def __init__(self): self.items = []\na, b = Bag(), Bag()\na.items.append(input())\nprint(len(b.items))',[('book\n','0'),('pen\n','0')],'Mutable class attributes are shared; initialize items on each instance.','Debugging'),
 ('p-generator',9,'Fill: lazy squares','Read n >= 0. Yield and print the squares of 0 through n-1 separated by spaces.','def squares(n):\n    for i in range(n):\n        ___ i*i\nprint(*squares(int(input())))\n','def squares(n):\n    for i in range(n): yield i*i\nprint(*squares(int(input())))',[('4\n','0 1 4 9'),('0\n','')],'yield produces one value at a time without ending the function.','Missing code'),
]
for id, m, title, problem, starter, solution, cases, hint, kind in _PUZZLES:
    add(id,m,title,'Developing',kind,problem,solution,cases,starter=starter,mode='puzzle',hint=hint,
        lesson=hint,files=cases[0][2] if len(cases[0])>2 else {})

QUIZZES = {}
def quiz(module, kind, question, options, answer, explanation):
    id = f'q-{module}-{sum(q["module"]==str(module) for q in QUIZZES.values())+1}'
    QUIZZES[id] = dict(id=id,module=str(module),kind=kind,question=question,options=options,answer=answer,explanation=explanation)

quiz(0,'Output prediction','What does print("  python ".strip().title()) display?', ['python','Python','  Python ','PYTHON'],1,'strip removes outer whitespace and title capitalizes the first letter.')
quiz(0,'Error identification','Which expression raises TypeError?', ['int("3") + 1','"3" + "1"','"3" + 1','float("3") + 1'],2,'Text and an integer cannot be added directly; convert one operand.')
quiz(0,'Multiple choice','What does a function with no explicit return return?', ['0','None','False','An empty string'],1,'Reaching the end of a function implicitly returns None.')
quiz(1,'Output prediction','What is the value of 7 % 2 == 1 and not False?', ['True','False','1','None'],0,'7 % 2 is 1, the comparison is True, and not False is True.')
quiz(1,'Error identification','A range is 10 through 20 inclusive. Which check is correct?', ['10 < x < 20','10 <= x <= 20','x >= 10 or x <= 20','x == 10 and x == 20'],1,'Both endpoints are included, so use <= on both sides.')
quiz(1,'Multiple choice','Which match case is a catch-all?', ['case else:','case *:','case _:','case any:'],2,'The wildcard pattern _ matches any value without binding a name.')
quiz(2,'Output prediction','What does list(range(2, 7, 2)) contain?', ['[2, 4, 6]','[2, 4, 6, 7]','[2, 3, 4, 5, 6]','[0, 2, 4, 6]'],0,'range starts at 2, steps by 2, and excludes 7.')
quiz(2,'Multiple choice','What does continue do inside a loop?', ['Ends the whole program','Ends the loop','Skips to the next iteration','Restarts the function'],2,'continue skips the rest of this iteration; break ends the loop.')
quiz(2,'Output prediction','What does {"a": 2}.get("b", 0) return?', ['None','0','2','KeyError'],1,'get returns the default when the key is missing.')
quiz(3,'Error identification','int("three") raises which exception?', ['TypeError','KeyError','ValueError','EOFError'],2,'The type is acceptable but the string has no valid integer representation.')
quiz(3,'Multiple choice','When does a try/except/else else block run?', ['Always','Only if try completes without an exception','Only after an exception','Before try'],1,'else separates success handling from exception handling.')
quiz(3,'Multiple choice','How should a function report an invalid argument?', ['Ignore it','raise ValueError with context','Always exit the process','Catch every exception silently'],1,'An explicit exception lets a caller handle failure appropriately.')
quiz(4,'Multiple choice','How do you decode a JSON string?', ['json.dumps(text)','json.loads(text)','json.load(text)','str.json(text)'],1,'loads reads JSON from a string; dumps serializes a Python value.')
quiz(4,'Multiple choice','What is sys.argv[0] normally?', ['First user argument','Number of arguments','Script name','Python version'],2,'User-supplied arguments begin at index 1.')
quiz(4,'Multiple choice','What is pip used for?', ['Running a loop','Installing Python packages','Formatting strings','Defining a class'],1,'pip installs distributions. Production dependencies should be reviewed and pinned; this sandbox does not allow arbitrary installs.')
quiz(5,'Multiple choice','Which pytest test name is discovered by default?', ['check_sum','sum_testcase','test_sum','verify_sum'],2,'pytest normally discovers test_ functions in test_*.py or *_test.py files.')
quiz(5,'Error identification','Which assertion checks that square(3) equals 9?', ['assert square(3)','assert square(3) == 9','assert square == 9','assert 3 == 9'],1,'A truthiness check accepts any nonzero result; equality tests the actual expected value.')
quiz(5,'Multiple choice','How does pytest check an expected ValueError?', ['with pytest.raises(ValueError):','except pytest:','assert ValueError','pytest.ignore(ValueError)'],0,'The context manager fails the test if the expected exception is not raised. __init__.py marks a conventional importable package.')
quiz(6,'Multiple choice','Which file mode preserves contents and writes at the end?', ['r','w','a','x'],2,'a appends, w truncates, r reads, and x creates a new file exclusively.')
quiz(6,'Error identification','Why is line.split(",") unreliable for CSV?', ['It cannot split strings','Quoted fields may contain commas','CSV never has commas','It sorts rows'],1,'csv.reader and DictReader respect quoting and escaped delimiters.')
quiz(6,'Multiple choice','Which Pillow pattern opens an image safely?', ['with Image.open(path) as image:','Image.read_csv(path)','open(path).resize()','Pillow(path).sort()'],0,'Pillow provides Image.open, transformations, and save. ImageSequence.Iterator visits animation frames. Binary image processing is not available in this text-file sandbox.')
quiz(7,'Output prediction','Does re.fullmatch(r"a.b", "a-b") match?', ['Yes','No','Only with IGNORECASE','Raises SyntaxError'],0,'A dot matches any single character except newline by default. Use \\. for a literal dot.')
quiz(7,'Multiple choice','What does a capturing group provide?', ['A loop','Access to the matched substring','A file','Automatic input validation'],1,'Parentheses capture substrings retrievable with group() or match indexing.')
quiz(7,'Error identification','Which validates one or more ASCII digits across the entire string?', ['re.search(r"[0-9]", s)','re.fullmatch(r"[0-9]+", s)','re.fullmatch(r"[0-9]*", s)','re.search(r".*", s)'],1,'fullmatch covers the entire string; + requires at least one character, whereas * allows empty text.')
quiz(8,'Multiple choice','What is self in an instance method?', ['The class name','The current instance','A global variable','A reserved constant'],1,'self is the conventional name for the instance passed to a method.')
quiz(8,'Error identification','Where should a separate mutable list for each instance be created?', ['In __init__ as self.items = []','As a shared class attribute','Only at module scope','In __str__ every time'],0,'Instance initialization avoids unintentionally sharing one list among objects.')
quiz(8,'Multiple choice','Which decorator supplies the class as the first argument?', ['@property','@staticmethod','@classmethod','@instance'],2,'classmethod receives cls; staticmethod receives no implicit argument. Properties use decorators to expose controlled access.')
quiz(9,'Output prediction','What does list(map(str, [1, 2])) return?', ['[1, 2]','["1", "2"]','"12"','A set'],1,'map lazily transforms each item; list materializes the results.')
quiz(9,'Multiple choice','What does yield do?', ['Ends the program','Pauses a generator and produces a value','Enforces a type hint','Creates a constant'],1,'The generator resumes after yield on the next request. next(iterator) raises StopIteration when exhausted.')
quiz(9,'Error identification','Do Python type hints enforce argument types at runtime?', ['Always','Only for str','No; separate checking tools can analyze them','Only in a class'],2,'Type hints document intent and support static analysis. They do not replace runtime validation.')


def public_exercise(item):
    return {k: deepcopy(v) for k,v in item.items() if k not in {'tests','solution','explanation'}}

def public_quiz(item):
    return {k: deepcopy(v) for k,v in item.items() if k not in {'answer','explanation'}}

def catalog():
    return dict(modules=MODULES, exercises=[public_exercise(e) for e in EXERCISES.values()],
                quizzes=[public_quiz(q) for q in QUIZZES.values()], version=1)
