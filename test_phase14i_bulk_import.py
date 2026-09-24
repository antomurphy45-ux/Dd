import json,tempfile,threading,unittest,uuid
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app

class Phase14IBulkImport(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/'db.sqlite'; app.init_db()
  cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler); cls.port=cls.server.server_address[1]
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
 @classmethod
 def tearDownClass(cls): cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2);cls.tmp.cleanup()
 def req(self,path,method='GET',body=None,cookie=None,headers=None):
  h=headers or {}; data=body
  r=Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=data,headers=h)
  if cookie:r.add_header('Cookie',cookie)
  try:
   with urlopen(r,timeout=5) as x:return x.status,x.read(),x.headers
  except HTTPError as e:return e.code,e.read(),e.headers
 def login(self):
  s,b,h=self.req('/api/login','POST',json.dumps({'email':'owner@demo.local','password':'DemoPass!123'}).encode(),headers={'Content-Type':'application/json'}); self.assertEqual(s,200); return h['Set-Cookie'].split(';',1)[0]
 def multipart(self,filename,data):
  boundary='----CC'+uuid.uuid4().hex
  body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n'.encode()+data+f'\r\n--{boundary}--\r\n'.encode())
  return body,{'Content-Type':f'multipart/form-data; boundary={boundary}'}
 def test_template_round_trip_and_live_dashboard_change(self):
  ck=self.login(); s,b,_=self.req('/api/projects','POST',json.dumps({'name':'Bulk Import Project'}).encode(),ck,{'Content-Type':'application/json'}); self.assertEqual(s,201); pid=json.loads(b)['id']
  s,b,h=self.req('/api/bulk-import/templates?module=Manpower',cookie=ck); self.assertEqual(s,200); self.assertEqual(h.get_content_type(),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
  rows=app.parse_xlsx_rows(b); self.assertEqual(rows[0],['Title','Date','Role','Actual Men','Hours','Notes']); self.assertIn('EXAMPLE',rows[1][0])
  # Build a valid workbook using the same stdlib generator format with two data rows.
  raw=app.make_xlsx_template('Manpower'); import zipfile,io,xml.etree.ElementTree as ET
  # Replace the Template sheet XML with a valid three-row sheet.
  bio=io.BytesIO()
  with zipfile.ZipFile(io.BytesIO(raw)) as zin, zipfile.ZipFile(bio,'w',zipfile.ZIP_DEFLATED) as zout:
   for name in zin.namelist():
    data=zin.read(name)
    if name=='xl/worksheets/sheet2.xml':
     vals=[rows[0],['Day 1','2026-09-17','Electrician','6','8','Initial'],['Day 2','2026-09-18','Foreman','3','9','Follow-up']]
     sr=[]
     for r,rv in enumerate(vals,1):
      cells=''.join(f'<c r="{app.xlsx_col(c)}{r}" t="inlineStr"><is><t>{app.xml_escape(v)}</t></is></c>' for c,v in enumerate(rv,1)); sr.append(f'<row r="{r}">{cells}</row>')
     data=f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(sr)}</sheetData></worksheet>'.encode()
    zout.writestr(name,data)
  body,hdr=self.multipart('manpower.xlsx',bio.getvalue()); s,b,_=self.req(f'/api/bulk-import?project_id={pid}&module=Manpower','POST',body,ck,hdr); self.assertEqual(s,201); self.assertEqual(json.loads(b)['rows_imported'],2)
  s,b,_=self.req('/api/dashboard',cookie=ck); d=json.loads(b); p=next(x for x in d['project_summary'] if x['project_id']==pid); self.assertEqual(p['manpower']['planned_men'],0.0); self.assertEqual(p['manpower']['actual_men'],9.0); self.assertEqual(p['manpower']['man_hours'],75.0)
 def test_invalid_import_is_atomic(self):
  ck=self.login(); s,b,_=self.req('/api/projects','POST',json.dumps({'name':'Bulk Atomic Project'}).encode(),ck,{'Content-Type':'application/json'}); self.assertEqual(s,201); pid=json.loads(b)['id']
  # Construct an invalid workbook directly from template bytes.
  raw=app.make_xlsx_template('Manpower'); import zipfile,io
  bio=io.BytesIO()
  with zipfile.ZipFile(io.BytesIO(raw)) as zin, zipfile.ZipFile(bio,'w',zipfile.ZIP_DEFLATED) as zout:
   for name in zin.namelist():
    data=zin.read(name)
    if name=='xl/worksheets/sheet2.xml':
     vals=[['Title','Date','Role','Actual Men','Hours','Notes'],['Good','2026-09-17','Electrician','4','4','8','ok'],['Bad','17/09/2026','NotARole','x','2','8','bad']]
     sr=[]
     for r,rv in enumerate(vals,1):
      cells=''.join(f'<c r="{app.xlsx_col(c)}{r}" t="inlineStr"><is><t>{app.xml_escape(v)}</t></is></c>' for c,v in enumerate(rv,1)); sr.append(f'<row r="{r}">{cells}</row>')
     data=f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(sr)}</sheetData></worksheet>'.encode()
    zout.writestr(name,data)
  body,hdr=self.multipart('bad.xlsx',bio.getvalue()); s,b,_=self.req(f'/api/bulk-import?project_id={pid}&module=Manpower','POST',body,ck,hdr); self.assertEqual(s,400); self.assertEqual(json.loads(b)['rows_imported'],0)
  s,b,_=self.req('/api/module/Manpower?project_id='+pid,cookie=ck); self.assertEqual(s,200); self.assertEqual(len(json.loads(b)['records']),0)
 def test_cross_tenant_import_blocked(self):
  ck=self.login(); s,b,_=self.req('/api/bulk-import/history?project_id=P2',cookie=ck); self.assertEqual(s,403)

if __name__=='__main__': unittest.main(verbosity=2)
