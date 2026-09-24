import json, tempfile, threading, unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app

class Phase14D(unittest.TestCase):
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
        if cookie: h['Cookie']=cookie
        try:
            with urlopen(Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=data,headers=h),timeout=5) as x:return x.status,json.loads(x.read().decode()),x.headers
        except HTTPError as e:return e.code,json.loads(e.read().decode()),e.headers
    def login(self):
        s,b,h=self.req('/api/login','POST',{'email':'owner@demo.local','password':'DemoPass!123'}); self.assertEqual(s,200); return h['Set-Cookie'].split(';',1)[0]
    def test_control_centre_counts_and_overdue(self):
        ck=self.login(); s,b,_=self.req('/api/plans','POST',{'project_id':'P1','name':'Control'},ck); self.assertEqual(s,201); pid=b['id']
        self.req(f'/api/plans/{pid}/tasks','POST',{'name':'Finished','start_date':'2026-09-01','finish_date':'2026-09-02','percent_complete':100},ck)
        self.req(f'/api/plans/{pid}/tasks','POST',{'name':'Incomplete','start_date':'2020-01-01','finish_date':'2020-01-02','percent_complete':25},ck)
        s,b,_=self.req(f'/api/plans/{pid}/control',cookie=ck); self.assertEqual(s,200); self.assertEqual(b['activity_counts']['total'],2); self.assertEqual(b['activity_counts']['completed'],1); self.assertEqual(len(b['overdue']),1)
    def test_control_centre_respects_project_tenant(self):
        ck=self.login(); s,b,_=self.req('/api/plans?project_id=P2',cookie=ck); self.assertEqual(s,403)
    def test_control_centre_baseline_variance(self):
        ck=self.login(); s,b,_=self.req('/api/plans','POST',{'project_id':'P1','name':'Variance'},ck); pid=b['id']
        s,b,_=self.req(f'/api/plans/{pid}/tasks','POST',{'name':'Task','start_date':'2026-09-01','finish_date':'2026-09-05','percent_complete':50},ck); self.assertEqual(s,201)
        self.assertEqual(self.req(f'/api/plans/{pid}/baseline','POST',cookie=ck)[0],200)
        # Move current finish later; baseline remains captured.
        tid=b['id']; self.assertEqual(self.req(f'/api/plans/{pid}/tasks/{tid}','PUT',{'name':'Task','start_date':'2026-09-01','finish_date':'2026-09-09','percent_complete':50,'planned_men':0,'dependency_type':'FS','lag_days':0},ck)[0],200)
        s,b,_=self.req(f'/api/plans/{pid}/control',cookie=ck); self.assertEqual(s,200); self.assertEqual(b['baseline_finish'],'2026-09-05'); self.assertEqual(b['current_finish'],'2026-09-09'); self.assertEqual(b['baseline_finish_variance_days'],4)
    def test_control_centre_rejects_invalid_dependency_graph(self):
        ck=self.login(); s,b,_=self.req('/api/plans','POST',{'project_id':'P1','name':'Cycle'},ck); pid=b['id']
        ids=[]
        for n in ('A','B'):
            s,b,_=self.req(f'/api/plans/{pid}/tasks','POST',{'name':n,'start_date':'2026-09-01','finish_date':'2026-09-02'},ck); ids.append(b['id'])
        # Existing task validation prevents self/cross-reference errors at create/edit level; create a cycle directly to test defence-in-depth.
        c=app.db(); c.execute('UPDATE plan_tasks SET predecessor_id=? WHERE id=?',(ids[1],ids[0])); c.execute('UPDATE plan_tasks SET predecessor_id=? WHERE id=?',(ids[0],ids[1])); c.commit(); c.close()
        s,b,_=self.req(f'/api/plans/{pid}/control',cookie=ck); self.assertEqual(s,409); self.assertIn('cycle',b['error'].lower())

if __name__=='__main__': unittest.main(verbosity=2)
