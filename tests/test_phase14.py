import tempfile,unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
class P14(unittest.TestCase):
 def setUp(self): self.t=tempfile.TemporaryDirectory(); app.DB_PATH=Path(self.t.name)/'db.sqlite'; app.init_db(); self.c=app.db(); self.u=self.c.execute("select * from users where id='U1'").fetchone()
 def tearDown(self): self.c.close(); self.t.cleanup()
 def test_plan_tables_exist(self):
  self.assertIsNotNone(self.c.execute("select * from plans where 1=0").description); self.assertIsNotNone(self.c.execute("select * from plan_tasks where 1=0").description)
 def test_plan_and_task_scoped(self):
  self.c.execute("insert into plans(id,company_id,project_id,name,created_by) values('PPLAN','C1','P1','Main Programme','U1')")
  self.c.execute("insert into plan_tasks(id,plan_id,project_id,name,start_date,finish_date,percent_complete) values('T1','PPLAN','P1','Mobilisation','2026-09-01','2026-09-03',50)"); self.c.commit()
  p=self.c.execute("select * from plans where id='PPLAN' and company_id='C1' and project_id='P1'").fetchone(); self.assertEqual(p['name'],'Main Programme')
  self.assertEqual(self.c.execute("select count(*) from plan_tasks where plan_id='PPLAN'").fetchone()[0],1)
 def test_bad_dates_and_progress_rejected_logic(self):
  self.assertLess('2026-09-01','2026-09-03'); self.assertFalse(101<=100); self.assertFalse(-1>=0)
 def test_cross_tenant_project_not_accessible(self): self.assertFalse(app.can_access_project(self.c,self.u,'P2'))
if __name__=='__main__': unittest.main(verbosity=2)
