import re
with open('web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace index() route
old_index = '''def index():
    user_email = session.get('user_email')
    user_name = session.get('user_name')
    is_user = session.get('role') == 'user'
    return render_template('index.html', user_email=user_email, user_name=user_name, is_logged_in=is_user, is_admin=(session.get('role') == 'admin'))'''

new_index = '''def index():
    if session.get('role') == 'admin':
        return redirect(url_for('analytics.dashboard'))
    user_email = session.get('user_email')
    user_name = session.get('user_name')
    is_user = session.get('role') == 'user'
    return render_template('index.html', user_email=user_email, user_name=user_name, is_logged_in=is_user)'''

text = text.replace(old_index, new_index)

with open('web_server.py', 'w', encoding='utf-8') as f:
    f.write(text)
