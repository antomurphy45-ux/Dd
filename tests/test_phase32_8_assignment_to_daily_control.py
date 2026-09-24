import json, tempfile, threading, sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app

class Phase328AssignmentDailyControl(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/'db.sqlite'; app.init_db()
        cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2); cls.tmp.cleanup()
    def req(self,path,method='GET',body=None,cookie=None):
        h={'Content-Type':'application/json'}
        if cookie: h['Cookie']=cookie
        try:
            with urlopen(Request(f'http://127.0.0.1:{self.server.server_address[1]}{path}',method=method,data=json.dumps(body).encode() if body is not None else None,headers=h),timeout=5) as r:
                return r.status,json.loads(r.read().decode()),r.headers
        except HTTPError as e:
            return e.code,json.loads(e.read().decode()),e.headers
    def login(self):
        s,_,h=self.req('/api/login','POST',{'email':'owner@demo.local','password':'DemoPass!123'}); self.assertEqual(s,200); return h['Set-Cookie'].split(';',1)[0]
    def test_assignment_appears_in_daily_site_control(self):
        ck=self.login()
        s,p,_=self.req('/api/projects',cookie=ck); self.assertEqual(s,200)
        pid=next(x['id'] for x in p['projects'] if x['id']=='DUB10')
        s,x,_=self.req('/api/staff','POST',{'staff_ref':'TEST-328','name':'Assigned Inactive Test','position':'Electrician','active':False},ck); self.assertEqual(s,201); sid=x['id']
        s,x,_=self.req('/api/project-assignments','POST',{'project_id':pid,'staff_id':sid,'assignment_role':'Electrician','start_date':'2026-09-20','finish_date':'2026-09-25'},ck); self.assertEqual(s,201)
        s,d,_=self.req(f'/api/daily-site-control?project_id={pid}&date=2026-09-20',cookie=ck); self.assertEqual(s,200)
        person=next((x for x in d['staff'] if x['id']==sid),None)
        self.assertIsNotNone(person,'Assigned staff must appear in Daily Site Control')
        self.assertEqual(person['assignment_role'],'Electrician')
    def test_daily_ui_uses_assignment_staff_flag(self):
        js=(Path(__file__).resolve().parents[1]/'static'/'app.js').read_text(encoding='utf8')
        self.assertIn('filter(x=>x.staff_active!==0)',js)
        self.assertNotIn("filter(x=>x.active);",js)

    def test_assignment_outside_day_is_not_shown(self):
        ck=self.login(); s,p,_=self.req('/api/projects',cookie=ck); pid=next(x['id'] for x in p['projects'] if x['id']=='DUB10')
        s,x,_=self.req('/api/staff','POST',{'staff_ref':'TEST-329','name':'Future Assigned Test','position':'Foreman'},ck); self.assertEqual(s,201); sid=x['id']
        s,_,_=self.req('/api/project-assignments','POST',{'project_id':pid,'staff_id':sid,'assignment_role':'Foreman','start_date':'2026-09-21','finish_date':'2026-09-25'},ck); self.assertEqual(s,201)
        s,d,_=self.req(f'/api/daily-site-control?project_id={pid}&date=2026-09-20',cookie=ck); self.assertEqual(s,200)
        self.assertFalse(any(x['id']==sid for x in d['staff']))

if __name__=='__main__': unittest.main()
