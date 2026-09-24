
import json, tempfile, threading, unittest, os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app

class SecurityAbuseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        app.DB_PATH=Path(cls.tmp.name)/"db.sqlite"
        app.init_db()
        cls.server=app.ThreadingHTTPServer(("127.0.0.1",0),app.Handler)
        cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2); cls.tmp.cleanup()

    def setUp(self):
        # Tests share a temporary database; restore the seeded manager after the
        # deliberate inactive-session test.
        c=app.db(); c.execute("UPDATE users SET active=1 WHERE id='U2'"); c.commit(); c.close()

    def req(self,path,method="GET",body=None,cookie=None,headers=None):
        data=json.dumps(body).encode() if body is not None else None
        h=dict(headers or {})
        if data: h["Content-Type"]="application/json"
        if cookie: h["Cookie"]=cookie
        try:
            with urlopen(Request(f"http://127.0.0.1:{self.port}{path}",method=method,data=data,headers=h),timeout=5) as r:
                raw=r.read().decode()
                try: obj=json.loads(raw)
                except Exception: obj=raw
                return r.status,obj,r.headers
        except HTTPError as e:
            raw=e.read().decode()
            try: obj=json.loads(raw)
            except Exception: obj=raw
            return e.code,obj,e.headers

    def login(self,email,password="DemoPass!123",forward_https=False):
        h={"X-Forwarded-Proto":"https"} if forward_https else {}
        s,d,headers=self.req("/api/login","POST",{"email":email,"password":password},headers=h)
        self.assertEqual(s,200)
        return headers["Set-Cookie"].split(";",1)[0],d,headers

    def test_unauthenticated_api_is_denied(self):
        for path in ["/api/me","/api/dashboard","/api/projects","/api/management","/api/users","/api/audit"]:
            s,_,_=self.req(path)
            self.assertEqual(s,401,path)

    def test_tenant_and_project_isolation_for_regular_user(self):
        ck,_,_=self.login("manager@demo.local")
        # Manager can access C1/P1, never C2/P2.
        self.assertEqual(self.req("/api/projects/P2",cookie=ck)[0],403)
        self.assertEqual(self.req("/api/module/RFIs?project_id=P2",cookie=ck)[0],403)
        self.assertEqual(self.req("/api/attachments?project_id=P2",cookie=ck)[0],403)
        self.assertEqual(self.req("/api/plans?project_id=P2",cookie=ck)[0],403)
        self.assertEqual(self.req("/api/bulk-import/history?project_id=P2",cookie=ck)[0],403)

    def test_cross_tenant_record_idor_is_denied(self):
        ck,_,_=self.login("manager@demo.local")
        c=app.db()
        rid=app.secrets.token_hex(8)
        c.execute("INSERT INTO module_records(id,company_id,project_id,module,title,data_json,created_by) VALUES(?,?,?,?,?,?,?)",
                  (rid,"C2","P2","RFIs","Private C2","{}","U3")); c.commit(); c.close()
        for method in ("GET","PUT","DELETE"):
            body={"title":"attempt","data":{"subject":"attempt"}} if method=="PUT" else None
            s,_,_=self.req(f"/api/module/RFIs/{rid}",method,body,cookie=ck)
            self.assertIn(s,(404,403),method)

    def test_admin_cannot_cross_company_by_project_id(self):
        ck,_,_=self.login("owner@demo.local")
        self.assertEqual(self.req("/api/projects/P2",cookie=ck)[0],403)
        self.assertEqual(self.req("/api/plans?project_id=P2",cookie=ck)[0],403)
        self.assertEqual(self.req("/api/module/RFIs?project_id=P2",cookie=ck)[0],403)

    def test_non_admin_cannot_manage_users_roles_or_company(self):
        ck,_,_=self.login("manager@demo.local")
        self.assertEqual(self.req("/api/users",cookie=ck)[0],403)
        self.assertEqual(self.req("/api/users/U2/access",cookie=ck)[0],403)
        self.assertEqual(self.req("/api/roles",cookie=ck)[0],403)
        self.assertEqual(self.req("/api/company","PUT",{"name":"attacker","country":"Ireland"},cookie=ck)[0],403)
        self.assertEqual(self.req("/api/audit",cookie=ck)[0],403)

    def test_inactive_user_session_is_rejected(self):
        ck,_,_=self.login("manager@demo.local")
        c=app.db(); c.execute("UPDATE users SET active=0 WHERE id='U2'"); c.commit(); c.close()
        self.assertEqual(self.req("/api/me",cookie=ck)[0],401)

    def test_invalid_or_expired_session_is_rejected(self):
        self.assertEqual(self.req("/api/me",cookie="cc_session=not-a-real-token")[0],401)

    def test_sensitive_fields_are_not_exposed_by_user_management(self):
        ck,_,_=self.login("owner@demo.local")
        s,d,_=self.req("/api/users",cookie=ck)
        self.assertEqual(s,200)
        raw=json.dumps(d)
        self.assertNotIn("password_hash",raw)
        self.assertNotIn("api_secret",raw)

    def test_security_headers_are_present(self):
        s,_,h=self.req("/api/me")  # 401 still must carry headers
        self.assertEqual(s,401)
        for key in ("X-Content-Type-Options","X-Frame-Options","Referrer-Policy","Permissions-Policy"):
            self.assertTrue(h.get(key),key)

    def test_https_forwarded_login_sets_secure_cookie(self):
        ck,d,h=self.login("owner@demo.local",forward_https=True)
        self.assertIn("Secure",h["Set-Cookie"])
        self.assertIn("HttpOnly",h["Set-Cookie"])
        self.assertIn("SameSite=Strict",h["Set-Cookie"])

    def test_plain_http_development_login_remains_usable(self):
        ck,d,h=self.login("owner@demo.local")
        self.assertNotIn("Secure",h["Set-Cookie"])
        self.assertIn("HttpOnly",h["Set-Cookie"])
        self.assertIn("SameSite=Strict",h["Set-Cookie"])
        self.assertEqual(self.req("/api/me",cookie=ck)[0],200)

    def test_path_encoded_project_ids_do_not_bypass_access_control(self):
        ck,_,_=self.login("manager@demo.local")
        for encoded in ("%50%32","P2%00","P2%2F..%2FP1"):
            s,_,_=self.req("/api/projects/"+encoded,cookie=ck)
            self.assertIn(s,(400,403,404))

if __name__=="__main__": unittest.main()
