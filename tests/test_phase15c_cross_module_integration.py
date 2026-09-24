import json,tempfile,threading,unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app

class Phase15CCrossModuleIntegration(unittest.TestCase):
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
        if cookie:h['Cookie']=cookie
        try:
            with urlopen(Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=data,headers=h),timeout=5) as r:
                raw=r.read().decode(); return r.status,(json.loads(raw) if raw else {}),r.headers
        except HTTPError as e:
            raw=e.read().decode(); return e.code,(json.loads(raw) if raw else {}),e.headers
    def login(self):
        s,d,h=self.req('/api/login','POST',{'email':'owner@demo.local','password':'DemoPass!123'}); self.assertEqual(s,200); return h['Set-Cookie'].split(';',1)[0]
    def add(self,ck,pid,module,title,data):
        s,d,_=self.req('/api/module/'+module.replace(' ','%20'),'POST',{'project_id':pid,'title':title,'data':data},ck); self.assertEqual(s,201,module); return d['id']

    def test_live_entry_flows_into_dashboard_and_management(self):
        ck=self.login(); s,d,_=self.req('/api/projects','POST',{'name':'15C Integration'},ck); self.assertEqual(s,201); pid=d['id']
        self.add(ck,pid,'Daily Control','Daily',{'date':'2026-09-17','status':'Open','planned_activities':'Start','completed_activities':'None','delays':'Plant','constraints':'Access','notes':'Live'})
        self.add(ck,pid,'Manpower','Crew',{'date':'2026-09-17','role':'Electrician','planned_men':5,'actual_men':4,'hours':8,'notes':'Live'})
        self.add(ck,pid,'RFIs','Open RFI',{'rfi_no':'RFI-15C','subject':'Detail','status':'Open','due_date':'2026-09-16','raised_by':'CM','response':'Pending','notes':'Late'})
        self.add(ck,pid,'Risks','Open Risk',{'risk_id':'R-15C','description':'Access','status':'Open','owner':'CM','due_date':'2026-09-16','likelihood':4,'impact':5,'mitigation':'Control','notes':'Critical'})
        self.add(ck,pid,'Actions','Open Action',{'action_id':'A-15C','description':'Close item','status':'Open','owner':'CM','due_date':'2026-09-16','priority':'High','notes':'Late'})
        self.add(ck,pid,'Snags','Open Snag',{'snag_id':'S-15C','description':'Defect','status':'Open','location':'Hall','owner':'Foreman','due_date':'2026-09-16','notes':'Late'})
        s,db,_=self.req('/api/dashboard',cookie=ck); self.assertEqual(s,200)
        p=next(x for x in db['project_summary'] if x['project_id']==pid)
        self.assertEqual(p['records'],6); self.assertEqual(p['kpis']['rfis'],1); self.assertEqual(p['kpis']['risks'],1); self.assertEqual(p['kpis']['actions'],1); self.assertEqual(p['kpis']['snags'],1)
        self.assertEqual(p['manpower']['planned_men'],5); self.assertEqual(p['manpower']['actual_men'],4); self.assertEqual(p['manpower']['man_hours'],32)
        s,m,_=self.req('/api/management?as_of=2026-09-17',cookie=ck); self.assertEqual(s,200)
        mp=next(x for x in m['projects'] if x['project_id']==pid)
        self.assertEqual(mp['manpower_today']['planned_men'],5); self.assertEqual(mp['manpower_today']['actual_men'],4); self.assertEqual(mp['manpower_today']['man_hours'],32)
        overdue=[x for x in m['issues'] if x['project_id']==pid and x['kind']=='Overdue control item']
        self.assertEqual(len(overdue),4)
        self.assertEqual(m['totals']['overdue_items'],4)

    def test_programme_update_flows_into_gantt_comparison_and_integration(self):
        ck=self.login(); s,d,_=self.req('/api/projects','POST',{'name':'15C Programme'},ck); pid=d['id']
        s,d,_=self.req('/api/plans','POST',{'project_id':pid,'name':'Live Programme'},ck); self.assertEqual(s,201); plan=d['id']
        s,d,_=self.req(f'/api/plans/{plan}/tasks','POST',{'name':'Activity A','start_date':'2026-09-17','finish_date':'2026-09-21','percent_complete':0,'planned_men':3,'milestone':False},ck); self.assertEqual(s,201); tid=d['id']
        self.req(f'/api/plans/{plan}/baseline','POST',{},ck)
        s,d,_=self.req(f'/api/plans/{plan}/update','POST',{'tasks':[{'id':tid,'percent_complete':60,'actual_start':'2026-09-17'}]},ck); self.assertEqual(s,200)
        s,g,_=self.req(f'/api/plans/{plan}/gantt',cookie=ck); self.assertEqual(s,200); task=next(x for x in g['tasks'] if x['id']==tid); self.assertEqual(task['percent_complete'],60)
        s,c,_=self.req(f'/api/plans/{plan}/comparison',cookie=ck); self.assertEqual(s,200); self.assertEqual(c['programme_progress'],60.0); self.assertEqual(c['baseline_finish'],'2026-09-21'); self.assertEqual(c['current_finish'],'2026-09-21')
        s,i,_=self.req(f'/api/plans/{plan}/integration',cookie=ck); self.assertEqual(s,200); self.assertEqual(i['programme_progress'],60.0); self.assertIn('tasks',i); self.assertEqual(i['tasks'][0]['percent_complete'],60)

    def test_programme_progress_and_manpower_remain_consistent_after_data_change(self):
        ck=self.login(); s,d,_=self.req('/api/projects','POST',{'name':'15C Consistency'},ck); pid=d['id']
        s,d,_=self.req('/api/plans','POST',{'project_id':pid,'name':'Programme'},ck); plan=d['id']
        for name,start,finish,pct,men in [('A','2026-09-17','2026-09-18',0,2),('B','2026-09-21','2026-09-25',0,4)]:
            self.assertEqual(self.req(f'/api/plans/{plan}/tasks','POST',{'name':name,'start_date':start,'finish_date':finish,'percent_complete':pct,'planned_men':men},ck)[0],201)
        self.add(ck,pid,'Manpower','Crew A',{'date':'2026-09-17','role':'Electrician','planned_men':2,'actual_men':1,'hours':8,'notes':'A'})
        self.add(ck,pid,'Manpower','Crew B',{'date':'2026-09-18','role':'4th Year','planned_men':3,'actual_men':3,'hours':7,'notes':'B'})
        s,i,_=self.req(f'/api/plans/{plan}/integration',cookie=ck); self.assertEqual(s,200)
        self.assertEqual(i['manpower']['total_planned_men_entries'],5); self.assertEqual(i['manpower']['total_actual_men_entries'],4)
        # Change a manpower entry through the same user endpoint and verify integration rereads persisted state.
        s,rows,_=self.req('/api/module/Manpower?project_id='+pid,cookie=ck); self.assertEqual(s,200); row=next(x for x in rows['records'] if x['title']=='Crew B'); rid=row['id']
        changed=json.loads(row['data_json']); changed['actual_men']=2
        s,_,_=self.req('/api/module/Manpower/'+rid,'PUT',{'title':'Crew B edited','data':changed},ck); self.assertEqual(s,200)
        s,i,_=self.req(f'/api/plans/{plan}/integration',cookie=ck); self.assertEqual(s,200); self.assertEqual(i['manpower']['total_actual_men_entries'],3)

    def test_historical_as_of_does_not_turn_future_due_dates_into_overdue(self):
        ck=self.login(); s,d,_=self.req('/api/projects','POST',{'name':'15C History'},ck); pid=d['id']
        self.add(ck,pid,'RFIs','Future RFI',{'rfi_no':'RFI-F','subject':'Future','status':'Open','due_date':'2026-09-20','raised_by':'CM','response':'Pending','notes':'Future'})
        s,m,_=self.req('/api/management?as_of=2026-09-19',cookie=ck); self.assertEqual(s,200); self.assertEqual(m['totals']['overdue_items'],0)
        s,m,_=self.req('/api/management?as_of=2026-09-21',cookie=ck); self.assertEqual(s,200); self.assertEqual(m['totals']['overdue_items'],1)
        s,m,_=self.req('/api/management?as_of=bad-date',cookie=ck); self.assertEqual(s,400)

    def test_cross_project_records_do_not_leak_into_plan_integration(self):
        ck=self.login();
        s,d,_=self.req('/api/projects','POST',{'name':'Project One'},ck); p1=d['id']
        s,d,_=self.req('/api/projects','POST',{'name':'Project Two'},ck); p2=d['id']
        s,d,_=self.req('/api/plans','POST',{'project_id':p1,'name':'P1 Plan'},ck); plan=d['id']
        self.req(f'/api/plans/{plan}/tasks','POST',{'name':'P1 Task','start_date':'2026-09-17','finish_date':'2026-09-17','percent_complete':100,'planned_men':1},ck)
        self.add(ck,p2,'Manpower','P2 Crew',{'date':'2026-09-17','role':'Electrician','planned_men':99,'actual_men':99,'hours':10,'notes':'Other project'})
        s,i,_=self.req(f'/api/plans/{plan}/integration',cookie=ck); self.assertEqual(s,200); self.assertEqual(i['manpower']['total_planned_men_entries'],0); self.assertEqual(i['manpower']['total_actual_men_entries'],0)

if __name__=='__main__': unittest.main(verbosity=2)
