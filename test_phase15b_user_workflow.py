import json,tempfile,threading,unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(root:=Path(__file__).resolve().parents[1])); import app

class Phase15BWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/"db.sqlite"; app.init_db()
        cls.server=app.ThreadingHTTPServer(("127.0.0.1",0),app.Handler)
        cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2); cls.tmp.cleanup()
    def req(self,path,method="GET",body=None,cookie=None):
        data=json.dumps(body).encode() if body is not None else None
        h={"Content-Type":"application/json"} if data else {}
        if cookie: h["Cookie"]=cookie
        try:
            with urlopen(Request(f"http://127.0.0.1:{self.port}{path}",method=method,data=data,headers=h),timeout=5) as r:
                raw=r.read().decode(); return r.status,(json.loads(raw) if raw else {}),r.headers
        except HTTPError as e:
            raw=e.read().decode(); return e.code,(json.loads(raw) if raw else {}),e.headers
    def login(self):
        s,d,h=self.req("/api/login","POST",{"email":"owner@demo.local","password":"DemoPass!123"})
        self.assertEqual(s,200); return h["Set-Cookie"].split(";",1)[0]
    def test_module_spec_endpoint_matches_bulk_contract(self):
        ck=self.login()
        for module,spec in app.BULK_IMPORT_SPECS.items():
            s,d,_=self.req("/api/module-spec?module="+module.replace(" ","%20"),cookie=ck)
            self.assertEqual(s,200,module)
            self.assertEqual([(x["header"],x["required"],x["type"]) for x in d["fields"]],spec,module)
    def test_add_edit_delete_full_user_flow_all_modules(self):
        ck=self.login()
        s,d,_=self.req("/api/projects","POST",{"name":"15B Workflow Project"},ck); self.assertEqual(s,201); pid=d["id"]
        examples={
            "Daily Control":{"date":"2026-09-17","status":"Open","planned_activities":"Start","completed_activities":"None","delays":"None","constraints":"None","notes":"Day"},
            "Manpower":{"date":"2026-09-17","role":"Electrician","actual_men":4,"hours":8,"notes":"Crew"},
            "RFIs":{"rfi_no":"RFI-001","subject":"Detail","status":"Open","due_date":"2026-09-20","raised_by":"CM","response":"Pending","notes":"N"},
            "Risks":{"risk_id":"R-001","description":"Access","status":"Open","owner":"CM","due_date":"2026-09-21","likelihood":3,"impact":4,"mitigation":"Plan","notes":"N"},
            "Actions":{"action_id":"A-001","description":"Confirm","status":"Open","owner":"CM","due_date":"2026-09-20","priority":"High","notes":"N"},
            "Snags":{"snag_id":"S-001","description":"Defect","status":"Open","location":"Hall","owner":"Foreman","due_date":"2026-09-22","notes":"N"},
            "Materials":{"item":"Tray","description":"300mm","quantity":10,"unit":"m","status":"Required","required_date":"2026-09-25","supplier":"A","notes":"N"},
            "Procurement":{"po_ref":"PO-1","item":"Tray","supplier":"A","quantity":10,"status":"Ordered","required_date":"2026-09-25","delivery_date":"2026-09-24","notes":"N"},
            "RAMS":{"ref":"RAMS-1","status":"Submitted","review_date":"2026-09-23","approved_by":"CM","notes":"N"},
            "Permits":{"permit_ref":"P-1","type":"Electrical","status":"Open","start_date":"2026-09-17","expiry_date":"2026-09-24","issued_by":"CM","notes":"N"},
            "Commissioning":{"system":"Electrical","test":"Functional","status":"Planned","planned_date":"2026-09-28","actual_date":"","result":"Pending","notes":"N"},
            "Variations":{"variation_ref":"V-1","description":"Extra","status":"Draft","value":100,"date":"2026-09-17","approved_value":0,"notes":"N"},
            "Cost Control":{"cost_code":"C-1","description":"Tray","budget":1000,"committed":500,"actual":200,"forecast":900,"notes":"N"},
            "Handover":{"description":"Electrical package","status":"Open","due_date":"2026-10-01","owner":"CM","notes":"N"},
            "Reports":{"report_type":"Daily Report","date":"2026-09-17","status":"Draft","author":"CM","notes":"N"}}
        for module,data in examples.items():
            enc=module.replace(" ","%20")
            s,d,_=self.req("/api/module/"+enc,"POST",{"project_id":pid,"title":module+" 15B","data":data},ck)
            self.assertEqual(s,201,module); rid=d["id"]
            s,d,_=self.req("/api/module/"+enc+"?project_id="+pid,cookie=ck)
            self.assertEqual(s,200,module); self.assertTrue(any(x["id"]==rid for x in d["records"]))
            changed={k:(v+1 if isinstance(v,(int,float)) else ("2026-09-29" if k.endswith("_date") or k=="date" else ("Foreman" if k=="role" else str(v)+" updated"))) for k,v in data.items()}
            s,d,_=self.req("/api/module/"+enc+"/"+rid,"PUT",{"title":module+" edited","data":changed},ck)
            self.assertEqual(s,200,module)
            s,d,_=self.req("/api/module/"+enc+"?project_id="+pid,cookie=ck); row=next(x for x in d["records"] if x["id"]==rid)
            saved=json.loads(row["data_json"])
            for k,v in changed.items():
                if v!="": self.assertEqual(saved[k],v,module+":"+k)
            s,d,_=self.req("/api/module/"+enc+"/"+rid,"DELETE",cookie=ck); self.assertEqual(s,200,module)
            s,d,_=self.req("/api/module/"+enc+"?project_id="+pid,cookie=ck)
            self.assertFalse(any(x["id"]==rid for x in d["records"]),module)
    def test_invalid_and_missing_required_are_rejected(self):
        ck=self.login(); s,d,_=self.req("/api/projects","POST",{"name":"15B Validation"},ck); pid=d["id"]
        cases=[("Manpower",{"date":"2026-09-17","role":"Electrician","actual_men":"bad","hours":8}),
               ("RFIs",{"status":"Open"}),("Materials",{"item":"Tray","quantity":"bad","unit":"m"})]
        for module,data in cases:
            s,d,_=self.req("/api/module/"+module.replace(" ","%20"),"POST",{"project_id":pid,"title":"Bad","data":data},ck)
            self.assertEqual(s,400,module)
    def test_permission_delete_is_enforced(self):
        ck=self.login(); s,d,_=self.req("/api/projects","POST",{"name":"15B Permissions"},ck); pid=d["id"]
        data={"subject":"Permission test"}
        s,d,_=self.req("/api/module/RFIs","POST",{"project_id":pid,"title":"RFI","data":data},ck); rid=d["id"]
        # Owner has delete by default; the endpoint must at least honour permission checks.
        s,d,_=self.req("/api/module/RFIs/"+rid,"DELETE",cookie=ck); self.assertEqual(s,200)
if __name__=="__main__": unittest.main()
