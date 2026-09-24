from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase_32_42_uses_explicit_blobs_credentials_fallback():
    source = (ROOT / "lib" / "api-implementation.mjs").read_text()
    assert "process.env.CONSTRUCTION_CONTROL_SITE_ID || process.env.SITE_ID || process.env.NETLIFY_SITE_ID" in source
    assert "process.env.CONSTRUCTION_CONTROL_BLOBS_TOKEN || process.env.NETLIFY_AUTH_TOKEN || process.env.NETLIFY_BLOBS_TOKEN" in source
    assert "getStore(STORE_NAME, { region: REGION, siteID, token })" in source
    assert "const store = blobStore();" in source


def test_phase_32_42_healthz_does_not_expose_secret():
    source = (ROOT / "functions" / "healthz.mjs").read_text()
    assert "site_id_present" in source
    assert "token_present" in source
    assert "CONSTRUCTION_CONTROL_BLOBS_TOKEN" in source
    assert "process.env.NETLIFY_AUTH_TOKEN" in source
    assert '"token": process.env' not in source
