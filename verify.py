import os

with open('web_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

verify_route = '''
@app.route('/googleae48116c49ed7429.html')
def google_verification():
    return 'google-site-verification: googleae48116c49ed7429.html'

'''

# Inject right after app = Flask(__name__)
content = content.replace("app = Flask(__name__)\n", "app = Flask(__name__)\n" + verify_route)

with open('web_server.py', 'w', encoding='utf-8') as f:
    f.write(content)
