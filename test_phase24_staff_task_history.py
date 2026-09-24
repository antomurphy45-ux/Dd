import json,tempfile,threading,unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app

class Phase24StaffTaskHistory(unittest.TestCase):
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
  
  data=json.dumps({'email':'owner@demo.local','password':'DemoPass!123'}).encode(); r=urlopen(Request(f'http://127.0.0.1:{self.port}/api/login',method='POST',data=data,headers={'Content-Type':'application/json'}),timeout=5); self.assertEqual(r.status,200); return r.headers['Set-Cookie'].split(';',1)[0]
 def setup(self):
  ck=self.login(); s,d=self.req('/api/projects','POST',{'name':'Staff History Project','manloader':12},ck); self.assertEqual(s,201); pid=d['id']
  s,d=self.req('/api/plans','POST',{'project_id':pid,'name':'Main Programme'},ck); self.assertEqual(s,201); plan=d['id']
  s,d=self.req('/api/tasks','POST',{'project_id':pid,'plan_id':plan,'name':'Containment installation','start_date':'2026-09-21','duration_working_days':3,'planned_men':4},ck); self.assertEqual(s,201); tid=d['id']
  return ck,pid,plan,tid
 def test_staff_crud_and_project_scoped_task_assignment_history(self):
  ck,pid,plan,tid=self.setup()
  s,d=self.req('/api/staff','POST',{'staff_ref':'EMP-001','name':'John Electric','position':'Electrician'},ck); self.assertEqual(s,201); sid=d['id']
  s,d=self.req('/api/staff','GET',cookie=ck); self.assertEqual(s,200); self.assertIn('John Electric',[x['name'] for x in d['staff']])
  s,d=self.req(f'/api/tasks/{tid}/staff','POST',{'staff_id':sid},ck); self.assertEqual(s,201); aid=d['id']
  s,d=self.req(f'/api/tasks/{tid}/history',cookie=ck); self.assertEqual(s,200); self.assertEqual(len(d['assignments']),1); self.assertEqual(d['assignments'][0]['staff_id'],sid); self.assertEqual(d['assignments'][0]['role_on_task'],'Electrician')
  s,d=self.req(f'/api/tasks/{tid}/work','POST',{'staff_id':sid,'work_date':'2026-09-21','hours':8,'note':'Installed containment'},ck); self.assertEqual(s,201)
  s,d=self.req(f'/api/tasks/{tid}/work',cookie=ck); self.assertEqual(s,200); self.assertEqual(d['work_logs'][0]['name'],'John Electric'); self.assertEqual(float(d['work_logs'][0]['hours']),8.0)
  s,d=self.req(f'/api/tasks/{tid}/staff/{aid}','DELETE',cookie=ck); self.assertEqual(s,200)
  s,d=self.req(f'/api/tasks/{tid}/history',cookie=ck); self.assertEqual(s,200); self.assertIsNotNone(d['assignments'][0]['unassigned_at']); self.assertEqual(len(d['work_logs']),1)
 def test_staff_reference_unique_and_inactive_cannot_be_assigned(self):
  ck,pid,plan,tid=self.setup()
  s,d=self.req('/api/staff','POST',{'staff_ref':'EMP-002','name':'A Worker','position':'Foreman'},ck); self.assertEqual(s,201); sid=d['id']
  s,d=self.req('/api/staff','POST',{'staff_ref':'EMP-002','name':'Another','position':'GO'},ck); self.assertEqual(s,409)
  s,d=self.req('/api/staff/'+sid,'PUT',{'staff_ref':'EMP-002','name':'A Worker','position':'Foreman','active':False},ck); self.assertEqual(s,200)
  s,d=self.req(f'/api/tasks/{tid}/staff','POST',{'staff_id':sid},ck); self.assertEqual(s,400)
 def test_same_staff_cannot_have_duplicate_active_assignment(self):
  ck,pid,plan,tid=self.setup(); s,d=self.req('/api/staff','POST',{'staff_ref':'EMP-003','name':'Site Worker','position':'4th Year'},ck); sid=d['id']
  self.assertEqual(self.req(f'/api/tasks/{tid}/staff','POST',{'staff_id':sid},ck)[0],201)
  self.assertEqual(self.req(f'/api/tasks/{tid}/staff','POST',{'staff_id':sid},ck)[0],409)
 def test_invalid_work_hours_and_cross_company_staff_are_rejected(self):
  ck,pid,plan,tid=self.setup(); s,d=self.req('/api/staff','POST',{'staff_ref':'EMP-004','name':'Worker','position':'GO'},ck); sid=d['id']
  self.assertEqual(self.req(f'/api/tasks/{tid}/work','POST',{'staff_id':sid,'work_date':'2026-09-21','hours':25},ck)[0],400)
  # C2 staff must not be visible/assignable to C1.
  data=json.dumps({'email':'site@demo.local','password':'DemoPass!123'}).encode(); r=urlopen(Request(f'http://127.0.0.1:{self.port}/api/login',method='POST',data=data,headers={'Content-Type':'application/json'}),timeout=5); self.assertEqual(r.status,200); ck2=r.headers['Set-Cookie'].split(';',1)[0]
  s,d=self.req('/api/staff',cookie=ck2); self.assertEqual(s,200); self.assertFalse(any(x['id']==sid for x in d['staff']))

if __name__=='__main__': unittest.main()
