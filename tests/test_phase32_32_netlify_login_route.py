from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

def test_redirect_preserves_api_splat_and_healthz():
    cfg=(ROOT/"netlify.toml").read_text()
    assert 'from = "/api/*"' in cfg
    assert 'to = "/.netlify/functions/api/:splat"' in cfg
    assert 'from = "/healthz"' in cfg
    assert 'to = "/.netlify/functions/api/healthz"' in cfg

def test_function_normalizes_direct_and_rewritten_paths():
    fn=(ROOT/"netlify/functions/api.mjs").read_text()
    assert 'function normalizePath(pathname)' in fn
    assert 'pathname.startsWith(prefix)' in fn
    assert '"/.netlify/functions/api/"' in fn
    assert '"/api/" + pathname.slice(prefix.length)' in fn

def test_frontend_reports_non_json_response_without_hiding_status():
    js=(ROOT/"app.js").read_text()
    assert "Invalid server response (HTTP ${r.status})" in js
    assert "credentials:'same-origin'" in js

def test_function_has_json_error_contract():
    fn=(ROOT/"netlify/functions/api.mjs").read_text()
    assert 'application/json; charset=utf-8' in fn
    assert 'Construction Control API error' in fn
    assert 'return json(500' in fn
