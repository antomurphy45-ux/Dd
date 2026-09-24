import base64, json, threading, tempfile, unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import quote
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app

class E2ESampleProject(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/'db.sqlite'; app.init_db()
        cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler); cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls): cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2); cls.tmp.cleanup()
    def req(self,path,method='GET',body=None,cookie=None):
        data=json.dumps(body).encode() if body is not None else None
        r=Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=data,headers={'Content-Type':'application/json'} if data else {})
        if cookie:r.add_header('Cookie',cookie)
        try:
            with urlopen(r,timeout=5) as x: return x.status, json.loads(x.read().decode()), x.headers
        except HTTPError as e: return e.code, json.loads(e.read().decode()), e.headers
    def login(self,email='owner@demo.local'):
        s,b,h=self.req('/api/login','POST',{'email':email,'password':'DemoPass!123'}); self.assertEqual(s,200); return h['Set-Cookie'].split(';',1)[0]
    def test_day_1_to_completion(self):
        ck=self.login()
        # Day 1: create a fresh project.
        s,b,_=self.req('/api/projects','POST',{'name':'E2E Sample Data Centre','level_id':'L3'},ck); self.assertEqual(s,201); pid=b['id']
        # Daily control and manpower.
        for module,title,data in [
            ('Daily Control','Day 1 Site Start',{'date':'2026-09-01','status':'Open','planned_activities':'Mobilise','completed_activities':'Induction','delays':'None'}),
            ('Manpower','Day 1 Labour',{'date':'2026-09-01','role':'Electrician','planned_men':4,'actual_men':4,'hours':9}),
            ('RFIs','RFI-001',{'rfi_no':'RFI-001','subject':'Containment detail'}),
            ('Risks','Risk-001',{'risk_id':'Risk-001','description':'Access constraint','likelihood':3,'impact':3}),
            ('Actions','ACT-001',{'action_id':'ACT-001','description':'Confirm delivery','owner':'Project Manager'}),
            ('Snags','SNAG-001',{'snag_id':'SNAG-001','description':'Minor snag','status':'Open'}),
            ('Materials','MAT-001',{'item':'Cable tray','quantity':120,'unit':'m'}),
            ('Procurement','PO-001',{'po_ref':'PO-001','item':'Cable tray','supplier':'Demo Supplier','status':'Ordered'}),
            ('RAMS','RAMS-001',{'ref':'RAMS-001','status':'Submitted'}),
            ('Permits','PERMIT-001',{'permit_ref':'PERMIT-001','type':'Electrical','status':'Open'}),
            ('Commissioning','TEST-001',{'system':'Electrical','test':'Functional test','status':'Planned'}),
            ('Variations','VAR-001',{'variation_ref':'VAR-001','description':'Demo variation','status':'Draft'}),
            ('Cost Control','COST-001',{'cost_code':'COST-001','description':'Demo cost','budget':100000,'forecast':100000}),
            ('Handover','HO-001',{'description':'Electrical handover','status':'Open'}),
        ]:
            s,b,_=self.req('/api/module/'+quote(module, safe=''),'POST',{'project_id':pid,'title':title,'data':data},ck); self.assertEqual(s,201,module); locals()[module.replace(' ','_')]=b['id']
        # Document attached to the RFI.
        rfi_id=self.req('/api/module/RFIs?project_id='+pid,cookie=ck)[1]['records'][0]['id']
        content=base64.b64encode(b'Day 1 sample drawing').decode()
        s,b,_=self.req('/api/attachments','POST',{'project_id':pid,'record_id':rfi_id,'filename':'drawing.pdf','mime_type':'application/pdf','content_base64':content},ck); self.assertEqual(s,201)
        # Programme: mobilisation -> containment -> test -> handover.
        s,b,_=self.req('/api/plans','POST',{'project_id':pid,'name':'Main Construction Programme'},ck); self.assertEqual(s,201); plan=b['id']
        tasks=[]
        for name,start,finish,pred,pct,men in [
            ('Mobilisation','2026-09-01','2026-09-03',None,100,4),
            ('Containment Installation','2026-09-04','2026-09-10',None,100,6),
            ('Testing & Commissioning','2026-09-11','2026-09-12',None,100,3),
            ('Handover','2026-09-13','2026-09-14',None,100,2),
        ]:
            payload={'name':name,'start_date':start,'finish_date':finish,'percent_complete':pct,'planned_men':men}
            if tasks: payload['predecessor_id']=tasks[-1]
            s,b,_=self.req(f'/api/plans/{plan}/tasks','POST',payload,ck); self.assertEqual(s,201,name); tasks.append(b['id'])
        s,g,_=self.req(f'/api/plans/{plan}/gantt',cookie=ck); self.assertEqual(s,200); self.assertEqual(len(g['tasks']),4); self.assertTrue(any(t['critical'] for t in g['tasks']))
        # Programme performance history and live update layer.
        s,b,_=self.req(f'/api/plans/{plan}/update','POST',{'update_date':'2026-09-07','note':'Mid-programme update','tasks':[{'id':tasks[0],'percent_complete':100},{'id':tasks[1],'percent_complete':50},{'id':tasks[2],'percent_complete':0},{'id':tasks[3],'percent_complete':0}]},ck); self.assertEqual(s,200)
        s,b,_=self.req(f'/api/plans/{plan}/update','POST',{'update_date':'2026-09-14','note':'Completion update','tasks':[{'id':tasks[0],'percent_complete':100,'actual_start':'2026-09-01','actual_finish':'2026-09-03'},{'id':tasks[1],'percent_complete':100,'actual_start':'2026-09-04','actual_finish':'2026-09-10'},{'id':tasks[2],'percent_complete':100,'actual_start':'2026-09-11','actual_finish':'2026-09-12'},{'id':tasks[3],'percent_complete':100,'actual_start':'2026-09-13','actual_finish':'2026-09-14'}]},ck); self.assertEqual(s,200)
        s,h,_=self.req(f'/api/plans/{plan}/updates',cookie=ck); self.assertEqual(s,200); self.assertEqual(len(h['updates']),2)
        s,p,_=self.req(f'/api/plans/{plan}/performance',cookie=ck); self.assertEqual(s,200); self.assertEqual(p['update_count'],2); self.assertEqual(p['current_progress'],100.0); self.assertGreaterEqual(p['manpower_totals']['actual_men'],4.0)
        # Request approval and complete it as the same administrator.
        s,w,_=self.req('/api/workflows','POST',{'project_id':pid,'module':'RFIs','record_id':rfi_id,'approver_user_id':'U1'},ck); self.assertEqual(s,201)
        wid=w['id']; s,decision,_=self.req('/api/workflows/'+wid,'PUT',{'decision':'Approved','note':'Approved in sample E2E'},ck); self.assertEqual(s,200); self.assertEqual(decision['status'],'Approved')
        # Final dashboard and audit trail.
        s,d,_=self.req('/api/dashboard',cookie=ck); self.assertEqual(s,200); self.assertTrue(any(x['id']==pid for x in d['projects']))
        s,a,_=self.req('/api/audit',cookie=ck); self.assertEqual(s,200); actions=[x['action'] for x in a['audit']]; self.assertIn('PLAN_CREATE',actions); self.assertIn('APPROVAL_APPROVED',actions)
        # Verify persistence directly after all work.
        c=app.db(); self.assertEqual(c.execute('select count(*) from module_records where project_id=?',(pid,)).fetchone()[0],14); self.assertEqual(c.execute('select count(*) from plan_tasks where plan_id=?',(plan,)).fetchone()[0],4); self.assertEqual(c.execute('select status from workflows where id=?',(wid,)).fetchone()[0],'Approved'); c.close()

if __name__=='__main__': unittest.main(verbosity=2)
