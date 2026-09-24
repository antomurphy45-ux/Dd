import json,tempfile,threading,unittest,sys
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app

class Phase32DailyOperatingSequence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/"db.sqlite"; app.init_db()
        cls.server=app.ThreadingHTTPServer(("127.0.0.1",0),app.Handler); cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2);cls.tmp.cleanup()
    def req(self,path,method="GET",body=None,cookie=None):
        h={"Content-Type":"application/json"};
        if cookie:h["Cookie"]=cookie
        try:
            with urlopen(Request(f"http://127.0.0.1:{self.port}{path}",method=method,data=json.dumps(body).encode() if body is not None else None,headers=h),timeout=5) as r:return r.status,json.loads(r.read().decode()),r.headers
        except HTTPError as e:return e.code,json.loads(e.read().decode()),e.headers
    def login(self):
        s,_,h=self.req('/api/login','POST',{'email':'owner@demo.local','password':'DemoPass!123'});self.assertEqual(s,200);return h['Set-Cookie'].split(';',1)[0]
    def test_assignment_attendance_held_up_and_close_out_persist(self):
        ck=self.login(); s,p,_=self.req('/api/projects',cookie=ck);pid=p['projects'][0]['id']
        s,x,_=self.req('/api/staff','POST',{'staff_ref':'TEST-DUB10-E1','name':'Pat Electrician','position':'Electrician'},ck);self.assertEqual(s,201);sid=x['id']
        day='2026-09-20';s,x,_=self.req('/api/project-assignments','POST',{'project_id':pid,'staff_id':sid,'assignment_role':'Electrician','start_date':'2026-09-19','finish_date':'2026-09-21'},ck);self.assertEqual(s,201)
        s,x,_=self.req('/api/project-assignments?project_id='+pid,cookie=ck);self.assertEqual(s,200);self.assertTrue(any(a['staff_id']==sid for a in x['assignments']))
        s,x,_=self.req('/api/plans','POST',{'project_id':pid,'name':'DUB10 Programme'},ck);plan=x['id']
        s,x,_=self.req('/api/tasks','POST',{'project_id':pid,'plan_id':plan,'name':'LV Board Installation','start_date':day,'duration':2,'status':'Starting','planned_men':1},ck);self.assertEqual(s,201);tid=x['id']
        body={'project_id':pid,'date':day,'attendance':[{'staff_id':sid,'onsite':True,'hours':8}], 'tasks':[{'id':tid,'percent_complete':55,'status':'Held Up','held_up_reason':'Material','status_notes':'Awaiting board delivery'}], 'status':'Complete','completed_activities':'Containment complete','delays':'Board delivery','notes':'Chase supplier'}
        s,x,_=self.req('/api/daily-site-control','POST',body,ck);self.assertEqual(s,200)
        s,d,_=self.req('/api/daily-site-control?project_id='+pid+'&date='+day,cookie=ck);self.assertEqual(s,200);self.assertEqual(d['actual_men'],1);self.assertTrue(any(x['id']==sid for x in d['staff']))
        task=next(t for t in d['tasks'] if t['id']==tid);self.assertEqual(task['status'],'Held Up');self.assertEqual(task['held_up_reason'],'Material');self.assertEqual(task['percent_complete'],55)
        # The close-out is a second save of the same daily record: it must retain task/attendance data.
        s,x,_=self.req('/api/daily-site-control','POST',{'project_id':pid,'date':day,'attendance':[],'tasks':[],'status':'Complete','notes':'Close-out saved'},ck);self.assertEqual(s,200)
        s,d,_=self.req('/api/daily-site-control?project_id='+pid+'&date='+day,cookie=ck);self.assertEqual(d['daily']['notes'],'Close-out saved');self.assertEqual(d['actual_men'],1)
    def test_ui_contract_and_no_unapproved_role(self):
        js=(Path(__file__).resolve().parents[1]/'static'/'app.js').read_text(encoding='utf8')
        for token in ('Morning Brief','Close Out','Starting tomorrow','Held Up','Assignments','saveCloseOut'):
            self.assertIn(token,js)
        self.assertNotIn('electrician mate',js.lower())
    def test_dashboard_health_is_red_for_held_up_work(self):
        ck=self.login();s,p,_=self.req('/api/projects',cookie=ck);pid=p['projects'][0]['id']; day='2026-09-20'
        s,x,_=self.req('/api/plans','POST',{'project_id':pid,'name':'DUB50 Programme'},ck);plan=x['id']
        s,x,_=self.req('/api/tasks','POST',{'project_id':pid,'plan_id':plan,'name':'Testing','start_date':day,'duration':1,'status':'Starting'},ck);tid=x['id']
        s,_,_=self.req('/api/daily-site-control','POST',{'project_id':pid,'date':day,'attendance':[],'tasks':[{'id':tid,'percent_complete':10,'status':'Held Up','held_up_reason':'Access'}]},ck);self.assertEqual(s,200)
        s,d,_=self.req('/api/dashboard?as_of='+day,cookie=ck);self.assertEqual(s,200);project=next(x for x in d['project_summary'] if x['project_id']==pid)
        self.assertEqual(project['health'],'red');self.assertGreaterEqual(project['programme']['held_up'],1)

if __name__=='__main__': unittest.main()
