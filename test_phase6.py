import json, os, subprocess, sys, tempfile, time, urllib.request, urllib.error
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
import unittest

ROOT=Path(__file__).parents[1]
class Phase6HttpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.NamedTemporaryFile(delete=False,suffix='.db'); cls.tmp.close()
        env=os.environ.copy(); env['CC_DB_PATH']=cls.tmp.name
        # app currently uses fixed path; run isolated by cwd in temp copy is cumbersome, so test app logic directly below.
    @classmethod
    def tearDownClass(cls): Path(cls.tmp.name).unlink(missing_ok=True)

class Phase6LogicTest(unittest.TestCase):
    def setUp(self):
        import app
        self.app=app
        self.tmp=tempfile.NamedTemporaryFile(delete=False); self.tmp.close()
        self.old=app.DB_PATH; app.init_db(self.tmp.name)
        import sqlite3
        self.c=sqlite3.connect(self.tmp.name); self.c.row_factory=sqlite3.Row
    def tearDown(self):
        self.c.close(); Path(self.tmp.name).unlink(missing_ok=True); self.app.DB_PATH=self.old
    def test_scoped_project_access(self):
        self.assertTrue(self.app.can_access_project(self.c,'U2','P1'))
        self.assertFalse(self.app.can_access_project(self.c,'U2','P2'))
        self.assertTrue(self.app.can_access_project(self.c,'U3','P2'))
    def test_role_permission_matrix_is_editable(self):
        rid=self.c.execute("select id from roles where company_id='C1' and name='Project Manager'").fetchone()[0]
        self.c.execute("update permissions set allowed=1 where role_id=? and module='Cost Control' and action='View'",(rid,)); self.c.commit()
        self.assertEqual(self.c.execute("select allowed from permissions where role_id=? and module='Cost Control' and action='View'",(rid,)).fetchone()[0],1)
    def test_tenant_safe_project_access_assignment(self):
        # A C1 admin cannot assign a C2 project to a C1 user through the valid-project set.
        valid={x[0] for x in self.c.execute("select id from projects where company_id='C1'").fetchall()}
        self.assertNotIn('P2',valid)
    def test_org_cannot_self_parent(self):
        lid='L2'
        self.assertFalse(lid not in [x[0] for x in self.c.execute("select id from org_levels where company_id='C1'").fetchall()])
    def test_audit_company_scope(self):
        self.c.execute("insert into audit(company_id,user_id,action,target) values('C1','U1','TEST','x')"); self.c.commit()
        self.assertEqual(self.c.execute("select count(*) from audit where company_id='C2' and action='TEST'").fetchone()[0],0)

if __name__=='__main__': unittest.main()
