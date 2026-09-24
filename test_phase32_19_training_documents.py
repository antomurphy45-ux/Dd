import sys; sys.path.insert(0, '.')
import base64, json, tempfile, threading, urllib.request, urllib.error
from pathlib import Path
import app

def req(base, method, path, body=None, cookie=None):
    data=json.dumps(body).encode() if body is not None else None
    headers={'Content-Type':'application/json'} if body is not None else {}
    if cookie: headers['Cookie']=cookie
    r=urllib.request.Request(base+path,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(r,timeout=5) as x:
            return x.status,x.read(),x.headers.get('Set-Cookie','')
    except urllib.error.HTTPError as e:
        return e.code,e.read(),e.headers.get('Set-Cookie','')

def test_training_document_upload_download_delete():
    with tempfile.TemporaryDirectory() as td:
        old=app.DB_PATH; app.DB_PATH=Path(td)/'construction_control.db'; app.init_db()
        srv=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler); th=threading.Thread(target=srv.serve_forever,daemon=True); th.start()
        base=f'http://127.0.0.1:{srv.server_address[1]}'
        try:
            code,_,sc=req(base,'POST','/api/login',{'email':'owner@demo.local','password':'DemoPass!123'}); assert code==200
            cookie=sc.split(';',1)[0]
            code,raw,_=req(base,'GET','/api/staff?active=all',cookie=cookie); assert code==200
            sid=json.loads(raw)['staff'][0]['id']
            body={'training_name':'Manual Handling','provider':'Test Provider','completed_date':'2026-09-20','status':'Current'}
            code,raw,_=req(base,'POST',f'/api/staff/{sid}/training',body,cookie); assert code==201
            tid=json.loads(raw)['id']
            content=b'certificate test document'
            doc={'filename':'manual-handling-certificate.pdf','mime_type':'application/pdf','content_base64':base64.b64encode(content).decode()}
            code,raw,_=req(base,'POST',f'/api/staff/{sid}/training/{tid}/documents',doc,cookie); assert code==201
            did=json.loads(raw)['id']
            code,raw,_=req(base,'GET',f'/api/staff/{sid}/training/{tid}/documents',cookie=cookie); assert code==200
            docs=json.loads(raw)['documents']; assert len(docs)==1 and docs[0]['filename']==doc['filename']
            code,raw,_=req(base,'GET',f'/api/staff-training-documents/{did}',cookie=cookie); assert code==200 and raw==content
            code,raw,_=req(base,'DELETE',f'/api/staff-training-documents/{did}',cookie=cookie); assert code==200
            code,raw,_=req(base,'GET',f'/api/staff/{sid}/training/{tid}/documents',cookie=cookie); assert json.loads(raw)['documents']==[]
        finally:
            srv.shutdown(); srv.server_close(); th.join(timeout=2); app.DB_PATH=old
