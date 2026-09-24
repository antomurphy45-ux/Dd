import tempfile, unittest, threading, json, sys
from pathlib import Path
from urllib.request import Request, urlopen
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); import app

class DUBProjectsPopulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); app.DB_PATH=Path(cls.tmp.name)/'db.sqlite'; app.init_db()
        cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler); cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2); cls.tmp.cleanup()
    def req(self,path,method='GET',body=None,cookie=None):
        h={'Content-Type':'application/json'}
        if cookie:h['Cookie']=cookie
        with urlopen(Request(f'http://127.0.0.1:{self.port}{path}',method=method,data=json.dumps(body).encode() if body is not None else None,headers=h),timeout=5) as r:
            return r.status,json.loads(r.read().decode()),r.headers
    def login(self):
        req=Request(f'http://127.0.0.1:{self.port}/api/login',method='POST',data=json.dumps({'email':'owner@demo.local','password':'DemoPass!123'}).encode(),headers={'Content-Type':'application/json'})
        with urlopen(req,timeout=5) as r:return r.headers['Set-Cookie'].split(';',1)[0]
    def test_both_projects_are_fully_populated(self):
        ck=self.login(); s,d,_=self.req('/api/projects',cookie=ck); self.assertEqual(s,200)
        ids={p['id'] for p in d['projects']}; self.assertTrue({'DUB10','DUB50'} <= ids)
        c=app.db()
        try:
            for pid in ('DUB10','DUB50'):
                self.assertEqual(c.execute('select count(*) from plans where project_id=?',(pid,)).fetchone()[0],1)
                self.assertEqual(c.execute('select count(*) from plan_tasks where project_id=?',(pid,)).fetchone()[0],15)
                self.assertEqual(c.execute('select count(*) from project_staff_assignments where project_id=?',(pid,)).fetchone()[0],9)
                self.assertEqual(c.execute('select count(*) from task_staff_assignments where project_id=?',(pid,)).fetchone()[0],9)
        finally:c.close()
    def test_programme_contains_sow_delivery_sequence(self):
        c=app.db()
        try:
            for pid in ('DUB10','DUB50'):
                names=[r[0] for r in c.execute('select name from plan_tasks where project_id=? order by start_date',(pid,))]
                for expected in ('MV Switchgear / Transformers','LV Boards / UPS / Generators','Chillers / Dry Coolers / CRAH','Fire Alarm / Suppression','BMS / Security Installation','Copper / Fibre Cabling','Level 5 IST / Utility Loss Testing','Client Training / Handover','Practical Completion / Snagging Closeout'):
                    self.assertIn(expected,names)
        finally:c.close()

if __name__=='__main__':unittest.main()
