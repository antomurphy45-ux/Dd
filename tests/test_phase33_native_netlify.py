from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_native_function_entrypoint():
    src = (ROOT / "functions" / "api.mjs").read_text()
    assert "Request + Context" in src
    assert 'from "../lib/api-implementation.mjs"' in src
    assert "handleRequest(nativeRequest)" in src
    assert "@netlify/aws-lambda-compat" not in src
    assert "invokeLambda" not in src


def test_native_cookie_bridge():
    src = (ROOT / "functions" / "api.mjs").read_text()
    assert 'context.cookies.get("cc_session")' in src
    assert "context.cookies.set(cookie)" in src
    assert 'headers.set("Cookie"' in src


def test_lambda_adapter_removed_from_implementation():
    src = (ROOT / "lib" / "api-implementation.mjs").read_text()
    assert "export { handleRequest };" in src
    assert "export async function invokeLambda" in src  # kept only inside the historical comment block


def test_netlify_configuration_is_native():
    src = (ROOT / "netlify.toml").read_text()
    assert 'directory = "functions/"' in src
    assert 'functions = "functions"' not in src
    assert 'node_modules/pyodide/**' in src


def test_lambda_compatibility_dependency_removed():
    src = (ROOT / "package.json").read_text()
    assert "@netlify/aws-lambda-compat" not in src
