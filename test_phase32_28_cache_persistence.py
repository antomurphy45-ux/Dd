from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]

def test_entrypoints_use_phase_32_29_cache_buster_and_root_static_are_synced():
    root = (ROOT / "index.html").read_text()
    static = (ROOT / "static/index.html").read_text()
    assert "app.js?v=32.29" in root
    assert "app.css?v=32.29" in root
    assert root == static

def test_netlify_functions_and_blob_persistence_are_configured():
    netlify = (ROOT / "netlify.toml").read_text()
    fn = (ROOT / "netlify/functions/api.mjs").read_text()
    pkg = (ROOT / "package.json").read_text()
    assert "functions = \"netlify/functions\"" in netlify
    assert "@netlify/blobs" in pkg
    assert "pyodide" in pkg
    assert "getStore" in fn
    assert "onlyIfMatch" in fn

def test_netlify_shell_is_not_cached():
    netlify = (ROOT / "netlify.toml").read_text()
    assert 'for = "/"' in netlify
    assert 'for = "/index.html"' in netlify
    assert "no-store" in netlify and "max-age=0" in netlify

def test_netlify_healthcheck_is_platform_specific():
    fn = (ROOT / "netlify/functions/api.mjs").read_text()
    assert "pathname === \"/healthz\"" in fn
    assert "platform: \"netlify\"" in fn
    assert "storage: \"netlify-blobs\"" in fn
