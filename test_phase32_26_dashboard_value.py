from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_dashboard_value_helper_is_defined_before_project_cards():
    for rel in ("app.js", "static/app.js"):
        js=(ROOT/rel).read_text()
        assert "function dashValue(p,key)" in js
        assert js.index("function dashValue(p,key)") < js.index("function dashboardProjectCards(projects)")
        assert "dashValue(p,'rfis')" in js
        assert "dashValue(p,'pending_approvals')" in js
