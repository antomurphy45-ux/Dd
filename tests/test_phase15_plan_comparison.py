import json,tempfile,threading,unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app

class Phase15PlanComparison(unittest.TestCase):
 """Regression test: /api/plans/<id>/comparison and /integration were fully implemented
 but unreachable because the route guard only listed gantt/resources/lookahead. This
 pins the fix so it cannot silently regress."""
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/'db.sqlite'; app.init_db()
  cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler); cls.port=cls.server.server_address[1]
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
 @classmethod
 def tearDownClass(cls): cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2);cls.tmp.cleanup()
 def req(self,path,method='GET',body=None,cookie=None):
  data=json.dumps(body).encode() if body is not None else None;r=Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=data,headers={'Content-Type':'application/json'} if data else {})
  if cookie:r.add_header('Cookie',cookie)
  try:
   with urlopen(r,timeout=5) as x:return x.status,json.loads(x.read().decode()),x.headers
  except HTTPError as e:return e.code,json.loads(e.read().decode()),e.headers
 def login(self,email='owner@demo.local'):
  s,_,h=self.req('/api/login','POST',{'email':email,'password':'DemoPass!123'});self.assertEqual(s,200);return h['Set-Cookie'].split(';',1)[0]

 def test_comparison_and_integration_routes_are_reachable(self):
  ck=self.login();s,b,_=self.req('/api/projects','POST',{'name':'Comparison Route Project'},ck);pid=b['id']
  s,b,_=self.req('/api/plans','POST',{'project_id':pid,'name':'Programme'},ck);plan=b['id']
  s,b,_=self.req(f'/api/plans/{plan}/tasks','POST',{'name':'Task A','start_date':'2026-09-21','finish_date':'2026-09-22','percent_complete':50,'planned_men':2},ck);self.assertEqual(s,201)
  self.req(f'/api/plans/{plan}/baseline','POST',{},ck)
  s,comp,_=self.req(f'/api/plans/{plan}/comparison',cookie=ck)
  self.assertEqual(s,200)
  self.assertIn('current_finish',comp); self.assertIn('baseline_finish',comp); self.assertIn('programme_progress',comp)
  s,integ,_=self.req(f'/api/plans/{plan}/integration',cookie=ck)
  self.assertEqual(s,200)
  self.assertIn('programme_progress',integ); self.assertIn('manpower',integ); self.assertIn('daily_control',integ)

if __name__=='__main__':unittest.main(verbosity=2)
