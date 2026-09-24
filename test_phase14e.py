import json, tempfile, threading, unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app

class P14E(unittest.TestCase):
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
        if cookie: r.add_header('Cookie',cookie)
        try:
            with urlopen(r,timeout=5) as x: return x.status,json.loads(x.read().decode()),x.headers
        except HTTPError as e: return e.code,json.loads(e.read().decode()),e.headers
    def login(self,email='owner@demo.local'):
        s,b,h=self.req('/api/login','POST',{'email':email,'password':'DemoPass!123'}); self.assertEqual(s,200); return h['Set-Cookie'].split(';',1)[0]
    def test_update_history_and_performance(self):
        ck=self.login(); s,b,_=self.req('/api/projects','POST',{'name':'Performance Test'},ck); self.assertEqual(s,201); pid=b['id']
        s,b,_=self.req('/api/plans','POST',{'project_id':pid,'name':'Programme'},ck); self.assertEqual(s,201); plan=b['id']
        ids=[]
        for name in ('Install','Test'):
            s,b,_=self.req(f'/api/plans/{plan}/tasks','POST',{'name':name,'start_date':'2026-09-01','finish_date':'2026-09-05','percent_complete':0,'planned_men':4},ck); self.assertEqual(s,201); ids.append(b['id'])
        s,b,_=self.req(f'/api/plans/{plan}/update','POST',{'update_date':'2026-09-05','note':'Week 1','tasks':[{'id':ids[0],'percent_complete':50},{'id':ids[1],'percent_complete':25}]},ck); self.assertEqual(s,200)
        s,b,_=self.req(f'/api/plans/{plan}/update','POST',{'update_date':'2026-09-12','note':'Week 2','tasks':[{'id':ids[0],'percent_complete':100,'actual_start':'2026-09-01','actual_finish':'2026-09-10'},{'id':ids[1],'percent_complete':75}]},ck); self.assertEqual(s,200)
        s,h,_=self.req(f'/api/plans/{plan}/updates',cookie=ck); self.assertEqual(s,200); self.assertEqual(len(h['updates']),2); self.assertEqual(h['updates'][0]['update_date'],'2026-09-12')
        s,p,_=self.req(f'/api/plans/{plan}/performance',cookie=ck); self.assertEqual(s,200); self.assertEqual(p['update_count'],2); self.assertEqual([x['progress'] for x in p['trend']],[37.5,87.5]); self.assertEqual(p['current_progress'],87.5)
    def test_invalid_update_is_atomic(self):
        ck=self.login(); s,b,_=self.req('/api/projects','POST',{'name':'Atomic Test'},ck); pid=b['id']; s,b,_=self.req('/api/plans','POST',{'project_id':pid,'name':'Programme'},ck); plan=b['id']
        s,b,_=self.req(f'/api/plans/{plan}/tasks','POST',{'name':'A','start_date':'2026-09-01','finish_date':'2026-09-02','percent_complete':10},ck); tid=b['id']
        s,b,_=self.req(f'/api/plans/{plan}/update','POST',{'update_date':'2026-09-05','tasks':[{'id':tid,'percent_complete':50},{'id':'NOPE','percent_complete':80}]},ck); self.assertEqual(s,400)
        c=app.db(); self.assertEqual(c.execute('select count(*) from plan_updates where plan_id=?',(plan,)).fetchone()[0],0); self.assertEqual(c.execute('select percent_complete from plan_tasks where id=?',(tid,)).fetchone()[0],10); c.close()
    def test_other_tenant_cannot_read_performance(self):
        ck=self.login(); s,b,_=self.req('/api/projects','POST',{'name':'Tenant Project'},ck); self.assertEqual(s,201); pid=b['id']; s,b,_=self.req('/api/plans','POST',{'project_id':pid,'name':'Programme'},ck); plan=b['id']
        site=self.login('site@demo.local'); s,b,_=self.req(f'/api/plans/{plan}/performance',cookie=site); self.assertIn(s,(404,403))

if __name__=='__main__': unittest.main(verbosity=2)
