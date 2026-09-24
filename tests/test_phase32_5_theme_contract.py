from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_theme_contract_is_wired():
    js = (ROOT / 'app.js').read_text()
    css = (ROOT / 'app.css').read_text()
    assert 'function applyThemeValues' in js
    assert 'function previewSettings' in js
    assert 'oninput="previewSettings()"' in js
    assert 'id=setHeader' in js and 'id=setSidebar' in js
    assert "state.settings={...state.settings,...payload,...(d.settings||{})}" in js
    assert "r.style.setProperty('--cc-blue',s.accent_color)" not in js
    assert 'button:not(.secondary){background:var(--accent)}' not in css
    assert 'button{background:var(--cc-navy)' in css
    assert 'aside{background:var(--sidebar)}' in css
    assert '.nav.on{background:rgba(255,255,255,.10)' in css
    assert '--header-color:#2563eb' in css
    assert '--cc-blue:var(--accent)' not in css
    assert 'content>header{border-top:4px solid var(--header-color)' in css
    assert 'aside{background:var(--sidebar)}' in css


def test_root_and_static_assets_are_identical():
    for name in ('app.js', 'app.css', 'index.html'):
        assert (ROOT / name).read_bytes() == (ROOT / 'static' / name).read_bytes(), name


def test_semantic_palette_is_not_overridden_by_accent():
    css = (ROOT / 'app.css').read_text()
    js = (ROOT / 'app.js').read_text()
    assert "r.style.setProperty('--cc-blue',s.accent_color)" not in js
    assert '--cc-blue:var(--accent)' not in css
    assert '.kpi-chip.red{background:#fff0f0}' in css
    assert '.kpi-chip.amber{background:#fff8e8}' in css
    assert '.kpi-chip.purple{background:#f5efff}' in css
    assert '.kpi-chip.teal{background:#eaf9f6}' in css
    assert '.dash-action.red .dash-icon{background:#ffe0e0}' in css
    assert '.dash-action.amber .dash-icon{background:#fff0ca}' in css
    assert '.dash-action.purple .dash-icon{background:#eee4ff}' in css
    assert '.dash-action.teal .dash-icon{background:#d8f3ef}' in css
    assert 'button:not(.secondary){background:var(--accent)}' not in css
