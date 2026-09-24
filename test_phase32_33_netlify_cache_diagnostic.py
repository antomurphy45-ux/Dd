from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_frontend_cache_version_bumped():
    html=(ROOT/"index.html").read_text()
    public=(ROOT/"public/index.html").read_text()
    assert "app.js?v=32.33" in html and "app.css?v=32.33" in html
    assert public==html

def test_no_store_headers_for_assets():
    cfg=(ROOT/"netlify.toml").read_text()
    assert 'for = "/app.js"' in cfg and 'for = "/app.css"' in cfg
    assert 'Cache-Control = "no-store, max-age=0, must-revalidate"' in cfg

def test_diagnostic_route_exists():
    fn=(ROOT/"netlify/functions/api.mjs").read_text()
    assert 'pathname === "/api/diagnostic"' in fn
    assert 'version: "32.33"' in fn
