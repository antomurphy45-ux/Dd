import json,tempfile,threading,unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app

class Phase22TaskAlerts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/"db.sqlite"; app.init_db(); cls.server=app.ThreadingHTTPServer(("127.0.0.1",0),app.Handler); cls.port=cls.server.server_address[1]; cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
 @classmethod
 def tearDownClass(cls): cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2);cls.tmp.cleanup()
 def req(self,path,method="GET",body=None,cookie=None):
  data=json.dumps(body).encode() if body is not None else None; h={"Content-Type":"application/json"} if body is not None else {}; h.update({"Cookie":cookie} if cookie else {})
  try:
   with urlopen(Request(f"http://127.0.0.1:{self.port}{path}",method=method,data=data,headers=h),timeout=5) as r:return r.status,json.loads(r.read().decode()),r.headers
  except HTTPError as e:return e.code,json.loads(e.read().decode()),e.headers
 def login(self):
  s,d,h=self.req("/api/login","POST",{"email":"owner@demo.local","password":"DemoPass!123"});self.assertEqual(s,200);return h["Set-Cookie"].split(";",1)[0]
 def test_notice_board_classifies_today_and_missed_tasks(self):
  ck=self.login(); s,d,_=self.req("/api/projects","POST",{"name":"Alert Project"},ck);self.assertEqual(s,201);pid=d["id"]
  s,d,_=self.req("/api/plans","POST",{"project_id":pid,"name":"Programme"},ck);self.assertEqual(s,201);plan=d["id"]
  self.req("/api/tasks","POST",{"project_id":pid,"plan_id":plan,"name":"Today task","start_date":app.date.today().isoformat(),"duration_working_days":1,"status":"Not Started"},ck)
  self.req("/api/tasks","POST",{"project_id":pid,"plan_id":plan,"name":"Missed task","start_date":"2026-01-01","duration_working_days":1,"status":"Not Started"},ck)
  self.req("/api/tasks","POST",{"project_id":pid,"plan_id":plan,"name":"Done old task","start_date":"2026-01-01","duration_working_days":1,"status":"Finished"},ck)
  s,d,_=self.req("/api/task-alerts",cookie=ck);self.assertEqual(s,200);self.assertEqual(d["today"],app.date.today().isoformat());self.assertEqual([x["name"] for x in d["today_tasks"]],["Today task"]);self.assertEqual([x["name"] for x in d["overdue_tasks"]],["Missed task"]);self.assertEqual(d["today_count"],1);self.assertEqual(d["overdue_count"],1)
