import json, sqlite3
from pathlib import Path
import app


def test_dub84_seed_contains_full_programme_and_source_manloader(tmp_path):
    db_path=tmp_path/'construction_control.db'
    app.init_db(db_path)
    c=sqlite3.connect(db_path); c.row_factory=sqlite3.Row
    project=c.execute("SELECT * FROM projects WHERE id='DUB84'").fetchone()
    assert project is not None
    assert project['start_date']=='2026-09-01'
    assert project['finish_date']=='2026-11-25'
    assert project['manloader']==34
    plan=c.execute("SELECT * FROM plans WHERE id='PLAN-DUB84'").fetchone()
    assert plan is not None and plan['baseline']==1
    tasks=c.execute("SELECT * FROM plan_tasks WHERE project_id='DUB84'").fetchall()
    assert len(tasks)==264
    assert not c.execute("SELECT 1 FROM plan_tasks WHERE project_id='DUB84' AND finish_date<start_date LIMIT 1").fetchone()
    assert c.execute("SELECT COUNT(*) FROM plan_tasks WHERE project_id='DUB84' AND planned_men>0").fetchone()[0] == 7
    source=json.loads((Path(app.BASE)/'data'/'dub84_programme.json').read_text())
    assert len(source['project']['manloader_days'])==60
    for row in source['project']['manloader_days']:
        total=c.execute("SELECT COALESCE(SUM(planned_men),0) FROM plan_tasks WHERE project_id='DUB84' AND start_date<=? AND finish_date>=?",(row['date'],row['date'])).fetchone()[0]
        assert total == row['planned_men'], (row['date'], total, row['planned_men'])
    # Idempotency: a second startup must not duplicate or reset the programme.
    c.close()
    app.init_db(db_path)
    c=sqlite3.connect(db_path)
    assert c.execute("SELECT COUNT(*) FROM plan_tasks WHERE project_id='DUB84'").fetchone()[0]==264
    assert c.execute("SELECT COUNT(*) FROM projects WHERE id='DUB84'").fetchone()[0]==1
    c.close()
