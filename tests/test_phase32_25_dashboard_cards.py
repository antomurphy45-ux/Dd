from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_project_cards_is_defined_before_dashboard_render():
    for rel in ('app.js', 'static/app.js'):
        js = (ROOT / rel).read_text()
        assert 'function dashboardProjectCards(projects)' in js
        assert js.index('function dashboardProjectCards(projects)') < js.index('dashboardProjectCards(projects)')
