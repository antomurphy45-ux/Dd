from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_netlify_publishes_only_frontend_assets():
    cfg=(ROOT/'netlify.toml').read_text()
    assert 'publish = "public"' in cfg
    assert 'functions = "functions"' in cfg
    for name in ['index.html','app.js','app.css']:
        assert (ROOT/'public'/name).exists()

def test_netlify_runtime_uses_blobs_and_pyodide():
    cfg=(ROOT/'netlify.toml').read_text()
    fn=(ROOT/'lib/api-implementation.mjs').read_text()
    pkg=json.loads((ROOT/'package.json').read_text())
    assert pkg['dependencies']['@netlify/blobs']=='11.1.0'
    assert pkg['dependencies']['pyodide']=='0.29.5'
    assert 'https://cdn.jsdelivr.net/pyodide/v0.29.5/full/' in fn
    assert 'getStore' in fn and 'onlyIfMatch' in fn
    assert 'external_node_modules = ["pyodide"]' in cfg

def test_render_deployment_files_are_not_part_of_netlify_build():
    assert not (ROOT/'render.yaml').exists()
    assert not (ROOT/'Dockerfile').exists()
    assert not (ROOT/'RENDER_DEPLOY.md').exists()

def test_root_and_public_frontend_assets_match():
    assert (ROOT/'index.html').read_bytes()==(ROOT/'public/index.html').read_bytes()
    assert (ROOT/'app.js').read_bytes()==(ROOT/'public/app.js').read_bytes()
    assert (ROOT/'app.css').read_bytes()==(ROOT/'public/app.css').read_bytes()
