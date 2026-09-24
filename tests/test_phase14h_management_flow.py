import json,tempfile,threading,unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app

class Phase14HManagementFlow(unittest.TestCase):
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
 def test_enter_change_re_read_management_centre(self):
  ck=self.login();s,b,_=self.req('/api/projects','POST',{'name':'Management Live Project'},ck);self.assertEqual(s,201);pid=b['id']
  # Enter controls; use a past due date so the management centre must surface it.
  s,b,_=self.req('/api/module/Actions','POST',{'project_id':pid,'title':'Cable route approval','data':{'description':'Confirm cable route','status':'Open','due_date':'2026-09-01'}},ck);self.assertEqual(s,201);aid=b['id']
  s,b,_=self.req('/api/module/RFIs','POST',{'project_id':pid,'title':'RFI-001','data':{'subject':'RFI subject','status':'Open'}},ck);self.assertEqual(s,201)
  s,b,_=self.req('/api/module/Manpower','POST',{'project_id':pid,'title':'Day 1','data':{'date':'2026-09-17','role':'Electrician','planned_men':4,'actual_men':6,'hours':8}},ck);self.assertEqual(s,201)
  s,b,_=self.req('/api/plans','POST',{'project_id':pid,'name':'Main Programme'},ck);self.assertEqual(s,201);plan=b['id']
  s,b,_=self.req(f'/api/plans/{plan}/tasks','POST',{'name':'Install','start_date':'2026-09-17','finish_date':'2026-09-20','percent_complete':25,'planned_men':4},ck);self.assertEqual(s,201)
  s,mg,_=self.req('/api/management',cookie=ck);self.assertEqual(s,200)
  p=next(x for x in mg['projects'] if x['project_id']==pid);self.assertEqual(p['open']['Actions'],1);self.assertEqual(p['manpower']['actual_men'],6.0);self.assertEqual(p['programme']['progress'],25.0);self.assertEqual(mg['totals']['overdue_items'],1)
  self.assertEqual(mg['issues'][0]['title'],'Cable route approval')
  # Change the action to closed and manpower to 7; management must re-read the new state.
  s,_,_=self.req(f'/api/module/Actions/{aid}','PUT',{'title':'Cable route approval','data':{'description':'Confirm cable route','status':'Closed','due_date':'2026-09-01'}},ck);self.assertEqual(s,200)
  s,mp,_=self.req('/api/module/Manpower?project_id='+pid,cookie=ck);mid=mp['records'][0]['id']
  s,_,_=self.req(f'/api/module/Manpower/{mid}','PUT',{'title':'Day 1 updated','data':{'date':'2026-09-17','role':'Electrician','planned_men':4,'actual_men':7,'hours':9}},ck);self.assertEqual(s,200)
  s,mg,_=self.req('/api/management',cookie=ck);p=next(x for x in mg['projects'] if x['project_id']==pid)
  self.assertEqual(p['open'].get('Actions',0),0);self.assertEqual(p['manpower']['actual_men'],7.0);self.assertEqual(p['manpower']['man_hours'],63.0);self.assertEqual(mg['totals']['overdue_items'],0)
 def test_management_is_project_and_tenant_scoped(self):
  ck=self.login();s,b,_=self.req('/api/projects','POST',{'name':'Scoped Project'},ck);self.assertEqual(s,201);pid=b['id']
  # Create data in a different company using the seeded site account.
  site=self.login('site@demo.local');s,b,_=self.req('/api/management',cookie=site);self.assertEqual(s,200)
  self.assertFalse(any(x['project_id']==pid for x in b['projects']))

if __name__=='__main__':unittest.main(verbosity=2)
