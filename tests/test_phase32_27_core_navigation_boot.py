from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_layout_and_page_helpers_are_defined_before_use_and_no_tooltip_helpers_returned():
    js = (ROOT / 'app.js').read_text()
    static_js = (ROOT / 'static/app.js').read_text()
    assert 'function layout(title,body,active=' in js
    assert 'function page(p)' in js
    assert js.index('function layout(title,body,active=') < js.index('function renderDashboard()')
    assert js.index('function page(p)') < js.index('function renderDashboard()')
    assert js == static_js
    assert 'function enhanceButtonHints' not in js
    assert 'Open or run this action.' not in js
