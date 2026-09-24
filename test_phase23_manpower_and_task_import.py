
import json,tempfile,threading,unittest,io,zipfile
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app

class Phase23ManpowerAndTaskImport(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/'db.sqlite'; app.init_db()
  cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler); cls.port=cls.server.server_address[1]
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
 @classmethod
 def tearDownClass(cls): cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2);cls.tmp.cleanup()
 def req(self,path,method='GET',body=None,cookie=None,raw=None,headers=None):
  data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None); h=headers or ({'Content-Type':'application/json'} if body is not None else {})
  if cookie:h['Cookie']=cookie
  try:
   with urlopen(Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=data,headers=h),timeout=5) as r:return r.status,json.loads(r.read().decode()),r.headers
  except HTTPError as e:return e.code,json.loads(e.read().decode()),e.headers
 def login(self):
  s,d,h=self.req('/api/login','POST',{'email':'owner@demo.local','password':'DemoPass!123'}); self.assertEqual(s,200); return h['Set-Cookie'].split(';',1)[0]
 def make_xlsx(self,rows):
  def col(n):
   z=''
   while n:z=chr(65+(n-1)%26)+z;n=(n-1)//26
   return z
  def sheet(vals):
   rr=[]
   for r,row in enumerate(vals,1):
    cells=''.join(f'<c r="{col(c)}{r}" t="inlineStr"><is><t>{app.xml_escape(v)}</t></is></c>' for c,v in enumerate(row,1));rr.append(f'<row r="{r}">{cells}</row>')
   return f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(rr)}</sheetData></worksheet>'
  ct='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
  rel='<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
  wb='<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Template" sheetId="1" r:id="rId1"/></sheets></workbook>'
  wr='<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
  b=io.BytesIO()
  with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
   for n,v in {'[Content_Types].xml':ct,'_rels/.rels':rel,'xl/workbook.xml':wb,'xl/_rels/workbook.xml.rels':wr,'xl/worksheets/sheet1.xml':sheet(rows)}.items():z.writestr(n,v)
  return b.getvalue()
 def multipart(self,ck,plan,raw):
  boundary='----CC23TEST'; body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="tasks.xlsx"\r\nContent-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n'.encode()+raw+f'\r\n--{boundary}--\r\n'.encode())
  return self.req('/api/task-import?plan_id='+plan,'POST',cookie=ck,raw=body,headers={'Content-Type':f'multipart/form-data; boundary={boundary}'})
 def test_project_manloader_is_set_at_project_setup(self):
  ck=self.login(); s,d,_=self.req('/api/projects','POST',{'name':'Manloader Project','manloader':16},ck); self.assertEqual(s,201); pid=d['id']
  s,d,_=self.req('/api/projects',cookie=ck); p=next(x for x in d['projects'] if x['id']==pid); self.assertEqual(float(p['manloader']),16.0)
  s,d,_=self.req('/api/projects/'+pid,'PUT',{'name':'Manloader Project','manloader':18},ck); self.assertEqual(s,200)
  s,d,_=self.req('/api/projects/'+pid,cookie=ck); self.assertEqual(float(d['project']['manloader']),18.0)
 def test_daily_manpower_uses_actual_men_only(self):
  ck=self.login(); s,d,_=self.req('/api/projects','POST',{'name':'Daily Actual Project','manloader':12},ck); pid=d['id']
  s,d,_=self.req('/api/module/Manpower','POST',{'project_id':pid,'title':'18 Sep','data':{'date':'2026-09-18','role':'Electrician','actual_men':9,'hours':8}},ck); self.assertEqual(s,201)
  s,d,_=self.req('/api/module-spec?module=Manpower',cookie=ck); self.assertEqual(s,200); self.assertEqual([x['header'] for x in d['fields']],['Title','Date','Role','Actual Men','Hours','Notes'])
  s,d,_=self.req('/api/project-overview?project_id='+pid,cookie=ck); self.assertEqual(s,200); self.assertEqual(d['project']['manloader'],12); self.assertEqual(d['kpis']['actual_men'],9.0)
 def test_task_template_matches_connected_task_contract(self):
  ck=self.login(); s,d,_=self.req('/api/projects','POST',{'name':'Task Contract'},ck); pid=d['id']; s,d,_=self.req('/api/plans','POST',{'project_id':pid,'name':'Programme'},ck); plan=d['id']
  r=urlopen(Request(f'http://127.0.0.1:{self.port}/api/task-import/templates?plan_id={plan}',headers={'Cookie':ck}),timeout=5); rows=app.parse_xlsx_rows(r.read()); self.assertEqual(rows[0],app.TASK_IMPORT_HEADERS); self.assertEqual(rows[0],['Task ID','Task','Start Date','Duration (working days)','Status','% Complete','Planned Men','Notes'])
 def test_task_import_rejects_status_progress_mismatch_atomically(self):
  ck=self.login(); s,d,_=self.req('/api/projects','POST',{'name':'Task Validation'},ck); pid=d['id']; s,d,_=self.req('/api/plans','POST',{'project_id':pid,'name':'Programme'},ck); plan=d['id']
  rows=[app.TASK_IMPORT_HEADERS,['T1','Good','2026-09-21','2','Not Started','0','3',''],['T2','Bad','2026-09-23','2','Finished','50','3','']]
  s,d,_=self.multipart(ck,plan,self.make_xlsx(rows)); self.assertEqual(s,400); self.assertTrue(any('100%' in e for e in d['errors']))
  s,d,_=self.req('/api/tasks?project_id='+pid+'&plan_id='+plan,cookie=ck); self.assertEqual(len(d['tasks']),0)
 def test_task_import_rejects_existing_id_and_invalid_duration(self):
  ck=self.login(); s,d,_=self.req('/api/projects','POST',{'name':'Task Duplicate'},ck); pid=d['id']; s,d,_=self.req('/api/plans','POST',{'project_id':pid,'name':'Programme'},ck); plan=d['id']
  rows=[app.TASK_IMPORT_HEADERS,['T1','Existing','2026-09-21','1','Not Started','0','2','']]; self.assertEqual(self.multipart(ck,plan,self.make_xlsx(rows))[0],201)
  rows=[app.TASK_IMPORT_HEADERS,['T1','Duplicate','2026-09-22','1','Not Started','0','2',''],['T2','Bad duration','2026-09-22','0','Not Started','0','2','']]
  s,d,_=self.multipart(ck,plan,self.make_xlsx(rows)); self.assertEqual(s,400); self.assertTrue(any('already exists' in e or 'at least 1' in e for e in d['errors']))
  s,d,_=self.req('/api/tasks?project_id='+pid+'&plan_id='+plan,cookie=ck); self.assertEqual(len(d['tasks']),1)

 def test_manpower_bulk_template_is_actual_only_and_imports(self):
  ck=self.login(); s,d,_=self.req('/api/projects','POST',{'name':'Manpower Bulk','manloader':20},ck); self.assertEqual(s,201); pid=d['id']
  r=urlopen(Request(f'http://127.0.0.1:{self.port}/api/bulk-import/templates?module=Manpower',headers={'Cookie':ck}),timeout=5); rows=app.parse_xlsx_rows(r.read()); self.assertEqual(rows[0],['Title','Date','Role','Actual Men','Hours','Notes'])
  raw=self.make_xlsx([rows[0],['Day 1','2026-09-18','Electrician','7','8','Actual onsite']])
  boundary='----CC23MP'; body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="manpower.xlsx"\r\nContent-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n'.encode()+raw+f'\r\n--{boundary}--\r\n'.encode())
  s,d,_=self.req('/api/bulk-import?project_id='+pid+'&module=Manpower','POST',cookie=ck,raw=body,headers={'Content-Type':f'multipart/form-data; boundary={boundary}'}); self.assertEqual(s,201); self.assertEqual(d['rows_imported'],1)
  s,d,_=self.req('/api/project-overview?project_id='+pid,cookie=ck); self.assertEqual(s,200); self.assertEqual(d['project']['manloader'],20); self.assertEqual(d['kpis']['actual_men'],7.0)

if __name__=='__main__': unittest.main()
