import sys, json, tempfile, threading, urllib.request, urllib.error, io, zipfile
from pathlib import Path
sys.path.insert(0,'.')
import app

def request(base, method, path, body=None, cookie=None, content_type='application/json'):
    headers={}
    data=body
    if cookie: headers['Cookie']=cookie
    if content_type: headers['Content-Type']=content_type
    r=urllib.request.Request(base+path,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(r,timeout=10) as x:
            return x.status,x.read(),x.headers
    except urllib.error.HTTPError as e:
        return e.code,e.read(),e.headers

def test_full_backup_restore_roundtrip():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); dbpath=root/'construction_control.db'; uploads=root/'uploads'; uploads.mkdir()
        old_db,old_uploads=app.DB_PATH,app.UPLOADS
        app.DB_PATH=dbpath; app.UPLOADS=uploads; app.BACKUPS=root/'backups'; app.BACKUPS.mkdir()
        try:
            app.init_db()
            (uploads/'logo.txt').write_text('backup-logo')
            srv=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler); th=threading.Thread(target=srv.serve_forever,daemon=True); th.start()
            base=f'http://127.0.0.1:{srv.server_address[1]}'
            code,body,h=request(base,'POST','/api/login',json.dumps({'email':'owner@demo.local','password':'DemoPass!123'}).encode())
            assert code==200
            cookie=h.get('Set-Cookie').split(';',1)[0]
            code,raw,h=request(base,'GET','/api/backup/export',cookie=cookie,content_type=None)
            assert code==200 and h.get_content_type()=='application/zip'
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                assert 'manifest.json' in z.namelist()
                assert 'construction_control.db' in z.namelist()
                assert 'uploads/logo.txt' in z.namelist()
            # Make a live change, then restore the downloaded backup.
            code,body,h=request(base,'POST','/api/projects',json.dumps({'name':'Temporary Before Restore','manloader':2}).encode(),cookie)
            assert code==201
            boundary='----CCBackupTest'
            payload=(b'--'+boundary.encode()+b'\r\nContent-Disposition: form-data; name="file"; filename="backup.zip"\r\nContent-Type: application/zip\r\n\r\n'+raw+b'\r\n--'+boundary.encode()+b'--\r\n')
            code,body,h=request(base,'POST','/api/backup/restore',payload,cookie,'multipart/form-data; boundary='+boundary)
            assert code==200, body
            c=app.db()
            try:
                assert c.execute("select 1 from projects where name='Temporary Before Restore'").fetchone() is None
                assert c.execute("select 1 from projects where name='DUB84 — Infil Programme'").fetchone()
            finally: c.close()
            assert (uploads/'logo.txt').read_text()=='backup-logo'
            srv.shutdown();srv.server_close();th.join(timeout=2)
        finally:
            app.DB_PATH=old_db;app.UPLOADS=old_uploads
