from web_server import app
with app.test_client() as c:
    response = c.get('/admin/login')
    print('LOGIN STATUS:', response.status_code)
    
    with c.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['user_email'] = 'admin@novabrief.local'
        
    response2 = c.get('/analytics/dashboard')
    print('DASHBOARD STATUS:', response2.status_code)
    
