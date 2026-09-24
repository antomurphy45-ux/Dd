from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_modern_netlify_entry_preserves_lambda_handler_contract():
    entry = ROOT / "functions/api.mjs"
    text = entry.read_text()
    assert 'from "@netlify/aws-lambda-compat"' in text
    assert "withLambda(lambdaHandler)" in text
    assert "event, context" in text
    assert "../lib/api-implementation.mjs" in text
