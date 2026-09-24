import io,json,tempfile,threading,unittest,uuid,zipfile
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app

class Phase14JProgrammeImport(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/'db.sqlite'; app.init_db(); cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler); cls.port=cls.server.server_address[1]; cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
 @classmethod
 def tearDownClass(cls): cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2);cls.tmp.cleanup()
 def req(self,path,method='GET',body=None,cookie=None,headers=None):
  r=Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=body,headers=headers or {})
  if cookie:r.add_header('Cookie',cookie)
  try:
   with urlopen(r,timeout=5) as x:return x.status,x.read(),x.headers
  except HTTPError as e:return e.code,e.read(),e.headers
 def login(self):
  s,b,h=self.req('/api/login','POST',json.dumps({'email':'owner@demo.local','password':'DemoPass!123'}).encode(),headers={'Content-Type':'application/json'});self.assertEqual(s,200);return h['Set-Cookie'].split(';',1)[0]
 def project_plan(self,ck):
  s,b,_=self.req('/api/projects','POST',json.dumps({'name':'Programme Import E2E'}).encode(),ck,{'Content-Type':'application/json'});self.assertEqual(s,201);pid=json.loads(b)['id']
  s,b,_=self.req('/api/plans','POST',json.dumps({'project_id':pid,'name':'Imported Programme'}).encode(),ck,{'Content-Type':'application/json'});self.assertEqual(s,201);return pid,json.loads(b)['id']
 def workbook(self,rows):
  raw=app.make_programme_xlsx_template('Imported Programme');bio=io.BytesIO()
  with zipfile.ZipFile(io.BytesIO(raw)) as zin,zipfile.ZipFile(bio,'w',zipfile.ZIP_DEFLATED) as zout:
   for name in zin.namelist():
    data=zin.read(name)
    if name=='xl/worksheets/sheet2.xml':
     vals=[ [x[0] for x in app.PROGRAMME_IMPORT_HEADERS] ]+rows; sr=[]
     for r,rv in enumerate(vals,1):
      cells=''.join(f'<c r="{app.xlsx_col(c)}{r}" t="inlineStr"><is><t>{app.xml_escape(v)}</t></is></c>' for c,v in enumerate(rv,1));sr.append(f'<row r="{r}">{cells}</row>')
     data=f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(sr)}</sheetData></worksheet>'.encode()
    zout.writestr(name,data)
  return bio.getvalue()
 def multipart(self,filename,data):
  b='----CC'+uuid.uuid4().hex;body=(f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n'.encode()+data+f'\r\n--{b}--\r\n'.encode());return body,{'Content-Type':f'multipart/form-data; boundary={b}'}
 def test_template_and_live_schedule_change(self):
  ck=self.login();pid,plan=self.project_plan(ck);s,b,h=self.req('/api/plan-import/templates?plan_id='+plan,cookie=ck);self.assertEqual(s,200);self.assertEqual(h.get_content_type(),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');self.assertEqual(app.parse_xlsx_rows(b)[0],[x[0] for x in app.PROGRAMME_IMPORT_HEADERS])
  rows=[['A001','Mobilise','','2026-10-05','2026-10-05','100','3','','FS','0','Yes','Mobilisation','','','',''],['A002','Install','A001','2026-10-06','2026-10-08','0','6','A001','FS','1','No','Install','','','',''],['A003','Test','A002','2026-10-09','2026-10-09','0','2','A002','FS','0','No','Testing','','','','']]
  body,hdr=self.multipart('programme.xlsx',self.workbook(rows));s,b,_=self.req('/api/plan-import?plan_id='+plan,'POST',body,ck,hdr);self.assertEqual(s,201);self.assertEqual(json.loads(b)['rows_imported'],3)
  s,b,_=self.req('/api/plans/'+plan,cookie=ck);d=json.loads(b);self.assertEqual(len(d['tasks']),3);ids={t['name']:t['id'] for t in d['tasks']};self.assertEqual(d['tasks'][1]['predecessor_id'],ids['Mobilise'])
  s,b,_=self.req('/api/plans/'+plan+'/gantt',cookie=ck);g=json.loads(b);self.assertEqual(g['finish_date'],'2026-10-12');self.assertEqual(len([x for x in g['tasks'] if x['critical']]),3)
  s,b,_=self.req('/api/plans/'+plan+'/control',cookie=ck);ctrl=json.loads(b);self.assertEqual(ctrl['activity_counts']['total'],3);self.assertEqual(ctrl['programme_progress'],20.0)
 def test_cycle_import_is_atomic(self):
  ck=self.login();pid,plan=self.project_plan(ck);rows=[['A001','One','A002','2026-11-02','2026-11-02','0','1','A002','FS','0','No','','','','',''],['A002','Two','A001','2026-11-03','2026-11-03','0','1','A001','FS','0','No','','','','','']];body,hdr=self.multipart('cycle.xlsx',self.workbook(rows));s,b,_=self.req('/api/plan-import?plan_id='+plan,'POST',body,ck,hdr);self.assertEqual(s,400);s,b,_=self.req('/api/plans/'+plan,cookie=ck);self.assertEqual(len(json.loads(b)['tasks']),0)
 def test_cross_tenant_blocked(self):
  ck=self.login();s,b,_=self.req('/api/plan-import/templates?plan_id=P2',cookie=ck);self.assertEqual(s,404)
if __name__=='__main__':unittest.main(verbosity=2)
