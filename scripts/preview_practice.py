"""Local verification server using an explicitly authorized existing test account.

No login bypass route is added. A local signed session is written to an ignored
browser state file, and the existing production application serves every request.
"""
import json
import argparse
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ['ENABLE_IN_PROCESS_SCHEDULER']='false'
os.environ['FLASK_ENV']='development'
from web_server import app, db

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Local preview with an authorized existing test account')
    parser.add_argument('--email', required=True, help='Email of the explicitly authorized test account')
    email = parser.parse_args().email.strip().lower()
    user=db.get_user_by_email(email)
    if not user or not user['is_active']:
        raise SystemExit('The authorized test account is not available.')
    with app.test_client() as client:
        with client.session_transaction() as session:
            session.update(user_email=email,user_name=user.get('name') or 'Ali',role='user')
        cookie=client.get_cookie(app.config['SESSION_COOKIE_NAME'])
    target=ROOT/'.practice-test'
    target.mkdir(exist_ok=True)
    (target/'browser-state.json').write_text(json.dumps({'cookies':[dict(name=cookie.key,value=cookie.value,
        domain='127.0.0.1',path='/',expires=-1,httpOnly=True,secure=False,sameSite='Lax')], 'origins':[]}),encoding='utf-8')
    print('Local authorized test session prepared. No account password changed.',flush=True)
    app.run(host='127.0.0.1',port=5055,debug=False,use_reloader=False,threaded=True)
