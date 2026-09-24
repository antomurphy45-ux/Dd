import json, tempfile, threading, unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app

class DashboardIntegration(unittest.TestCase):
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
        r=Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=data,headers={'Content-Type':'application/json'} if data else {})
        if cookie:r.add_header('Cookie',cookie)
        try:
            with urlopen(r,timeout=5) as x:return x.status,json.loads(x.read().decode()),x.headers
        except HTTPError as e:return e.code,json.loads(e.read().decode()),e.headers
    def login(self,email):
        s,b,h=self.req('/api/login','POST',{'email':email,'password':'DemoPass!123'});self.assertEqual(s,200);return h['Set-Cookie'].split(';',1)[0]
    def test_dashboard_reflects_entered_project_data(self):
        ck=self.login('owner@demo.local')
        s,b,_=self.req('/api/projects','POST',{'name':'Dashboard Live Test'},ck);self.assertEqual(s,201);pid=b['id']
        s,b,_=self.req('/api/module/RFIs','POST',{'project_id':pid,'title':'RFI-001','data':{'subject':'Demo RFI','status':'Open'}},ck);self.assertEqual(s,201)
        s,b,_=self.req('/api/module/Risks','POST',{'project_id':pid,'title':'Risk-001','data':{'description':'Demo risk','status':'Open'}},ck);self.assertEqual(s,201)
        s,b,_=self.req('/api/module/Actions','POST',{'project_id':pid,'title':'Action-001','data':{'description':'Demo action','status':'Open'}},ck);self.assertEqual(s,201)
        s,b,_=self.req('/api/module/Snags','POST',{'project_id':pid,'title':'Snag-001','data':{'description':'Demo snag','status':'Open'}},ck);self.assertEqual(s,201)
        s,b,_=self.req('/api/plans','POST',{'project_id':pid,'name':'Live Programme'},ck);self.assertEqual(s,201);plan=b['id']
        s,b,_=self.req(f'/api/plans/{plan}/tasks','POST',{'name':'Install','start_date':'2026-09-17','finish_date':'2026-09-18','percent_complete':50,'planned_men':4},ck);self.assertEqual(s,201)
        s,b,_=self.req('/api/module/Manpower','POST',{'project_id':pid,'title':'Day 1','data':{'date':'2026-09-17','role':'Electrician','planned_men':4,'actual_men':5,'hours':8}},ck);self.assertEqual(s,201)
        s,d,_=self.req('/api/dashboard',cookie=ck);self.assertEqual(s,200)
        row=next(x for x in d['project_summary'] if x['project_id']==pid)
        self.assertEqual(row['records'],5);self.assertEqual(row['kpis']['rfis'],1);self.assertEqual(row['kpis']['risks'],1);self.assertEqual(row['kpis']['actions'],1);self.assertEqual(row['kpis']['snags'],1)
        self.assertIsNotNone(row['active_plan']);self.assertEqual(row['active_plan']['name'],'Live Programme');self.assertEqual(row['active_plan']['progress'],50.0);self.assertEqual(row['active_plan']['activity_count'],1)
        self.assertEqual(d['total_records'],5);self.assertEqual(d['total_kpis']['rfis'],1);self.assertEqual(d['total_kpis']['risks'],1);self.assertEqual(d['total_kpis']['actions'],1);self.assertEqual(d['total_kpis']['snags'],1)
    def test_dashboard_updates_after_edit(self):
        ck=self.login('owner@demo.local')
        s,b,_=self.req('/api/projects','POST',{'name':'Dashboard Edit Test'},ck);pid=b['id']
        s,b,_=self.req('/api/module/RFIs','POST',{'project_id':pid,'title':'RFI','data':{'subject':'Private test','status':'Open'}},ck);rid=b['id']
        s,d,_=self.req('/api/dashboard',cookie=ck);row=next(x for x in d['project_summary'] if x['project_id']==pid);self.assertEqual(row['kpis']['rfis'],1)
        s,_,_=self.req(f'/api/module/RFIs/{rid}','PUT',{'title':'RFI closed','data':{'subject':'Demo RFI closed','status':'Closed'}},ck);self.assertEqual(s,200)
        s,d,_=self.req('/api/dashboard',cookie=ck);row=next(x for x in d['project_summary'] if x['project_id']==pid);self.assertEqual(row['kpis']['rfis'],1)
    def test_scoped_user_dashboard_does_not_count_unassigned_project(self):
        owner=self.login('owner@demo.local')
        s,b,_=self.req('/api/projects','POST',{'name':'Owner Only'},owner);pid=b['id']
        self.req('/api/module/RFIs','POST',{'project_id':pid,'title':'Private RFI','data':{'subject':'Private RFI subject'}},owner)
        site=self.login('site@demo.local')
        s,d,_=self.req('/api/dashboard',cookie=site);self.assertEqual(s,200);self.assertEqual(d['total_records'],0);self.assertFalse(any(x['project_id']==pid for x in d['project_summary']))

if __name__=='__main__':unittest.main(verbosity=2)
