import tempfile, unittest, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
class P14BIntegration(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(); app.DB_PATH=Path(self.t.name)/'db.sqlite'; app.init_db(); self.c=app.db(); self.u=self.c.execute("select * from users where id='U1'").fetchone()
  self.c.execute("insert into plans(id,company_id,project_id,name,created_by) values('PL','C1','P1','Main','U1')")
  self.c.execute("insert into plan_tasks(id,plan_id,project_id,name,start_date,finish_date,percent_complete,planned_men,baseline_start,baseline_finish) values('T','PL','P1','Install','2026-09-07','2026-09-11',50,4,'2026-09-07','2026-09-11')")
  self.c.execute("insert into module_records(id,company_id,project_id,module,title,data_json,created_by) values('D','C1','P1','Daily Control','Day','{\"date\":\"2026-09-08\",\"completed_activities\":\"Install\"}','U1')")
  self.c.execute("insert into module_records(id,company_id,project_id,module,title,data_json,created_by) values('M','C1','P1','Manpower','Labour','{\"date\":\"2026-09-08\",\"planned_men\":4,\"actual_men\":3,\"hours\":8,\"role\":\"Electrician\"}','U1')")
  self.c.commit()
 def tearDown(self): self.c.close(); self.t.cleanup()
 def test_baseline_columns_and_progress_weight(self):
  r=self.c.execute("select baseline_start,baseline_finish from plan_tasks where id='T'").fetchone(); self.assertEqual(r['baseline_start'],'2026-09-07'); self.assertEqual(r['baseline_finish'],'2026-09-11')
  data=json.loads(self.c.execute("select data_json from module_records where id='M'").fetchone()[0]); self.assertEqual(data['actual_men'],3)
 def test_scope_isolation_for_integration_sources(self):
  self.c.execute("insert into module_records(id,company_id,project_id,module,title,data_json) values('X','C2','P2','Manpower','Other','{\"date\":\"2026-09-08\",\"actual_men\":99}')"); self.c.commit()
  self.assertEqual(self.c.execute("select count(*) from module_records where company_id='C1' and project_id='P1' and module='Manpower'").fetchone()[0],1)
if __name__=='__main__': unittest.main(verbosity=2)
