from pathlib import Path


def test_api_exports_modern_and_lambda_handlers():
    text = Path("netlify/functions/api.mjs").read_text()
    assert "export default handleRequest;" in text
    assert "export const handler = async (event) =>" in text
    assert "isBase64Encoded: true" in text
    assert "statusCode: response.status" in text
