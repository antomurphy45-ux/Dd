from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_redirect_preserves_api_splat_and_healthz():
    cfg = (ROOT / "netlify.toml").read_text()
    assert 'from = "/api/*"' in cfg
    assert 'to = "/.netlify/functions/api/:splat"' in cfg
    assert 'from = "/healthz"' in cfg
    assert 'to = "/.netlify/functions/healthz"' in cfg


def test_api_entry_has_health_probe():
    fn = (ROOT / "functions/api.mjs").read_text()
    assert 'path === "/healthz"' in fn
    assert 'statusCode: 200' in fn


def test_function_has_json_error_contract():
    fn = (ROOT / "lib/api-implementation.mjs").read_text()
    assert 'content-type": "application/json' in fn
    assert 'return json(500' in fn
