from web_server import app
with app.test_client() as c:
    with c.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['user_email'] = 'admin@novabrief.tech'
    response = c.get('/analytics/messages')
    print('MESSAGES STATUS:', response.status_code)
    response2 = c.get('/analytics/dashboard')
    print('DASHBOARD STATUS:', response2.status_code)
