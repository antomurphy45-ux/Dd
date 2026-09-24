from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_modules_are_defined_before_dashboard_render():
    js = (ROOT / 'app.js').read_text()
    static_js = (ROOT / 'static/app.js').read_text()
    expected = "const DASH_MODULES=[['RFIs','rfis','blue','RFIs'],['Risks','risks','red','Risks'],['Actions','actions','amber','Actions'],['Snags','snags','purple','Snags'],['Approvals','pending_approvals','teal','Pending approvals']];"
    assert expected in js
    assert js.index(expected) < js.index('const issueCards=DASH_MODULES.map')
    assert js == static_js
