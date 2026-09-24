import json,tempfile,threading,unittest,sys
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app

class Phase27DailyWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/"db.sqlite"; app.init_db()
        cls.server=app.ThreadingHTTPServer(("127.0.0.1",0),app.Handler); cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2); cls.tmp.cleanup()
    def req(self,path,method="GET",body=None,cookie=None):
        data=json.dumps(body).encode() if body is not None else None; h={"Content-Type":"application/json"} if data else {}
        if cookie:h["Cookie"]=cookie
        try:
            with urlopen(Request(f"http://127.0.0.1:{self.port}{path}",method=method,data=data,headers=h),timeout=5) as r:return r.status,json.loads(r.read().decode())
        except HTTPError as e:return e.code,json.loads(e.read().decode())
    def login(self):
        s,d=self.req("/api/login","POST",{"email":"owner@demo.local","password":"DemoPass!123"})
        self.assertEqual(s,200)
        # req helper does not expose headers, so login through a direct request to retain cookie.
        r=urlopen(Request(f"http://127.0.0.1:{self.port}/api/login",method="POST",data=json.dumps({"email":"owner@demo.local","password":"DemoPass!123"}).encode(),headers={"Content-Type":"application/json"}),timeout=5)
        return r.headers["Set-Cookie"].split(";",1)[0]
    def test_daily_issue_quick_capture_and_daily_readback(self):
        ck=self.login()
        s,p=self.req("/api/projects",cookie=ck);self.assertEqual(s,200);pid=p["projects"][0]["id"]
        s,d=self.req(f"/api/daily-site-control?project_id={pid}&date=2026-09-18",cookie=ck);self.assertEqual(s,200)
        s,x=self.req("/api/daily-site-issue","POST",{"project_id":pid,"date":"2026-09-18","module":"Actions","title":"Delivery delay","description":"Tray delivery delayed"},ck);self.assertEqual(s,201);self.assertEqual(x["module"],"Actions")
        s,d=self.req(f"/api/daily-site-control?project_id={pid}&date=2026-09-18",cookie=ck);self.assertEqual(s,200)
        self.assertGreaterEqual(d["controls"]["Actions"],1)
    def test_invalid_quick_issue_rejected(self):
        ck=self.login(); s,p=self.req("/api/projects",cookie=ck);pid=p["projects"][0]["id"]
        s,d=self.req("/api/daily-site-issue","POST",{"project_id":pid,"module":"Actions","title":"","description":""},ck);self.assertEqual(s,400)
    def test_daily_ui_has_quick_capture_and_photo(self):
        js=Path(__file__).resolve().parents[1]/"static"/"app.js"; txt=js.read_text()
        self.assertIn("QUICK CAPTURE",txt);self.assertIn("dailyPhoto",txt);self.assertIn("uploadDailyPhoto",txt)
if __name__=="__main__":unittest.main()
