from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_api_entry_is_commonjs_and_dynamic_imports_implementation():
    text=(ROOT/'functions/api.js').read_text()
    assert 'exports.handler' in text
    assert 'import("../lib/api-implementation.mjs")' in text
