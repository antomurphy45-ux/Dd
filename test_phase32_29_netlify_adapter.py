import json, os, shutil, sqlite3, tempfile, importlib, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_app(tmp):
    db = tmp / 'construction_control.db'
    if not db.exists(): shutil.copy2(ROOT / 'netlify_seed.db', db)
    os.environ['CONSTRUCTION_CONTROL_DB'] = str(db)
    os.environ['CONSTRUCTION_CONTROL_UPLOADS'] = str(tmp / 'uploads')
    os.environ['CONSTRUCTION_CONTROL_BACKUPS'] = str(tmp / 'backups')
    os.environ['SECURE_COOKIES'] = '1'
    sys.path.insert(0, str(ROOT))
    sys.modules.pop('app', None)
    return importlib.import_module('app')

def call(app, method, path, body=None, cookie=None):
    headers={'Content-Type':'application/json','X-Forwarded-Proto':'https'}
    if cookie: headers['Cookie']=cookie
    raw=json.dumps(body).encode() if body is not None else b''
    status, out_headers, raw_out = app.netlify_handle(method, path, headers, raw)
    try: data=json.loads(raw_out.decode())
    except Exception: data=raw_out
    return status, out_headers, data

def test_netlify_health_and_login():
    with tempfile.TemporaryDirectory() as d:
        app=load_app(Path(d))
        status, headers, data=call(app,'GET','/healthz')
        assert status == 200
        status, headers, data=call(app,'POST','/api/login',{'email':'owner@demo.local','password':'DemoPass!123'})
        assert status == 200 and data['user']['email']=='owner@demo.local'
        cookie=headers['Set-Cookie'].split(';',1)[0]
        status, _, me=call(app,'GET','/api/me',cookie=cookie)
        assert status == 200 and me['user']['email']=='owner@demo.local'

def test_netlify_settings_persist_through_adapter_restart():
    with tempfile.TemporaryDirectory() as d:
        tmp=Path(d); app=load_app(tmp)
        status, headers, _=call(app,'POST','/api/login',{'email':'owner@demo.local','password':'DemoPass!123'})
        cookie=headers['Set-Cookie'].split(';',1)[0]
        payload={'accent_color':'#123456','sidebar_color':'#234567','background_color':'#345678','card_color':'#456789','text_color':'#56789A','density':'compact','dashboard_default':'home'}
        status, _, _=call(app,'PUT','/api/settings',payload,cookie)
        assert status == 200
        sys.modules.pop('app',None)
        app2=load_app(tmp)
        status, _, got=call(app2,'GET','/api/settings',cookie=cookie)
        assert status == 200 and got['settings']['accent_color']=='#123456'
