import json,tempfile,threading,unittest,sys
from pathlib import Path
from urllib.request import Request,urlopen
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app
class Phase28PMDashboard(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/'db.sqlite'; app.init_db(); cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler); cls.port=cls.server.server_address[1]; cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
 @classmethod
 def tearDownClass(cls): cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2);cls.tmp.cleanup()
 def req(self,path,method='GET',body=None,cookie=None):
  data=json.dumps(body).encode() if body is not None else None; h={'Content-Type':'application/json'} if data else {}; h.update({'Cookie':cookie} if cookie else {})
  with urlopen(Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=data,headers=h),timeout=5) as r:return r.status,json.loads(r.read().decode())
 def login(self):
  r=urlopen(Request(f'http://127.0.0.1:{self.port}/api/login',method='POST',data=json.dumps({'email':'owner@demo.local','password':'DemoPass!123'}).encode(),headers={'Content-Type':'application/json'}),timeout=5);return r.headers['Set-Cookie'].split(';',1)[0]
 def test_dashboard_accepts_local_calendar_date_and_returns_today_attention(self):
  ck=self.login(); s,d=self.req('/api/dashboard?as_of=2026-09-21',cookie=ck); self.assertEqual(s,200); self.assertEqual(d['date'],'2026-09-21'); self.assertTrue(d['project_summary']); self.assertIn('today',d['project_summary'][0]); self.assertIn('tasks_starting',d['project_summary'][0]['today']); self.assertIn('tasks_late',d['project_summary'][0]['today'])
 def test_dashboard_rejects_invalid_date(self):
  ck=self.login();
  try:self.req('/api/dashboard?as_of=not-a-date',cookie=ck);self.fail('invalid date should fail')
  except Exception as e:self.assertIn('HTTP Error 400',str(e))
 def test_dashboard_ui_is_attention_first(self):
  js=(Path(__file__).resolve().parents[1]/'static/app.js').read_text(); css=(Path(__file__).resolve().parents[1]/'static/app.css').read_text();
  for token in ('PROJECT CONTROL CENTRE','Tasks that should have started','Tasks starting today','Projects below plan','Daily control still to complete','Open Daily Site Control','openDashboardTask') : self.assertIn(token,js)
  for token in ('.dash-hero','.dash-today-strip','.dash-priority-grid','.attention-item','.task-detail-grid'): self.assertIn(token,css)
if __name__=='__main__':unittest.main()
