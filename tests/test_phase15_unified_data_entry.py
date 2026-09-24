import json,tempfile,threading,unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app

class UnifiedIndividualDataEntry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        app.DB_PATH=Path(cls.tmp.name)/'db.sqlite'
        app.init_db()
        cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2); cls.tmp.cleanup()
    def req(self,path,method='GET',body=None,cookie=None):
        data=json.dumps(body).encode() if body is not None else None
        r=Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=data,
                  headers={'Content-Type':'application/json'} if data else {})
        if cookie: r.add_header('Cookie',cookie)
        try:
            with urlopen(r,timeout=5) as x:
                return x.status,json.loads(x.read().decode()),x.headers
        except HTTPError as e:
            return e.code,json.loads(e.read().decode()),e.headers
    def login(self):
        s,_,h=self.req('/api/login','POST',{'email':'owner@demo.local','password':'DemoPass!123'})
        self.assertEqual(s,200); return h['Set-Cookie'].split(';',1)[0]

    def test_bulk_spec_and_individual_spec_are_identical(self):
        ck=self.login()
        for module,spec in app.BULK_IMPORT_SPECS.items():
            s,d,_=self.req('/api/module-spec?module='+module.replace(' ','%20'),cookie=ck)
            self.assertEqual(s,200,module)
            returned=[(x['header'],x['required'],x['type']) for x in d['fields']]
            self.assertEqual(returned,spec,module)

    def test_all_modules_individual_add_edit_readback(self):
        ck=self.login()
        s,b,_=self.req('/api/projects','POST',{'name':'Unified Data Entry Project'},ck)
        self.assertEqual(s,201); pid=b['id']

        examples={
            "Daily Control":{"date":"2026-09-17","status":"Open","planned_activities":"Start","completed_activities":"None","delays":"None","constraints":"None","notes":"Day 1"},
            "Manpower":{"date":"2026-09-17","role":"Electrician","planned_men":4,"actual_men":3,"hours":8,"notes":"Crew"},
            "RFIs":{"rfi_no":"RFI-001","subject":"Containment detail","status":"Open","due_date":"2026-09-20","raised_by":"CM","response":"Pending","notes":"Test"},
            "Risks":{"risk_id":"R-001","description":"Access constraint","status":"Open","owner":"CM","due_date":"2026-09-21","likelihood":3,"impact":4,"mitigation":"Plan access","notes":"Test"},
            "Actions":{"action_id":"A-001","description":"Confirm delivery","status":"Open","owner":"CM","due_date":"2026-09-20","priority":"High","notes":"Test"},
            "Snags":{"snag_id":"S-001","description":"Minor defect","status":"Open","location":"Hall 1","owner":"Foreman","due_date":"2026-09-22","notes":"Test"},
            "Materials":{"item":"Cable tray","description":"300mm tray","quantity":120,"unit":"m","status":"Required","required_date":"2026-09-25","supplier":"Supplier A","notes":"Test"},
            "Procurement":{"po_ref":"PO-001","item":"Cable tray","supplier":"Supplier A","quantity":120,"status":"Ordered","required_date":"2026-09-25","delivery_date":"2026-09-24","notes":"Test"},
            "RAMS":{"ref":"RAMS-001","status":"Submitted","review_date":"2026-09-23","approved_by":"CM","notes":"Test"},
            "Permits":{"permit_ref":"P-001","type":"Electrical","status":"Open","start_date":"2026-09-17","expiry_date":"2026-09-24","issued_by":"CM","notes":"Test"},
            "Commissioning":{"system":"Electrical","test":"Functional test","status":"Planned","planned_date":"2026-09-28","actual_date":"","result":"Pending","notes":"Test"},
            "Variations":{"variation_ref":"V-001","description":"Additional works","status":"Draft","value":1250,"date":"2026-09-17","approved_value":0,"notes":"Test"},
            "Cost Control":{"cost_code":"C-001","description":"Containment","budget":10000,"committed":5000,"actual":2500,"forecast":9000,"notes":"Test"},
            "Handover":{"description":"Electrical package","status":"Open","due_date":"2026-10-01","owner":"CM","notes":"Test"},
            "Reports":{"report_type":"Daily Report","date":"2026-09-17","status":"Draft","author":"CM","notes":"Test"},
        }
        for module,data in examples.items():
            s,b,_=self.req('/api/module/'+module.replace(' ','%20'),'POST',
                           {'project_id':pid,'title':module+' Entry','data':data},ck)
            self.assertEqual(s,201,module)
            rid=b['id']
            s,b,_=self.req('/api/module/'+module.replace(' ','%20')+'?project_id='+pid,cookie=ck)
            self.assertEqual(s,200,module)
            row=next(x for x in b['records'] if x['id']==rid)
            saved=json.loads(row['data_json'])
            for k,v in data.items():
                if v!='':
                    self.assertEqual(saved[k],v,module+":"+k)
            changed=dict(data)
            # Change every populated field to prove Edit uses the same schema.
            for k,v in list(changed.items()):
                if isinstance(v,(int,float)): changed[k]=float(v)+1
                elif k.endswith('_date') or k=="date": changed[k]="2026-09-29"
                elif k=="role": changed[k]="Foreman"
                else: changed[k]=str(v)+" updated"
            s,b,_=self.req('/api/module/'+module.replace(' ','%20')+'/'+rid,'PUT',
                           {'title':module+' Edited','data':changed},ck)
            self.assertEqual(s,200,module)
            s,b,_=self.req('/api/module/'+module.replace(' ','%20')+'?project_id='+pid,cookie=ck)
            row=next(x for x in b['records'] if x['id']==rid); saved=json.loads(row['data_json'])
            for k,v in changed.items():
                if v!='': self.assertEqual(saved[k],v,module+" edit:"+k)

    def test_required_fields_are_rejected_for_each_module(self):
        ck=self.login()
        s,b,_=self.req('/api/projects','POST',{'name':'Required Field Project'},ck)
        self.assertEqual(s,201); pid=b['id']
        for module,spec in app.BULK_IMPORT_SPECS.items():
            required=[h for h,req,_ in spec if req and h!="Title"]
            if not required: continue
            data={}
            # Deliberately omit the first required non-title field.
            for h,req,typ in spec:
                if h=="Title" or not req: continue
                if h==required[0]: continue
                data[app.import_data_key(h)]="x"
            s,b,_=self.req('/api/module/'+module.replace(' ','%20'),'POST',
                           {'project_id':pid,'title':'Missing required','data':data},ck)
            self.assertEqual(s,400,module)
            self.assertIn(required[0],str(b),module)

if __name__=="__main__": unittest.main()
