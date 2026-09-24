from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_api_entry_uses_modern_runtime_compatibility_wrapper():
    text = (ROOT / "functions/api.mjs").read_text()
    assert 'import { withLambda } from "@netlify/aws-lambda-compat";' in text
    assert "export default withLambda(lambdaHandler);" in text
    assert 'import("../lib/api-implementation.mjs")' in text
