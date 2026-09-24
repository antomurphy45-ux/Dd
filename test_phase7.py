import os
from pathlib import Path
import tempfile, unittest, sqlite3
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app

class Phase7Test(unittest.TestCase):
    def test_module_tenant_and_permission(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"x.db"; app.init_db(db); c=sqlite3.connect(db); c.row_factory=sqlite3.Row
            owner=c.execute("SELECT * FROM users WHERE id=\"U1\"").fetchone()
            self.assertTrue(app.can_access_project(c, owner, "P1"))
            c.execute("INSERT INTO module_records(id,company_id,project_id,module,title,data_json) VALUES(?,?,?,?,?,?)",("r1","C1","P1","RFIs","Test RFI","{}")); c.commit()
            self.assertEqual(c.execute("SELECT company_id FROM module_records WHERE id=?",("r1",)).fetchone()["company_id"],"C1")
            self.assertFalse(app.can_access_project(c, owner, "P2")); c.close()

    def test_module_permission_function(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"x.db"; app.init_db(db); c=sqlite3.connect(db); c.row_factory=sqlite3.Row
            manager=c.execute("SELECT * FROM users WHERE id=\"U2\"").fetchone()
            self.assertTrue(app.has_permission(c,manager,"RFIs","View"))
            self.assertTrue(app.has_permission(c,manager,"RFIs","Create"))
            self.assertFalse(app.has_permission(c,manager,"RFIs","Delete")); c.close()

if __name__=="__main__": unittest.main()

class Phase7HttpTest(unittest.TestCase):
    def test_login_and_module_crud_http(self):
        import threading, urllib.request, urllib.error, json, http.cookiejar
        from http.server import ThreadingHTTPServer
        with tempfile.TemporaryDirectory() as td:
            old=app.DB_PATH; app.DB_PATH=Path(td)/'http.db'; app.init_db()
            server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler); t=threading.Thread(target=server.serve_forever,daemon=True); t.start()
            try:
                base=f'http://127.0.0.1:{server.server_port}'
                jar=http.cookiejar.CookieJar(); opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
                def req(method,path,payload=None):
                    r=urllib.request.Request(base+path,method=method,data=json.dumps(payload).encode() if payload is not None else None,headers={'Content-Type':'application/json'})
                    with opener.open(r,timeout=3) as x:return x.status,json.loads(x.read())
                status,_=req('POST','/api/login',{'email':'owner@demo.local','password':'DemoPass!123'}); self.assertEqual(status,200)
                status,d=req('POST','/api/module/RFIs',{'project_id':'P1','title':'RFI 001','data':{'subject':'Test subject','notes':'Test'}}); self.assertEqual(status,201); rid=d['id']
                status,d=req('GET','/api/module/RFIs?project_id=P1'); self.assertEqual(status,200); self.assertEqual(len(d['records']),1)
                status,_=req('PUT',f'/api/module/RFIs/{rid}',{'title':'RFI 001 updated','data':{'subject':'Changed subject','notes':'Changed'}}); self.assertEqual(status,200)
                status,_=req('DELETE',f'/api/module/RFIs/{rid}'); self.assertEqual(status,200)
                status,d=req('GET','/api/module/RFIs?project_id=P1'); self.assertEqual(status,200); self.assertEqual(d['records'],[])
            finally:
                server.shutdown(); server.server_close(); app.DB_PATH=old


class Phase8DashboardTest(unittest.TestCase):
    def test_dashboard_is_tenant_scoped(self):
        import app
        with tempfile.TemporaryDirectory() as td:
            app.DB_PATH = Path(td) / "cc.db"
            app.init_db()
            c=app.db()
            u=c.execute("SELECT * FROM users WHERE id='U2'").fetchone()
            c.execute("INSERT INTO module_records(id,company_id,project_id,module,title,data_json,created_by) VALUES(?,?,?,?,?,?,?)",("R1","C1","P1","RFIs","RFI-001",'{}','U2'))
            c.commit()
            # U2 has P1 only; the dashboard must not expose C2/P2.
            projects=c.execute("SELECT p.id FROM projects p JOIN project_access pa ON pa.project_id=p.id WHERE p.company_id=? AND pa.user_id=?",(u['company_id'],u['id'])).fetchall()
            self.assertEqual(set(x['id'] for x in projects),{'P1','DUB10','DUB50'})
            self.assertEqual(c.execute("SELECT COUNT(*) FROM module_records WHERE company_id='C1'").fetchone()[0],1)
            c.close()
