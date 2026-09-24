import json,tempfile,threading,unittest,secrets
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app

class Phase25DailySiteControl(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/'db.sqlite'; app.init_db()
  cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler); cls.port=cls.server.server_address[1]
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
 @classmethod
 def tearDownClass(cls): cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2);cls.tmp.cleanup()
 def req(self,path,method='GET',body=None,cookie=None):
  data=json.dumps(body).encode() if body is not None else None; h={'Content-Type':'application/json'} if body is not None else {}
  if cookie:h['Cookie']=cookie
  try:
   with urlopen(Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=data,headers=h),timeout=5) as r:return r.status,json.loads(r.read().decode())
  except HTTPError as e:return e.code,json.loads(e.read().decode())
 def login(self):
  s,d=self.req('/api/login','POST',{'email':'owner@demo.local','password':'DemoPass!123'}); self.assertEqual(s,200); return self.req_cookie('/api/login')
 def req_cookie(self,path):
  data=json.dumps({'email':'owner@demo.local','password':'DemoPass!123'}).encode(); r=urlopen(Request(f'http://127.0.0.1:{self.port}{path}',method='POST',data=data,headers={'Content-Type':'application/json'}),timeout=5); return r.headers['Set-Cookie'].split(';',1)[0]
 def setup(self):
  ck=self.login(); s,d=self.req('/api/projects','POST',{'name':'Daily Project','manloader':16},ck); pid=d['id']; s,d=self.req('/api/plans','POST',{'project_id':pid,'name':'Programme'},ck); plan=d['id']
  s,d=self.req('/api/tasks','POST',{'project_id':pid,'plan_id':plan,'name':'Task starting today','start_date':'2026-09-18','duration_working_days':2,'planned_men':4},ck); t1=d['id']
  s,d=self.req('/api/tasks','POST',{'project_id':pid,'plan_id':plan,'name':'Late task','start_date':'2026-09-16','duration_working_days':2,'planned_men':3},ck); t2=d['id']
  s,d=self.req('/api/staff','POST',{'staff_ref':'E1-'+secrets.token_hex(2),'name':'John','position':'Electrician'},ck); sid1=d['id']
  s,d=self.req('/api/staff','POST',{'staff_ref':'E2-'+secrets.token_hex(2),'name':'Mark','position':'Foreman'},ck); sid2=d['id']
  return ck,pid,plan,t1,t2,sid1,sid2
 def test_daily_get_derives_planned_men_and_flags_tasks(self):
  ck,pid,plan,t1,t2,s1,s2=self.setup(); s,d=self.req(f'/api/daily-site-control?project_id={pid}&date=2026-09-18',cookie=ck); self.assertEqual(s,200); self.assertEqual(d['planned_men'],4.0); self.assertTrue(any(x['id']==t1 and x['bucket']=='starting' for x in d['tasks'])); self.assertTrue(any(x['id']==t2 and x['bucket']=='late_start' for x in d['tasks'])); self.assertEqual(d['actual_men'],0)
 def test_daily_save_is_atomic_and_readback(self):
  ck,pid,plan,t1,t2,s1,s2=self.setup(); payload={'project_id':pid,'date':'2026-09-18','attendance':[{'staff_id':s1,'onsite':True,'hours':8},{'staff_id':s2,'onsite':False,'hours':8}],'tasks':[{'id':t1,'percent_complete':50}], 'status':'Complete','safety_check':'Completed','completed_activities':'Containment started','delays':'None','constraints':'','notes':'Daily note'}
  s,d=self.req('/api/daily-site-control','POST',payload,ck); self.assertEqual(s,200)
  s,d=self.req(f'/api/daily-site-control?project_id={pid}&date=2026-09-18',cookie=ck); self.assertEqual(d['actual_men'],1); self.assertEqual(d['man_hours'],8.0); self.assertEqual(d['daily']['completed_activities'],'Containment started'); self.assertEqual(next(x for x in d['tasks'] if x['id']==t1)['percent_complete'],50)
 def test_daily_save_rejects_invalid_staff_and_is_atomic(self):
  ck,pid,plan,t1,t2,s1,s2=self.setup()
  payload={'project_id':pid,'date':'2026-09-18','attendance':[{'staff_id':s1,'onsite':True,'hours':8},{'staff_id':'not-a-real-staff','onsite':True,'hours':8}], 'tasks':[{'id':t1,'percent_complete':50}]}
  s,d=self.req('/api/daily-site-control','POST',payload,ck); self.assertEqual(s,400)
  s,d=self.req(f'/api/daily-site-control?project_id={pid}&date=2026-09-18',cookie=ck); self.assertEqual(d['actual_men'],0); self.assertEqual(next(x for x in d['tasks'] if x['id']==t1)['percent_complete'],0)

if __name__=='__main__': unittest.main()
