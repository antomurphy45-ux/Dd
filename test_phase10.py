import tempfile, threading, urllib.request, urllib.error, json, http.cookiejar
from pathlib import Path
import sys, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
from http.server import ThreadingHTTPServer

class Phase10WorkflowTest(unittest.TestCase):
    def test_workflow_notification_and_authorisation(self):
        with tempfile.TemporaryDirectory() as td:
            old=app.DB_PATH; app.DB_PATH=Path(td)/'db.sqlite'; app.init_db()
            server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler); t=threading.Thread(target=server.serve_forever,daemon=True); t.start()
            try:
                base=f'http://127.0.0.1:{server.server_port}'
                jar=http.cookiejar.CookieJar(); opener=http.cookiejar.CookieJar(); opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
                def req(method,path,payload=None,expect_error=False):
                    data=json.dumps(payload).encode() if payload is not None else None
                    r=urllib.request.Request(base+path,method=method,data=data,headers={'Content-Type':'application/json'})
                    try:
                        with opener.open(r,timeout=3) as x:return x.status,json.loads(x.read() or b'{}')
                    except urllib.error.HTTPError as e:return e.code,json.loads(e.read() or b'{}')
                self.assertEqual(req('POST','/api/login',{'email':'owner@demo.local','password':'DemoPass!123'})[0],200)
                st,d=req('POST','/api/module/RFIs',{'project_id':'P1','title':'RFI Approval Test','data':{'subject':'Approval test'}}); self.assertEqual(st,201); rid=d['id']
                st,d=req('POST','/api/workflows',{'project_id':'P1','module':'RFIs','record_id':rid,'approver_user_id':'U2'}); self.assertEqual(st,201); wid=d['id']
                st,d=req('GET','/api/workflows?project_id=P1'); self.assertEqual(st,200); self.assertEqual(d['workflows'][0]['status'],'Pending')
                # Switch to manager account with a fresh cookie jar.
                jar2=http.cookiejar.CookieJar(); op2=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar2))
                r=urllib.request.Request(base+'/api/login',method='POST',data=json.dumps({'email':'manager@demo.local','password':'DemoPass!123'}).encode(),headers={'Content-Type':'application/json'})
                with op2.open(r,timeout=3) as x:self.assertEqual(x.status,200)
                def req2(method,path,payload=None):
                    r=urllib.request.Request(base+path,method=method,data=json.dumps(payload).encode() if payload is not None else None,headers={'Content-Type':'application/json'})
                    try:
                        with op2.open(r,timeout=3) as x:return x.status,json.loads(x.read() or b'{}')
                    except urllib.error.HTTPError as e:return e.code,json.loads(e.read() or b'{}')
                st,d=req2('GET','/api/notifications'); self.assertEqual(st,200); self.assertTrue(any(n['type']=='Approval Requested' for n in d['notifications']))
                st,d=req2('PUT',f'/api/workflows/{wid}',{'decision':'Approved','note':'Reviewed'}); self.assertEqual(st,200); self.assertEqual(d['status'],'Approved')
                st,d=req2('PUT',f'/api/workflows/{wid}',{'decision':'Rejected'}); self.assertEqual(st,409)
                # Manager must not be able to approve a workflow for an inaccessible project.
                st,d=req2('POST','/api/workflows',{'project_id':'P2','module':'RFIs','record_id':rid,'approver_user_id':'U2'}); self.assertIn(st,(400,403))
            finally:
                server.shutdown(); server.server_close(); app.DB_PATH=old

    def test_notification_is_user_scoped(self):
        with tempfile.TemporaryDirectory() as td:
            app.DB_PATH=Path(td)/'db.sqlite'; app.init_db(); c=app.db()
            u1=c.execute("SELECT * FROM users WHERE id='U1'").fetchone(); u2=c.execute("SELECT * FROM users WHERE id='U2'").fetchone()
            app.notify(c,'C1','U2','P1','Test','Private','Only U2'); c.commit()
            rows=c.execute("SELECT * FROM notifications WHERE company_id=? AND user_id=?",('C1','U1')).fetchall(); self.assertEqual(rows,[])
            rows=c.execute("SELECT * FROM notifications WHERE company_id=? AND user_id=?",('C1','U2')).fetchall(); self.assertEqual(len(rows),1)
            c.close()

if __name__=='__main__': unittest.main()
