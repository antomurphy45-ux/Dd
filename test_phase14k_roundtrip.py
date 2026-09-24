import io,json,tempfile,threading,unittest,uuid,zipfile
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app
class Phase14K(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/'db.sqlite'; app.init_db(); cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler); cls.port=cls.server.server_address[1]; cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
 @classmethod
 def tearDownClass(cls): cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2);cls.tmp.cleanup()
 def req(self,path,method='GET',body=None,cookie=None,headers=None):
  r=Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=body,headers=headers or {}); 
  if cookie:r.add_header('Cookie',cookie)
  try:
   with urlopen(r,timeout=5) as x:return x.status,x.read(),x.headers
  except HTTPError as e:return e.code,e.read(),e.headers
 def login(self):
  s,b,h=self.req('/api/login','POST',json.dumps({'email':'owner@demo.local','password':'DemoPass!123'}).encode(),headers={'Content-Type':'application/json'});self.assertEqual(s,200);return h['Set-Cookie'].split(';',1)[0]
 def setup(self,ck):
  s,b,_=self.req('/api/projects','POST',json.dumps({'name':'14K Project'}).encode(),ck,{'Content-Type':'application/json'});self.assertEqual(s,201);pid=json.loads(b)['id']
  s,b,_=self.req('/api/plans','POST',json.dumps({'project_id':pid,'name':'14K Programme'}).encode(),ck,{'Content-Type':'application/json'});self.assertEqual(s,201);return pid,json.loads(b)['id']
 def wb(self,rows):
  raw=app.make_programme_xlsx_template('14K Programme');bio=io.BytesIO()
  with zipfile.ZipFile(io.BytesIO(raw)) as zin,zipfile.ZipFile(bio,'w',zipfile.ZIP_DEFLATED) as zout:
   for name in zin.namelist():
    data=zin.read(name)
    if name=='xl/worksheets/sheet2.xml':
     vals=[[x[0] for x in app.PROGRAMME_IMPORT_HEADERS]]+rows; sr=[]
     for r,rv in enumerate(vals,1):
      cells=''.join(f'<c r="{app.xlsx_col(c)}{r}" t="inlineStr"><is><t>{app.xml_escape(v)}</t></is></c>' for c,v in enumerate(rv,1));sr.append(f'<row r="{r}">{cells}</row>')
     data=f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(sr)}</sheetData></worksheet>'.encode()
    zout.writestr(name,data)
  return bio.getvalue()
 def mp(self,fn,data):
  b='----CC'+uuid.uuid4().hex; body=(f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{fn}"\r\nContent-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n'.encode()+data+f'\r\n--{b}--\r\n'.encode());return body,{'Content-Type':f'multipart/form-data; boundary={b}'}
 def import_initial(self,ck,plan):
  rows=[['A001','Mobilise','','2026-10-05','2026-10-05','0','3','','FS','0','Yes','', '', '', '', ''],['A002','Install','A001','2026-10-06','2026-10-08','25','6','A001','FS','1','No','', '', '', '', '']]
  body,h=self.mp('p.xlsx',self.wb(rows));s,b,_=self.req('/api/plan-import?plan_id='+plan,'POST',body,ck,h);self.assertEqual(s,201)
 def test_export_has_stable_ids_and_roundtrip_updates_and_adds(self):
  ck=self.login();pid,plan=self.setup(ck);self.import_initial(ck,plan)
  s,b,h=self.req('/api/plan-export/'+plan,cookie=ck);self.assertEqual(s,200);self.assertEqual(h.get_content_type(),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');rows=app.parse_xlsx_rows(b);self.assertEqual(rows[0],[x[0] for x in app.PROGRAMME_IMPORT_HEADERS]);self.assertEqual(rows[1][0],'A001');self.assertEqual(rows[2][0],'A002')
  rows[1][4]='2026-10-06';rows[1][5]='50';rows.append(['A003','Test','A002','2026-10-09','2026-10-09','0','2','A002','FS','0','No','', '', '', '', ''])
  body,h=self.mp('edited.xlsx',self.wb(rows[1:]));s,b,_=self.req('/api/plan-import/roundtrip?plan_id='+plan+'&commit=0','POST',body,ck,h);d=json.loads(b);self.assertEqual(s,200);self.assertEqual(d['updates'],2);self.assertEqual(d['adds'],1)
  body,h=self.mp('edited.xlsx',self.wb(rows[1:]));s,b,_=self.req('/api/plan-import/roundtrip?plan_id='+plan+'&commit=1','POST',body,ck,h);self.assertEqual(s,200)
  s,b,_=self.req('/api/plans/'+plan,cookie=ck);tasks=json.loads(b)['tasks'];self.assertEqual(len(tasks),3);a={t['activity_id']:t for t in tasks};self.assertEqual(a['A001']['percent_complete'],50);self.assertEqual(a['A001']['finish_date'],'2026-10-06');self.assertEqual(a['A003']['predecessor_id'],a['A002']['id'])
  s,b,_=self.req('/api/plans/'+plan+'/gantt',cookie=ck);self.assertEqual(s,200);self.assertEqual(json.loads(b)['finish_date'],'2026-10-13')
 def test_preview_errors_are_non_destructive(self):
  ck=self.login();pid,plan=self.setup(ck);self.import_initial(ck,plan);s,b,_=self.req('/api/plans/'+plan,cookie=ck);before=json.loads(b)['tasks']; rows=[['A001','Mobilise','','2026-10-05','2026-10-05','50','3','','FS','0','Yes','', '', '', '', ''],['A002','Install','A001','2026-10-06','2026-10-08','25','6','A002','FS','1','No','', '', '', '', '']]
  body,h=self.mp('bad.xlsx',self.wb(rows));s,b,_=self.req('/api/plan-import/roundtrip?plan_id='+plan+'&commit=1','POST',body,ck,h);self.assertEqual(s,400);s,b,_=self.req('/api/plans/'+plan,cookie=ck);after=json.loads(b)['tasks'];self.assertEqual([(x['activity_id'],x['percent_complete']) for x in before],[(x['activity_id'],x['percent_complete']) for x in after])

 def test_cross_tenant_export_blocked(self):
  ck=self.login();s,b,_=self.req('/api/plan-export/P2',cookie=ck);self.assertEqual(s,404)

if __name__=='__main__':unittest.main(verbosity=2)
