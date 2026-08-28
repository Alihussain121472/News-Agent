import re
with open('web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_route = '''@app.route('/dashboard')
@admin_required
def dashboard():
    return redirect(url_for('analytics.dashboard'))

@app.route('/admin/dashboard')
def legacy_admin_dashboard():
    return redirect(url_for('analytics.dashboard'))
'''

text = text.replace('''@app.route('/dashboard')
@admin_required
def dashboard():
    return redirect(url_for('analytics.dashboard'))''', new_route)

with open('web_server.py', 'w', encoding='utf-8') as f:
    f.write(text)
