import json, tempfile, threading, unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app

class Phase14C(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/'db.sqlite'; app.init_db()
        cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler); cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2); cls.tmp.cleanup()
    def req(self,path,method='GET',body=None,cookie=None):
        data=json.dumps(body).encode() if body is not None else None
        h={'Content-Type':'application/json'} if data else {}
        if cookie: h['Cookie']=cookie
        r=Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=data,headers=h)
        try:
            with urlopen(r,timeout=5) as x:return x.status,json.loads(x.read().decode()),x.headers
        except HTTPError as e:return e.code,json.loads(e.read().decode()),e.headers
    def login(self):
        s,b,h=self.req('/api/login','POST',{'email':'owner@demo.local','password':'DemoPass!123'}); self.assertEqual(s,200); return h['Set-Cookie'].split(';',1)[0]
    def test_calendar_exception_changes_working_day(self):
        ck=self.login(); s,b,_=self.req('/api/plans','POST',{'project_id':'P1','name':'Calendar Test'},ck); self.assertEqual(s,201); plan=b['id']
        s,b,_=self.req('/api/plan-calendar','POST',{'project_id':'P1','plan_id':plan,'exception_date':'2026-09-07','working':False,'reason':'Site shutdown'},ck); self.assertEqual(s,200)
        self.assertFalse(app.plan_is_working(app.db(),'C1','P1',plan,__import__('datetime').date(2026,9,7)))
    def test_programme_update_changes_progress_and_audit(self):
        ck=self.login(); s,b,_=self.req('/api/plans','POST',{'project_id':'P1','name':'Update Test'},ck); plan=b['id']
        s,b,_=self.req(f'/api/plans/{plan}/tasks','POST',{'name':'Install','start_date':'2026-09-07','finish_date':'2026-09-09','percent_complete':0,'planned_men':3},ck); tid=b['id']
        s,b,_=self.req(f'/api/plans/{plan}/update','POST',{'tasks':[{'id':tid,'percent_complete':50}]},ck); self.assertEqual(s,200); self.assertEqual(b['updated'],1)
        s,b,_=self.req(f'/api/plans/{plan}',cookie=ck); self.assertEqual(b['tasks'][0]['percent_complete'],50)
        c=app.db(); self.assertTrue(c.execute("select 1 from audit where action='PLAN_PROGRAMME_UPDATE' and target=?",(plan,)).fetchone()); c.close()
    def test_invalid_programme_update_rejected_without_partial_commit(self):
        ck=self.login(); s,b,_=self.req('/api/plans','POST',{'project_id':'P1','name':'Atomic Test'},ck); plan=b['id']
        ids=[]
        for n in ('A','B'):
            s,b,_=self.req(f'/api/plans/{plan}/tasks','POST',{'name':n,'start_date':'2026-09-07','finish_date':'2026-09-08','percent_complete':0},ck); ids.append(b['id'])
        s,b,_=self.req(f'/api/plans/{plan}/update','POST',{'tasks':[{'id':ids[0],'percent_complete':75},{'id':'bad','percent_complete':90}]},ck); self.assertEqual(s,400)
        c=app.db(); self.assertEqual(c.execute('select percent_complete from plan_tasks where id=?',(ids[0],)).fetchone()[0],0); c.close()
    def test_calendar_is_tenant_scoped(self):
        ck=self.login(); s,b,_=self.req('/api/plan-calendar?project_id=P2',cookie=ck); self.assertEqual(s,403)

if __name__=='__main__': unittest.main(verbosity=2)
