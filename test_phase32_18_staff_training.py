import sys; sys.path.insert(0, '.')
import json, tempfile, threading, urllib.request, urllib.error
from pathlib import Path
import app

def req(base, method, path, body=None, cookie=None):
    data=json.dumps(body).encode() if body is not None else None
    headers={'Content-Type':'application/json'} if body is not None else {}
    if cookie: headers['Cookie']=cookie
    r=urllib.request.Request(base+path,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(r,timeout=5) as x:
            return x.status,json.loads(x.read()),x.headers.get('Set-Cookie','')
    except urllib.error.HTTPError as e:
        return e.code,json.loads(e.read()),e.headers.get('Set-Cookie','')

def test_staff_training_crud_persists():
    with tempfile.TemporaryDirectory() as td:
        old=app.DB_PATH; app.DB_PATH=Path(td)/'construction_control.db'; app.init_db()
        srv=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler); th=threading.Thread(target=srv.serve_forever,daemon=True); th.start()
        base=f'http://127.0.0.1:{srv.server_address[1]}'
        try:
            code,_,sc=req(base,'POST','/api/login',{'email':'owner@demo.local','password':'DemoPass!123'}); assert code==200
            cookie=sc.split(';',1)[0]
            code,staff,_=req(base,'GET','/api/staff?active=all',cookie=cookie); assert code==200
            sid=staff['staff'][0]['id']
            body={'training_name':'Manual Handling','provider':'Test Provider','completed_date':'2026-09-20','expiry_date':'2027-09-20','certificate_ref':'MH-001','status':'Current','notes':'Annual refresher'}
            code,out,_=req(base,'POST',f'/api/staff/{sid}/training',body,cookie); assert code==201
            tid=out['id']
            code,out,_=req(base,'GET',f'/api/staff/{sid}/training',cookie=cookie); assert code==200 and len(out['training'])==1 and out['training'][0]['training_name']=='Manual Handling'
            code,_,_=req(base,'PUT',f'/api/staff/{sid}/training/{tid}',{**body,'training_name':'Manual Handling Refresher'},cookie); assert code==200
            code,out,_=req(base,'GET',f'/api/staff/{sid}/training',cookie=cookie); assert out['training'][0]['training_name']=='Manual Handling Refresher'
            code,_,_=req(base,'DELETE',f'/api/staff/{sid}/training/{tid}',cookie=cookie); assert code==200
            code,out,_=req(base,'GET',f'/api/staff/{sid}/training',cookie=cookie); assert out['training']==[]
        finally:
            srv.shutdown(); srv.server_close(); th.join(timeout=2); app.DB_PATH=old
