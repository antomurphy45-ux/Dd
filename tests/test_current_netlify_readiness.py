from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_netlify_function_directory_contains_real_entries():
    functions = ROOT / "functions"
    assert (functions / "api.js").exists()
    assert (functions / "healthz.js").exists()
    assert not (functions / "api.mjs").exists()
    assert not (functions / "api.cjs").exists()


def test_netlify_config_points_to_function_directory_and_routes():
    cfg = (ROOT / "netlify.toml").read_text()
    assert 'functions = "functions"' in cfg
    assert 'from = "/api/*"' in cfg
    assert 'to = "/.netlify/functions/api/:splat"' in cfg
    assert 'from = "/healthz"' in cfg
    assert 'to = "/.netlify/functions/healthz"' in cfg
    assert 'node_bundler = "esbuild"' in cfg
    assert 'external_node_modules = ["pyodide"]' in cfg


def test_dependencies_and_included_runtime_files_exist():
    pkg = json.loads((ROOT / "package.json").read_text())
    assert pkg["dependencies"]["@netlify/blobs"] == "11.1.0"
    assert pkg["dependencies"]["pyodide"] == "0.29.5"
    for rel in ["app.py", "netlify_seed.db", "lib/api-implementation.mjs"]:
        assert (ROOT / rel).exists(), rel


def test_commonjs_function_exports_handler_and_health_probe_runs():
    js = """
const api = require('./functions/api.js');
if (typeof api.handler !== 'function') process.exit(2);
api.handler({path:'/healthz'}).then(r => {
  if (r.statusCode !== 200) process.exit(3);
  const d = JSON.parse(r.body);
  if (d.status !== 'ok' || d.platform !== 'netlify') process.exit(4);
  console.log('api-handler-healthz: PASS');
});
"""
    r = subprocess.run(["node", "-e", js], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr + r.stdout
    assert "api-handler-healthz: PASS" in r.stdout


def test_independent_healthz_function_exports_handler():
    js = """
const f = require('./functions/healthz.js');
if (typeof f.handler !== 'function') process.exit(2);
f.handler({}).then(r => {
  if (r.statusCode !== 200) process.exit(3);
  const d = JSON.parse(r.body);
  if (d.function !== 'healthz') process.exit(4);
  console.log('healthz-function: PASS');
});
"""
    r = subprocess.run(["node", "-e", js], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr + r.stdout


def test_frontend_root_static_public_are_identical():
    for name in ["index.html", "app.js", "app.css"]:
        assert (ROOT / name).read_bytes() == (ROOT / "static" / name).read_bytes()
        assert (ROOT / name).read_bytes() == (ROOT / "public" / name).read_bytes()


def test_frontend_cache_headers_are_no_store():
    cfg = (ROOT / "netlify.toml").read_text()
    for asset in ["/", "/index.html", "/app.js", "/app.css"]:
        assert f'for = "{asset}"' in cfg
    assert cfg.count('Cache-Control = "no-store, max-age=0"') >= 4
