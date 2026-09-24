
import os, sqlite3, unittest, json
from pathlib import Path
import sys
ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT))
import app

class Phase30ProfessionalBrandingLadder(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp=tempfile.NamedTemporaryFile(delete=False,suffix=".db"); self.tmp.close()
        self.old=app.DB_PATH; app.init_db(self.tmp.name)
        self.c=sqlite3.connect(self.tmp.name); self.c.row_factory=sqlite3.Row

    def tearDown(self):
        self.c.close(); Path(self.tmp.name).unlink(missing_ok=True); app.DB_PATH=self.old

    def test_company_logo_field_is_safe_and_public(self):
        cols={r[1] for r in self.c.execute("PRAGMA table_info(companies)").fetchall()}
        self.assertIn("logo_url",cols)
        company=self.c.execute("select * from companies where id='C1'").fetchone()
        public=app.public_company(company)
        self.assertIn("logo_url",public)
        self.assertNotIn("password_hash",public)

    def test_ladder_roles_have_ordered_levels(self):
        rows=self.c.execute("select name,access_level,parent_role_id from roles where company_id='C1' order by access_level").fetchall()
        self.assertTrue(any(r["name"]=="Project Manager" and r["access_level"]==5 for r in rows))
        self.assertTrue(any(r["name"]=="Company Administrator" and r["access_level"]==9 for r in rows))

    def test_permission_can_inherit_from_lower_role(self):
        # Build a temporary custom role that inherits the Site User level.
        parent=self.c.execute("select id from roles where company_id='C1' and name='Project Manager'").fetchone()["id"]
        rid="CUSTOM-L6"
        self.c.execute("insert into roles(id,company_id,name,access_level,parent_role_id) values(?,?,?,?,?)",(rid,"C1","Custom Construction Manager",6,parent))
        self.c.executemany("insert into permissions(role_id,module,action,allowed) values(?,?,?,0)",[(rid,m,a) for m in app.MODULES for a in app.ACTIONS])
        self.c.execute("update users set role='Custom Construction Manager' where id='U2'")
        self.c.commit()
        u=self.c.execute("select * from users where id='U2'").fetchone()
        self.assertTrue(app.has_permission(self.c,u,"Daily Control","Create"))

    def test_dashboard_unsaved_scope_is_defined_before_render(self):
        js=(ROOT/"static/app.js").read_text(encoding="utf-8")
        self.assertIn("const att=dashboardAttentionCards(projects);",js)
        self.assertIn("const unsaved=att.unsaved;",js)
        self.assertNotIn("const att=dashboardAttentionCards(projects);\n const projectOptions",js)

    def test_ui_uses_ladder_not_checkbox_first(self):
        js=(ROOT/"static/app.js").read_text(encoding="utf-8")
        self.assertIn("Access Ladder",js)
        self.assertIn("Advanced permissions",js)
        self.assertIn("access_level",js)
        css=(ROOT/"static/app.css").read_text(encoding="utf-8")
        self.assertIn(".access-ladder",css)
        self.assertIn(".brand-logo-placeholder",css)

class Phase30ScopeReviewSample(unittest.TestCase):
    def test_two_exact_scope_review_jobs_are_saved(self):
        db=ROOT/"sample_four_projects.db"
        self.assertTrue(db.exists())
        c=sqlite3.connect(db); c.row_factory=sqlite3.Row
        rows=c.execute("select * from projects where name like 'SOW Review — Data Centre Building %' order by name").fetchall()
        self.assertEqual(len(rows),2)
        for p in rows:
            self.assertEqual(p["scope_ref"],"SOW-DC-001 Rev 1.1")
            self.assertIsNotNone(p["start_date"]); self.assertIsNotNone(p["finish_date"])
            plan=c.execute("select * from plans where project_id=?",(p["id"],)).fetchone()
            self.assertIsNotNone(plan)
            tasks=c.execute("select * from plan_tasks where project_id=? order by start_date",(p["id"],)).fetchall()
            self.assertEqual(len(tasks),15)
            self.assertEqual(tasks[0]["name"],"Mobilisation, site establishment, surveys")
            self.assertEqual(tasks[-1]["name"],"Practical Completion")
            mods={r[0] for r in c.execute("select distinct module from module_records where project_id=?",(p["id"],)).fetchall()}
            required={"Daily Control","Documents","RFIs","Risks","Actions","Snags","Materials","Procurement","RAMS","Permits","Commissioning","Variations","Cost Control","Handover","Reports"}
            self.assertTrue(required.issubset(mods))
            self.assertGreater(c.execute("select count(*) from daily_attendance where project_id=?",(p["id"],)).fetchone()[0],1000)
        c.close()

if __name__=="__main__":
    unittest.main()
