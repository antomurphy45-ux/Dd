
import json,tempfile,threading,unittest,io,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app

class Phase21Tasks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/'db.sqlite'; app.init_db()
        cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler); cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2);cls.tmp.cleanup()
    def req(self,path,method='GET',body=None,cookie=None,raw=None,headers=None):
        data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        h={'Content-Type':'application/json'} if body is not None else {}
        if headers:h.update(headers)
        if cookie:h['Cookie']=cookie
        try:
            with urlopen(Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=data,headers=h),timeout=5) as r:return r.status,json.loads(r.read().decode()),r.headers
        except HTTPError as e:return e.code,json.loads(e.read().decode()),e.headers
    def login(self,email='owner@demo.local'):
        s,d,h=self.req('/api/login','POST',{'email':email,'password':'DemoPass!123'});self.assertEqual(s,200);return h['Set-Cookie'].split(';',1)[0]
    def setup_plan(self,ck):
        s,d,_=self.req('/api/projects','POST',{'name':'Task Project'},ck);self.assertEqual(s,201);pid=d['id']
        s,d,_=self.req('/api/plans','POST',{'project_id':pid,'name':'Main Programme'},ck);self.assertEqual(s,201)
        return pid,d['id']
    def make_xlsx(self,rows):
        def xcol(n):
            s=''
            while n:s=chr(65+(n-1)%26)+s;n=(n-1)//26
            return s
        def sh(vals):
            out=[]
            for r,row in enumerate(vals,1):
                cells=''.join(f'<c r="{xcol(c)}{r}" t="inlineStr"><is><t>{app.xml_escape(v)}</t></is></c>' for c,v in enumerate(row,1))
                out.append(f'<row r="{r}">{cells}</row>')
            return '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+''.join(out)+'</sheetData></worksheet>'
        ct='<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
        rel='<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
        wb='<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Template" sheetId="1" r:id="rId1"/></sheets></workbook>'
        wr='<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
            for n,v in {'[Content_Types].xml':ct,'_rels/.rels':rel,'xl/workbook.xml':wb,'xl/_rels/workbook.xml.rels':wr,'xl/worksheets/sheet1.xml':sh(rows)}.items():z.writestr(n,v)
        return b.getvalue()
    def multipart(self,ck,plan,filename,raw):
        boundary='----CC21TEST'
        body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n'.encode()+raw+f'\r\n--{boundary}--\r\n'.encode())
        return self.req('/api/task-import?plan_id='+plan,'POST',cookie=ck,raw=body,headers={'Content-Type':f'multipart/form-data; boundary={boundary}'})
    def test_task_lifecycle_and_overall_progress(self):
        ck=self.login();pid,plan=self.setup_plan(ck)
        s,d,_=self.req('/api/tasks','POST',{'project_id':pid,'plan_id':plan,'name':'Containment','start_date':'2026-09-21','duration_working_days':3,'status':'Not Started'},ck);self.assertEqual(s,201);tid=d['id']
        s,d,_=self.req('/api/tasks','POST',{'project_id':pid,'plan_id':plan,'name':'First Fix','start_date':'2026-09-24','duration_working_days':2,'status':'Finished'},ck);self.assertEqual(s,201)
        s,d,_=self.req(f'/api/tasks/{tid}','PUT',{'project_id':pid,'status':'Started'},ck);self.assertEqual(s,200);self.assertEqual(d['percent_complete'],1)
        s,d,_=self.req('/api/tasks?project_id='+pid+'&plan_id='+plan,cookie=ck);self.assertEqual(s,200);self.assertEqual(d['counts']['Started'],1);self.assertEqual(d['counts']['Finished'],1);self.assertEqual(d['overall_progress'],50.5)
    def test_bulk_task_import_calculates_working_day_finish(self):
        ck=self.login();pid,plan=self.setup_plan(ck)
        rows=[app.TASK_IMPORT_HEADERS,['T-1','Cable install','2026-09-21','3','Not Started','0','4',''],['T-2','Testing','2026-09-24','2','Finished','0','2','']]
        s,d,_=self.multipart(ck,plan,'tasks.xlsx',self.make_xlsx(rows));self.assertEqual(s,201);self.assertEqual(d['rows_imported'],2)
        s,d,_=self.req('/api/tasks?project_id='+pid+'&plan_id='+plan,cookie=ck);self.assertEqual(s,200)
        self.assertEqual([(x['activity_id'],x['finish_date'],x['status']) for x in d['tasks']],[('T-1','2026-09-23','Not Started'),('T-2','2026-09-25','Finished')])
    def test_bulk_is_atomic_on_invalid_status(self):
        ck=self.login();pid,plan=self.setup_plan(ck)
        rows=[app.TASK_IMPORT_HEADERS,['T-1','Good','2026-09-21','2','Not Started','0','1',''],['T-2','Bad','2026-09-23','2','Paused','0','1','']]
        s,d,_=self.multipart(ck,plan,'bad.xlsx',self.make_xlsx(rows));self.assertEqual(s,400)
        s,d,_=self.req('/api/tasks?project_id='+pid+'&plan_id='+plan,cookie=ck);self.assertEqual(len(d['tasks']),0)
    def test_task_template_download(self):
        ck=self.login();pid,plan=self.setup_plan(ck)
        r=urlopen(Request(f'http://127.0.0.1:{self.port}/api/task-import/templates?plan_id={plan}',headers={'Cookie':ck}),timeout=5)
        raw=r.read(); self.assertEqual(r.status,200); self.assertEqual(r.headers.get_content_type(),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'); self.assertGreater(len(raw),500)
    def test_task_cross_project_idor_rejected(self):
        ck=self.login();pid,plan=self.setup_plan(ck);s,d,_=self.req('/api/tasks','POST',{'project_id':pid,'plan_id':plan,'name':'Task','start_date':'2026-09-21','duration_working_days':1},ck);tid=d['id']
        s,d,_=self.req('/api/projects','POST',{'name':'Other'},ck);other=d['id']
        s,d,_=self.req(f'/api/tasks/{tid}','PUT',{'project_id':other,'status':'Finished'},ck);self.assertEqual(s,404)
        # The supplied project id is ignored for locating the task, but access is still constrained to its real project.
        s,d,_=self.req('/api/tasks?project_id='+other+'&plan_id='+plan,cookie=ck);self.assertEqual(s,404)

if __name__=='__main__':unittest.main()
