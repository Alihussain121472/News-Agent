from web_server import app
with app.test_client() as c:
    response = c.post('/api/auth/login', json={'email': 'syedali6160@gmail.com', 'password': 'password123'})
    print('USER LOGIN STATUS:', response.status_code)
    print(response.get_json())
