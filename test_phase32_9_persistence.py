import sys; sys.path.insert(0, ".")
import json, tempfile, threading, urllib.request, urllib.error
from pathlib import Path
import app


def req(base, method, path, body=None, cookie=None):
    data=None
    headers={}
    if body is not None:
        data=json.dumps(body).encode(); headers['Content-Type']='application/json'
    if cookie: headers['Cookie']=cookie
    r=urllib.request.Request(base+path,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(r,timeout=5) as x:
            return x.status, json.loads(x.read()), x.headers.get('Set-Cookie','')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()), e.headers.get('Set-Cookie','')


def test_project_user_persist_across_restart():
    with tempfile.TemporaryDirectory() as td:
        db=Path(td)/'construction_control.db'
        old=app.DB_PATH
        app.DB_PATH=db
        app.init_db()
        srv=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        th=threading.Thread(target=srv.serve_forever,daemon=True); th.start()
        base=f'http://127.0.0.1:{srv.server_address[1]}'
        code,b,set_cookie=req(base,'POST','/api/login',{'email':'owner@demo.local','password':'DemoPass!123'})
        assert code==200
        cookie=set_cookie.split(';',1)[0]
        code,b,_=req(base,'POST','/api/projects',{'name':'Persistence Test Project','manloader':3},cookie)
        assert code==201
        code,b,_=req(base,'POST','/api/users',{'name':'Persistence Test User','email':'persist@example.local','password':'TemporaryPass123!','role':'Site User','active':True},cookie)
        assert code==201
        srv.shutdown(); srv.server_close(); th.join(timeout=2)
        # Simulate a process restart against the same DB file.
        app.DB_PATH=db
        app.init_db()
        c=app.db()
        try:
            assert c.execute("select 1 from projects where name='Persistence Test Project'").fetchone()
            assert c.execute("select 1 from users where email='persist@example.local'").fetchone()
        finally:
            c.close(); app.DB_PATH=old
