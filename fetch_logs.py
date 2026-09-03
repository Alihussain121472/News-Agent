import requests

session = requests.Session()
login_data = {
    'email': 'syedali6160@gmail.com',
    'password': 'admin'
}
res = session.post('https://novabrief-web.onrender.com/api/auth/admin/login', json=login_data)
if res.status_code == 200:
    logs = session.get('https://novabrief-web.onrender.com/api/email-logs').json()
    for l in logs[:5]:
        print(l)
else:
    print("Login failed:", res.text)
