from pathlib import Path
import re

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
    # The old Lambda adapter must not be executable code.
    uncommented = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    assert "invokeLambda" not in uncommented


def test_netlify_configuration_is_native():
    src = (ROOT / "netlify.toml").read_text()
    assert re.search(r"\[build\][\s\S]*publish = \"public\"", src)
    assert re.search(r"\[functions\][\s\S]*directory = \"functions/\"", src)
    build_section = src.split("[functions]", 1)[0]
    assert "directory = \"functions/\"" not in build_section
    assert 'node_modules/pyodide/**' in src


def test_required_function_files_exist():
    assert (ROOT / "functions" / "api.mjs").is_file()
    assert (ROOT / "functions" / "healthz.mjs").is_file()


def test_lambda_compatibility_dependency_removed():
    src = (ROOT / "package.json").read_text()
    assert "@netlify/aws-lambda-compat" not in src
