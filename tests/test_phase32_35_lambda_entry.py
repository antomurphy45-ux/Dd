from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_commonjs_netlify_entry_exports_handler():
    entry = ROOT / "netlify" / "functions" / "api.cjs"
    assert entry.exists()
    text = entry.read_text(encoding="utf-8")
    assert "exports.handler" in text
    assert 'import("../lib/api-implementation.mjs")' in text


def test_esm_implementation_is_not_a_function_entry():
    assert not (ROOT / "netlify" / "functions" / "api.mjs").exists()
    assert (ROOT / "netlify" / "lib" / "api-implementation.mjs").exists()
