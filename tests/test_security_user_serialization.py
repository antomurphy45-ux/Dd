import json,tempfile,threading,unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app

class UserSerializationSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        app.DB_PATH=Path(cls.tmp.name)/'db.sqlite'
        app.init_db()
        c=app.db()
        # Simulate a future schema change: a sensitive user field must not
        # become browser-visible merely because it is added to users.
        c.execute("ALTER TABLE users ADD COLUMN api_secret TEXT")
        c.execute("UPDATE users SET api_secret='SHOULD_NEVER_LEAK'")
        c.commit(); c.close()
        cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2); cls.tmp.cleanup()

    def req(self,path,method='GET',body=None,cookie=None):
        data=json.dumps(body).encode() if body is not None else None
        headers={'Content-Type':'application/json'} if data else {}
        if cookie: headers['Cookie']=cookie
        try:
            with urlopen(Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=data,headers=headers),timeout=5) as r:
                raw=r.read().decode(); return r.status,(json.loads(raw) if raw else {}),r.headers
        except HTTPError as e:
            raw=e.read().decode(); return e.code,(json.loads(raw) if raw else {}),e.headers

    def login(self):
        s,d,h=self.req('/api/login','POST',{'email':'owner@demo.local','password':'DemoPass!123'})
        self.assertEqual(s,200)
        self.assertNotIn('password_hash', json.dumps(d))
        self.assertNotIn('api_secret', json.dumps(d))
        self.assertIn('user',d); self.assertIn('company',d)
        self.assertEqual(set(d['user']), {'id','company_id','name','email','active','role','created_at'})
        return h['Set-Cookie'].split(';',1)[0]

    def test_login_never_returns_password_hash_or_sensitive_future_columns(self):
        self.login()

    def test_me_never_returns_password_hash_or_sensitive_future_columns(self):
        ck=self.login()
        s,d,_=self.req('/api/me',cookie=ck)
        self.assertEqual(s,200)
        self.assertNotIn('password_hash', json.dumps(d))
        self.assertNotIn('api_secret', json.dumps(d))
        self.assertEqual(set(d['user']), {'id','company_id','name','email','active','role','created_at'})

    def test_internal_database_row_still_contains_hash_for_authentication_only(self):
        c=app.db(); row=c.execute("SELECT * FROM users WHERE email='owner@demo.local'").fetchone(); c.close()
        self.assertTrue(row['password_hash'])
        self.assertTrue(row['api_secret'])
        self.assertNotEqual(row['password_hash'],'DemoPass!123')

if __name__=='__main__': unittest.main()
