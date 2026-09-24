import base64, json, tempfile, threading, unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app

class Phase14GDataFlow(unittest.TestCase):
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
    def login(self):
        s,_,h=self.req('/api/login','POST',{'email':'owner@demo.local','password':'DemoPass!123'}); self.assertEqual(s,200); return h['Set-Cookie'].split(';',1)[0]
    def test_enter_change_re_read_across_control_centre(self):
        ck=self.login()
        s,b,_=self.req('/api/projects','POST',{'name':'Live Data Flow Project'},ck); self.assertEqual(s,201); pid=b['id']
        # Enter initial site data.
        for module,title,data in [
            ('RFIs','RFI-001',{'subject':'Flow RFI','status':'Open'}),('Risks','Risk-001',{'description':'Flow risk','status':'Open'}),
            ('Actions','Action-001',{'description':'Flow action','status':'Open'}),('Snags','Snag-001',{'description':'Flow snag','status':'Open'}),
            ('Manpower','Day 1',{'date':'2026-09-17','role':'Electrician','planned_men':4,'actual_men':5,'hours':8})]:
            s,b,_=self.req('/api/module/'+module,'POST',{'project_id':pid,'title':title,'data':data},ck); self.assertEqual(s,201)
        # Create a live programme and capture a baseline.
        s,b,_=self.req('/api/plans','POST',{'project_id':pid,'name':'Live Programme'},ck); self.assertEqual(s,201); plan=b['id']
        s,b,_=self.req(f'/api/plans/{plan}/tasks','POST',{'name':'Install containment','start_date':'2026-09-17','finish_date':'2026-09-18','percent_complete':50,'planned_men':4},ck); self.assertEqual(s,201); task=b['id']
        s,_,_=self.req(f'/api/plans/{plan}/baseline','POST',None,ck); self.assertEqual(s,200)
        # READ: dashboard must show exactly what was entered.
        s,d,_=self.req('/api/dashboard',cookie=ck); self.assertEqual(s,200); row=next(x for x in d['project_summary'] if x['project_id']==pid)
        self.assertEqual(row['kpis']['rfis'],1); self.assertEqual(row['kpis']['risks'],1); self.assertEqual(row['kpis']['actions'],1); self.assertEqual(row['kpis']['snags'],1)
        self.assertEqual(row['manpower']['planned_men'],4.0); self.assertEqual(row['manpower']['actual_men'],5.0); self.assertEqual(row['manpower']['man_hours'],40.0)
        self.assertEqual(row['active_plan']['progress'],50.0); self.assertEqual(row['programme']['finish_variance_days'],0)
        # CHANGE: progress and programme finish move; then dashboard must reflect the changed state.
        s,_,_=self.req(f'/api/plans/{plan}/tasks/{task}','PUT',{'name':'Install containment','start_date':'2026-09-17','finish_date':'2026-09-21','percent_complete':75,'planned_men':6,'actual_start':'2026-09-17'},ck); self.assertEqual(s,200)
        s,d,_=self.req('/api/dashboard',cookie=ck); row=next(x for x in d['project_summary'] if x['project_id']==pid)
        self.assertEqual(row['active_plan']['progress'],75.0); self.assertEqual(row['active_plan']['finish'],'2026-09-21'); self.assertEqual(row['programme']['finish_variance_days'],3)
        # CHANGE: manpower record update; dashboard manpower must change too.
        s,mp,_=self.req('/api/module/Manpower?project_id='+pid,cookie=ck); self.assertEqual(s,200); mid=mp['records'][0]['id']
        s,_,_=self.req(f'/api/module/Manpower/{mid}','PUT',{'title':'Day 1 updated','data':{'date':'2026-09-17','role':'Electrician','planned_men':6,'actual_men':7,'hours':9}},ck); self.assertEqual(s,200)
        s,d,_=self.req('/api/dashboard',cookie=ck); row=next(x for x in d['project_summary'] if x['project_id']==pid)
        self.assertEqual(row['manpower']['planned_men'],6.0); self.assertEqual(row['manpower']['actual_men'],7.0); self.assertEqual(row['manpower']['man_hours'],63.0); self.assertEqual(row['manpower']['variance_men'],1.0)
        # Enter an approval + document and confirm the dashboard counts change.
        s,rf,_=self.req('/api/module/RFIs?project_id='+pid,cookie=ck); rid=rf['records'][0]['id']
        s,w,_=self.req('/api/workflows','POST',{'project_id':pid,'module':'RFIs','record_id':rid,'approver_user_id':'U1'},ck); self.assertEqual(s,201)
        content=base64.b64encode(b'live-flow').decode(); s,_,_=self.req('/api/attachments','POST',{'project_id':pid,'record_id':rid,'filename':'live.pdf','mime_type':'application/pdf','content_base64':content},ck); self.assertEqual(s,201)
        s,d,_=self.req('/api/dashboard',cookie=ck); row=next(x for x in d['project_summary'] if x['project_id']==pid)
        self.assertEqual(row['kpis']['pending_approvals'],1); self.assertEqual(row['kpis']['documents'],1)
        # Complete approval and confirm the pending count changes to zero.
        wid=w['id']; s,_,_=self.req('/api/workflows/'+wid,'PUT',{'decision':'Approved','note':'Approved'},ck); self.assertEqual(s,200)
        s,d,_=self.req('/api/dashboard',cookie=ck); row=next(x for x in d['project_summary'] if x['project_id']==pid)
        self.assertEqual(row['kpis']['pending_approvals'],0); self.assertEqual(row['kpis']['documents'],1)
        # Planning performance must also see the updated task/manpower values.
        s,p,_=self.req(f'/api/plans/{plan}/performance',cookie=ck); self.assertEqual(s,200); self.assertEqual(p['current_progress'],75.0); self.assertEqual(p['manpower_totals']['planned_men'],6.0); self.assertEqual(p['manpower_totals']['actual_men'],7.0)

if __name__=='__main__': unittest.main(verbosity=2)
