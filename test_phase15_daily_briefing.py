import json,tempfile,threading,unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app

class Phase15DailyBriefing(unittest.TestCase):
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

 def test_as_of_reproduces_a_historical_days_briefing(self):
  ck=self.login();s,b,_=self.req('/api/projects','POST',{'name':'Daily Briefing Project'},ck);self.assertEqual(s,201);pid=b['id']
  # Manpower logged on three different days.
  self.req('/api/module/Manpower','POST',{'project_id':pid,'title':'Day 1','data':{'date':'2026-09-15','role':'Electrician','planned_men':4,'actual_men':4,'hours':8}},ck)
  self.req('/api/module/Manpower','POST',{'project_id':pid,'title':'Day 2','data':{'date':'2026-09-16','role':'Electrician','planned_men':4,'actual_men':5,'hours':8}},ck)
  self.req('/api/module/Manpower','POST',{'project_id':pid,'title':'Day 3','data':{'date':'2026-09-17','role':'Electrician','planned_men':6,'actual_men':6,'hours':8}},ck)
  # Programme task running 15th-18th.
  s,b,_=self.req('/api/plans','POST',{'project_id':pid,'name':'Main Programme'},ck);plan=b['id']
  self.req(f'/api/plans/{plan}/tasks','POST',{'name':'First fix','start_date':'2026-09-15','finish_date':'2026-09-18','percent_complete':40,'planned_men':4},ck)
  # As-of the 16th: only that day's manpower counts as "today", task is in progress, not yet due/overdue.
  s,mg,_=self.req(f'/api/management?project_id={pid}&as_of=2026-09-16',cookie=ck);self.assertEqual(s,200)
  self.assertEqual(mg['as_of'],'2026-09-16')
  p=next(x for x in mg['projects'] if x['project_id']==pid)
  self.assertEqual(p['manpower_today']['actual_men'],5.0)
  self.assertEqual(p['manpower']['actual_men'],15.0)
  self.assertEqual(p['programme']['in_progress_today'],1)
  self.assertEqual(p['programme']['due_today'],0)
  self.assertEqual(p['programme']['overdue_activities'],0)
  # As-of the 19th (after finish, still only 40% done): now overdue, not "today's" manpower entry.
  s,mg2,_=self.req(f'/api/management?as_of=2026-09-19',cookie=ck)
  p2=next(x for x in mg2['projects'] if x['project_id']==pid)
  self.assertEqual(p2['manpower_today']['actual_men'],0.0)
  self.assertEqual(p2['programme']['overdue_activities'],1)
  # Re-running as_of=2026-09-16 later must give the identical historical snapshot (reproducibility).
  s,mg3,_=self.req(f'/api/management?as_of=2026-09-16',cookie=ck)
  p3=next(x for x in mg3['projects'] if x['project_id']==pid)
  self.assertEqual(p3['manpower_today']['actual_men'],5.0)

 def test_as_of_defaults_to_today_and_rejects_bad_dates(self):
  ck=self.login()
  s,mg,_=self.req('/api/management',cookie=ck);self.assertEqual(s,200)
  from datetime import date
  self.assertEqual(mg['as_of'],date.today().isoformat())
  s,b,_=self.req('/api/management?as_of=not-a-date',cookie=ck);self.assertEqual(s,400)

if __name__=='__main__':unittest.main(verbosity=2)
