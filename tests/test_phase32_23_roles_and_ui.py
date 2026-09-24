import json, shutil, tempfile, threading, urllib.request, urllib.error
from pathlib import Path
import sqlite3, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def request(base, path, method='GET', payload=None, cookie=''):
    data=json.dumps(payload).encode() if payload is not None else None
    req=urllib.request.Request(base+path, data=data, method=method, headers={'Content-Type':'application/json','Cookie':cookie} if cookie else {'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read().decode()), r.headers.get('Set-Cookie','')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode()), e.headers.get('Set-Cookie','')


def test_phase32_23_role_structure_and_permissions_and_tooltips():
    with tempfile.TemporaryDirectory() as td:
        db=Path(td)/'construction_control.db'; shutil.copy(Path(app.__file__).parent/'netlify_seed.db', db)
        old=app.DB_PATH; app.DB_PATH=db; app.init_db()
        server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        base=f'http://127.0.0.1:{server.server_address[1]}'
        try:
            code,data,cookie=request(base,'/api/login','POST',{'email':'owner@demo.local','password':'DemoPass!123'})
            assert code==200
            code,data,_=request(base,'/api/roles','GET',cookie=cookie)
            assert code==200
            names=[r['name'] for r in data['roles']]
            assert names[:8] or names
            for name in ['Viewer','Site User','Foreman','Charge Hand','Construction Manager','Business Unit Lead','Company Director','Company Administrator']:
                assert name in names
            assert 'Site Manager' not in names
            assert 'Project Manager' not in names
            ladder={x['name']:x['level'] for x in data['ladder']}
            assert ladder=={'Viewer':1,'Site User':2,'Foreman':3,'Charge Hand':4,'Construction Manager':5,'Business Unit Lead':6,'Company Director':7,'Company Administrator':8}
            # Add a foreman user; deletion is deliberately not exposed as an API route.
            code,data,_=request(base,'/api/users','POST',{'name':'Test Foreman','email':'foreman@test.local','password':'TempPass!123','role':'Foreman','active':True},cookie=cookie)
            assert code==201
            uid=data['id']
            code,_,_=request(base,f'/api/users/{uid}','DELETE',cookie=cookie)
            assert code in (404,405)
            # Company admin can assign the new foreman to an existing project.
            code,data,_=request(base,f'/api/users/{uid}/access','PUT',{'project_ids':['P1']},cookie=cookie)
            assert code==200
            code,data,_=request(base,f'/api/users/{uid}/access','GET',cookie=cookie)
            assert code==200 and data['project_ids']==['P1']
            # Construction Manager can manage access for Foreman/Charge Hand on projects they control.
            code,_,_=request(base,'/api/login','POST',{'email':'manager@demo.local','password':'DemoPass!123'})
            assert code==200
            # Login response cookie is in the third return value.
            _,_,manager_cookie=request(base,'/api/login','POST',{'email':'manager@demo.local','password':'DemoPass!123'})
            code,data,_=request(base,f'/api/users/{uid}/access','PUT',{'project_ids':['P1']},cookie=manager_cookie)
            assert code==200
            # Manager cannot assign a company-director role.
            con=sqlite3.connect(db); con.execute("UPDATE users SET role='Company Director' WHERE id=?",(uid,)); con.commit(); con.close()
            code,_,_=request(base,f'/api/users/{uid}/access','PUT',{'project_ids':['P1']},cookie=manager_cookie)
            assert code==403
        finally:
            server.shutdown(); server.server_close(); app.DB_PATH=old


def test_phase32_23_frontend_has_no_generic_open_run_tooltip_generator():
    js=(Path(app.__file__).parent/'static'/'app.js').read_text()
    assert 'Open or run this action.' not in js
    assert 'function enhanceButtonHints' not in js
