import os
import re

def clean_python_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Strip non-ASCII from python files, since python 3 allows utf-8 but we don't really need it here
    # except maybe if there are strings with emojis. Let's just strip the specific mojibake we saw:
    # AAA,A?A?sAAAA,A?A?sA
    new_content = re.sub(r'[ÃÂâ€šA,\?s]+', ' ', content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Cleaned {filepath}")

clean_python_file('web_server.py')
clean_python_file('database.py')
