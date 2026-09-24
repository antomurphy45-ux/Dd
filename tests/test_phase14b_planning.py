import json, threading, tempfile, unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app

class Phase14BPlanning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/'db.sqlite'; app.init_db()
        cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2); cls.tmp.cleanup()
    def req(self,path,method='GET',body=None,cookie=None):
        data=json.dumps(body).encode() if body is not None else None
        r=Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=data,headers={'Content-Type':'application/json'} if data else {})
        if cookie:r.add_header('Cookie',cookie)
        try:
            with urlopen(r,timeout=5) as x:return x.status,json.loads(x.read().decode()),x.headers
        except HTTPError as e:return e.code,json.loads(e.read().decode()),e.headers
    def login(self):
        s,b,h=self.req('/api/login','POST',{'email':'owner@demo.local','password':'DemoPass!123'}); self.assertEqual(s,200); return h['Set-Cookie'].split(';',1)[0]
    def test_working_days_dependencies_baseline_resources_lookahead(self):
        ck=self.login(); s,b,_=self.req('/api/plans','POST',{'project_id':'P1','name':'Enhanced Programme'},ck); self.assertEqual(s,201); pid=b['id']
        payloads=[
            {'name':'A','start_date':'2026-09-18','finish_date':'2026-09-21','planned_men':4},
            {'name':'B','start_date':'2026-09-21','finish_date':'2026-09-23','planned_men':6,'predecessor_id':None,'dependency_type':'SS','lag_days':1},
        ]
        ids=[]
        for p in payloads:
            s,b,_=self.req(f'/api/plans/{pid}/tasks','POST',p,ck); self.assertEqual(s,201); ids.append(b['id'])
        # Update B to depend on A using Finish-to-Start with one working-day lag.
        s,b,_=self.req(f'/api/plans/{pid}/tasks/{ids[1]}','PUT',{'predecessor_id':ids[0],'dependency_type':'FS','lag_days':1},ck); self.assertEqual(s,200)
        s,g,_=self.req(f'/api/plans/{pid}/gantt',cookie=ck); self.assertEqual(s,200)
        self.assertEqual(g['tasks'][0]['scheduled_start'],'2026-09-18')
        self.assertEqual(g['tasks'][0]['scheduled_finish'],'2026-09-21')
        self.assertEqual(g['tasks'][1]['scheduled_start'],'2026-09-23')
        self.assertTrue(any(t['critical'] for t in g['tasks']))
        s,b,_=self.req(f'/api/plans/{pid}/baseline','POST',{},ck); self.assertEqual(s,200)
        c=app.db(); row=c.execute('select baseline,baseline_start,baseline_finish from plans p join plan_tasks t on t.plan_id=p.id where p.id=?',(pid,)).fetchone(); self.assertEqual(row['baseline'],1); self.assertEqual(row['baseline_start'],'2026-09-18'); c.close()
        s,r,_=self.req(f'/api/plans/{pid}/resources',cookie=ck); self.assertEqual(s,200); self.assertGreaterEqual(r['peak_men'],6)
        s,l,_=self.req(f'/api/plans/{pid}/lookahead?days=28',cookie=ck); self.assertEqual(s,200); self.assertEqual(len(l['tasks']),2)
    def test_cycle_is_rejected(self):
        ck=self.login(); s,b,_=self.req('/api/plans','POST',{'project_id':'P1','name':'Cycle Test'},ck); pid=b['id']
        ids=[]
        for n in ('A','B'):
            s,b,_=self.req(f'/api/plans/{pid}/tasks','POST',{'name':n,'start_date':'2026-09-01','finish_date':'2026-09-02'},ck); ids.append(b['id'])
        self.assertEqual(self.req(f'/api/plans/{pid}/tasks/{ids[0]}','PUT',{'predecessor_id':ids[1]},ck)[0],200)
        self.assertEqual(self.req(f'/api/plans/{pid}/tasks/{ids[1]}','PUT',{'predecessor_id':ids[0]},ck)[0],200)
        s,b,_=self.req(f'/api/plans/{pid}/gantt',cookie=ck); self.assertEqual(s,409); self.assertIn('cycle',b['error'].lower())

if __name__=='__main__': unittest.main(verbosity=2)
