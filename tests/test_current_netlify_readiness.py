from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_netlify_function_directory_contains_modern_entries():
    functions = ROOT / "functions"
    assert (functions / "api.mjs").exists()
    assert (functions / "healthz.mjs").exists()
    assert not (functions / "api.js").exists()
    assert not (functions / "healthz.js").exists()


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
    assert pkg["dependencies"]["@netlify/aws-lambda-compat"] == "2.0.0"
    assert pkg["dependencies"]["@netlify/blobs"] == "11.1.0"
    assert pkg["dependencies"]["pyodide"] == "0.29.5"
    for rel in ["app.py", "netlify_seed.db", "lib/api-implementation.mjs"]:
        assert (ROOT / rel).exists(), rel


def test_modern_api_function_uses_lambda_compat_and_health_probe():
    text = (ROOT / "functions/api.mjs").read_text()
    assert 'from "@netlify/aws-lambda-compat"' in text
    assert "export default withLambda(lambdaHandler)" in text
    assert 'import("../lib/api-implementation.mjs")' in text
    assert 'path === "/healthz"' in text
    assert "statusCode: 200" in text


def test_independent_healthz_function_is_modern_netlify_function():
    text = (ROOT / "functions/healthz.mjs").read_text()
    assert "export default async function handler" in text
    assert "new Response" in text
    assert 'function: "healthz"' in text


def test_frontend_root_static_public_are_identical():
    for name in ["index.html", "app.js", "app.css"]:
        assert (ROOT / name).read_bytes() == (ROOT / "static" / name).read_bytes()
        assert (ROOT / name).read_bytes() == (ROOT / "public" / name).read_bytes()


def test_frontend_cache_headers_are_no_store():
    cfg = (ROOT / "netlify.toml").read_text()
    for asset in ["/", "/index.html", "/app.js", "/app.css"]:
        assert f'for = "{asset}"' in cfg
    assert cfg.count('Cache-Control = "no-store, max-age=0"') >= 4
