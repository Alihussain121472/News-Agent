from web_server import app
with app.test_client() as c:
    with c.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['user_email'] = 'admin@novabrief.local'
    response = c.get('/analytics/dashboard')
    print('STATUS CODE:', response.status_code)
    # print(response.text)
