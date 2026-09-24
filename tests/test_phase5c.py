
import tempfile,sqlite3,unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]))
import app

class Phase5CTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.NamedTemporaryFile(delete=False);self.tmp.close()
        self.old=app.DB_PATH;app.init_db(self.tmp.name)
        self.c=sqlite3.connect(self.tmp.name);self.c.row_factory=sqlite3.Row
    def tearDown(self):
        self.c.close();Path(self.tmp.name).unlink(missing_ok=True);app.DB_PATH=self.old
    def test_schema_persists(self):
        self.c.execute("INSERT INTO projects(id,company_id,name,level_id,manloader) VALUES(?,?,?,?,?)",("PX","C1","Persistent Project",None,10));self.c.commit();self.c.close()
        c=sqlite3.connect(self.tmp.name);self.assertEqual(c.execute("select name from projects where id='PX'").fetchone()[0],"Persistent Project");c.close()
    def test_server_scopes_project_access_by_company(self):
        self.assertTrue(app.can_access_project(self.c,"U1","P1"))
        self.assertFalse(app.can_access_project(self.c,"U1","P2"))
        self.assertTrue(app.can_access_project(self.c,"U3","P2"))
    def test_company_isolation_query(self):
        rows=self.c.execute("select id from projects where company_id=?",("C1",)).fetchall()
        self.assertEqual(set(x[0] for x in rows),{'P1','DUB10','DUB50'})
    def test_password_security(self):
        h=app.pw_hash("Secret!123");self.assertTrue(app.pw_ok("Secret!123",h));self.assertFalse(app.pw_ok("Wrong",h))
    def test_tiers(self):
        self.assertEqual(app.TIERS["individual"]["users"],1);self.assertEqual(app.TIERS["small"]["projects"],20);self.assertIn("management",app.TIERS["business"]["features"])
    def test_role_permissions(self):
        rid=self.c.execute("select id from roles where name='Project Manager'").fetchone()[0]
        self.assertEqual(self.c.execute("select allowed from permissions where role_id=? and module='Daily Control' and action='Edit'",(rid,)).fetchone()[0],1)
        self.assertEqual(self.c.execute("select allowed from permissions where role_id=? and module='Cost Control' and action='Edit'",(rid,)).fetchone()[0],0)

if __name__=="__main__":unittest.main()
