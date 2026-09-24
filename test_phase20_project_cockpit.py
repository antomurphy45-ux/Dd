import json,tempfile,threading,unittest
from datetime import date
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app

class Phase20ProjectCockpit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/'db.sqlite'; app.init_db()
        cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler); cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2); cls.tmp.cleanup()
    def req(self,path,method='GET',body=None,cookie=None):
        data=json.dumps(body).encode() if body is not None else None; h={'Content-Type':'application/json'} if data else {}
        if cookie:h['Cookie']=cookie
        try:
            with urlopen(Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=data,headers=h),timeout=5) as r:return r.status,json.loads(r.read().decode()),r.headers
        except HTTPError as e:return e.code,json.loads(e.read().decode()),e.headers
    def login(self,email='owner@demo.local'):
        s,d,h=self.req('/api/login','POST',{'email':email,'password':'DemoPass!123'});self.assertEqual(s,200);return h['Set-Cookie'].split(';',1)[0]
    def add(self,ck,pid,module,title,data):
        s,d,_=self.req('/api/module/'+module.replace(' ','%20'),'POST',{'project_id':pid,'title':title,'data':data},ck);self.assertEqual(s,201);return d['id']
    def test_project_overview_is_connected_to_live_data(self):
        ck=self.login();s,d,_=self.req('/api/projects','POST',{'name':'Cockpit Project'},ck);self.assertEqual(s,201);pid=d['id']
        self.add(ck,pid,'RFIs','RFI-001',{'rfi_no':'RFI-001','subject':'Design detail','status':'Open','due_date':'2026-09-16'})
        self.add(ck,pid,'Risks','Risk-001',{'risk_id':'R-1','description':'Access','status':'Open','due_date':'2026-09-16','likelihood':4,'impact':5})
        self.add(ck,pid,'Manpower','Crew',{'date':date.today().isoformat(),'role':'Electrician','planned_men':5,'actual_men':4,'hours':8})
        s,d,_=self.req('/api/plans','POST',{'project_id':pid,'name':'Main Programme'},ck);self.assertEqual(s,201);plan=d['id']
        self.req(f'/api/plans/{plan}/tasks','POST',{'name':'Install','start_date':'2026-09-17','finish_date':'2026-09-18','percent_complete':50,'planned_men':5},ck)
        s,d,_=self.req('/api/project-overview?project_id='+pid,cookie=ck);self.assertEqual(s,200)
        self.assertEqual(d['project']['id'],pid);self.assertEqual(d['kpis']['records'],3);self.assertEqual(d['kpis']['actual_men'],4.0);self.assertEqual(d['kpis']['today_actual_men'],4.0)
        self.assertEqual(next(x for x in d['modules'] if x['module']=='RFIs')['count'],1);self.assertEqual(next(x for x in d['modules'] if x['module']=='Risks')['count'],1)
        self.assertEqual(len(d['attention']),2);self.assertEqual(d['programme']['name'],'Main Programme');self.assertEqual(d['programme']['progress'],50.0)
    def test_project_overview_rejects_inaccessible_project(self):
        owner=self.login();s,d,_=self.req('/api/projects','POST',{'name':'Owner Private'},owner);pid=d['id']
        site=self.login('site@demo.local');s,d,_=self.req('/api/project-overview?project_id='+pid,cookie=site);self.assertEqual(s,403)
    def test_project_overview_filters_modules_by_view_permission(self):
        owner=self.login();s,d,_=self.req('/api/projects','POST',{'name':'Scoped'},owner);pid=d['id']
        self.add(owner,pid,'RFIs','Private RFI',{'subject':'x'})
        self.add(owner,pid,'Daily Control','Daily',{'date':'2026-09-17'})
        # Create a least-privilege role directly in the isolated test database.
        c=app.db(); c.execute("INSERT INTO roles(id,company_id,name) VALUES(?,?,?)",('R-SCOPED','C1','Scoped Test User')); c.executemany("INSERT INTO permissions(role_id,module,action,allowed) VALUES(?,?,?,?)",[('R-SCOPED',m,a,0) for m in app.MODULES for a in app.ACTIONS]); c.execute("UPDATE permissions SET allowed=1 WHERE role_id=? AND module='Daily Control' AND action='View'",('R-SCOPED',)); uid='U-SCOPED'; c.execute("INSERT INTO users(id,company_id,name,email,password_hash,active,role) VALUES(?,?,?,?,?,?,?)",(uid,'C1','Scoped Site','scoped@demo.local',app.pw_hash('DemoPass!123'),1,'Scoped Test User')); c.execute("INSERT INTO project_access(user_id,project_id) VALUES(?,?)",(uid,pid)); c.commit(); c.close()
        site=self.login('scoped@demo.local');s,d,_=self.req('/api/project-overview?project_id='+pid,cookie=site);self.assertEqual(s,200)
        names={x['module'] for x in d['modules']};self.assertIn('Daily Control',names);self.assertNotIn('RFIs',names)

if __name__=='__main__':unittest.main(verbosity=2)
