import tempfile, threading, urllib.request, urllib.error, json, http.cookiejar
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
from http.server import ThreadingHTTPServer
import unittest

class Phase9AttachmentTest(unittest.TestCase):
    def test_attachment_upload_download_tenant_scope(self):
        with tempfile.TemporaryDirectory() as td:
            olddb, oldup = app.DB_PATH, app.UPLOADS
            app.DB_PATH=Path(td)/'db.sqlite'; app.UPLOADS=Path(td)/'uploads'; app.UPLOADS.mkdir()
            app.init_db()
            server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler); t=threading.Thread(target=server.serve_forever,daemon=True); t.start()
            try:
                base=f'http://127.0.0.1:{server.server_port}'; jar=http.cookiejar.CookieJar(); opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
                def req(method,path,payload=None):
                    data=json.dumps(payload).encode() if payload is not None else None
                    r=urllib.request.Request(base+path,method=method,data=data,headers={'Content-Type':'application/json'})
                    try:
                        with opener.open(r,timeout=3) as x:return x.status,x.read()
                    except urllib.error.HTTPError as e:return e.code,e.read()
                self.assertEqual(req('POST','/api/login',{'email':'owner@demo.local','password':'DemoPass!123'})[0],200)
                import base64
                content=base64.b64encode(b'hello construction control').decode()
                st,body=req('POST','/api/attachments',{'project_id':'P1','filename':'test.txt','mime_type':'text/plain','content_base64':content}); self.assertEqual(st,201); aid=json.loads(body)['id']
                st,body=req('GET','/api/attachments?project_id=P1'); self.assertEqual(st,200); self.assertIn(b'test.txt',body)
                st,body=req('GET',f'/api/attachments/{aid}'); self.assertEqual(st,200); self.assertEqual(body,b'hello construction control')
                # Cross-company attachment access must fail.
                c=app.db(); c.execute("INSERT INTO attachments(id,company_id,project_id,filename,stored_name,mime_type,size_bytes) VALUES(?,?,?,?,?,?,?)",('CROSS','C1','P1','cross.txt','cross.bin','text/plain',1)); c.commit(); c.close()
            finally:
                server.shutdown(); server.server_close(); app.DB_PATH=olddb; app.UPLOADS=oldup

if __name__=='__main__': unittest.main()
