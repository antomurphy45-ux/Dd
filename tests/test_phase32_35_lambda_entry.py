from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]

def test_commonjs_netlify_entry_exports_handler():
    entry=ROOT/"functions/api.js"
    text=entry.read_text()
    assert "exports.handler" in text
    assert "../lib/api-implementation.mjs" in text
