import unittest, tempfile, json, base64, threading, urllib.request, urllib.error, http.cookiejar, urllib.parse, urllib.request
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
import app

class Phase13Adversarial(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory(); self.old_db=app.DB_PATH; self.old_up=app.UPLOADS
        app.DB_PATH=Path(self.td.name)/'db.sqlite'; app.UPLOADS=Path(self.td.name)/'uploads'; app.UPLOADS.mkdir()
        app.init_db()
        self.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler); threading.Thread(target=self.server.serve_forever,daemon=True).start()
        self.base=f'http://127.0.0.1:{self.server.server_port}'; self.jar=http.cookiejar.CookieJar(); self.op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); app.DB_PATH=self.old_db; app.UPLOADS=self.old_up; self.td.cleanup()
    def req(self,method,path,payload=None):
        data=json.dumps(payload).encode() if payload is not None else None
        r=urllib.request.Request(self.base+path,method=method,data=data,headers={'Content-Type':'application/json'})
        try:
            with self.op.open(r,timeout=3) as x:return x.status,json.loads(x.read() or b'{}')
        except urllib.error.HTTPError as e:
            try:return e.code,json.loads(e.read() or b'{}')
            except:return e.code,{}
    def login(self,email='owner@demo.local'):
        return self.req('POST','/api/login',{'email':email,'password':'DemoPass!123'})
    def test_cross_tenant_module_and_attachment_are_denied(self):
        self.login(); st,_=self.req('GET','/api/module/RFIs?project_id=P2'); self.assertEqual(st,403)
        st,_=self.req('POST','/api/attachments',{'project_id':'P2','filename':'x.txt','mime_type':'text/plain','content_base64':base64.b64encode(b'x').decode()}); self.assertEqual(st,403)
    def test_non_admin_cannot_enumerate_other_projects(self):
        self.login('manager@demo.local'); st,d=self.req('GET','/api/projects'); self.assertEqual(st,200); self.assertEqual(set(p['id'] for p in d['projects']),{'P1','DUB10','DUB50'})
    def test_bad_record_link_is_rejected(self):
        self.login(); st,d=self.req('POST','/api/module/RFIs',{'project_id':'P1','title':'RFI','data':{'subject':'Adversarial test'}}); self.assertEqual(st,201)
        rid=d['id']; st,_=self.req('POST','/api/attachments',{'project_id':'P1','record_id':'not-a-real-record','filename':'x.txt','mime_type':'text/plain','content_base64':base64.b64encode(b'x').decode()}); self.assertEqual(st,400)
    def test_nul_filename_rejected(self):
        self.login(); st,_=self.req('POST','/api/attachments',{'project_id':'P1','filename':'x\u0000.txt','mime_type':'text/plain','content_base64':base64.b64encode(b'x').decode()}); self.assertEqual(st,400)
    def test_invalid_json_does_not_create_record(self):
        r=urllib.request.Request(self.base+'/api/login',method='POST',data=b'{bad',headers={'Content-Type':'application/json'})
        try:self.op.open(r,timeout=3)
        except urllib.error.HTTPError as e:self.assertEqual(e.code,400)
        c=app.db(); self.assertEqual(c.execute("select count(*) from module_records").fetchone()[0],0); c.close()
    def test_inactive_user_session_is_denied(self):
        self.login('manager@demo.local'); c=app.db(); c.execute("update users set active=0 where email='manager@demo.local'"); c.commit(); c.close(); st,_=self.req('GET','/api/me'); self.assertEqual(st,401)

if __name__=='__main__':unittest.main()
