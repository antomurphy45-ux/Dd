from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase_32_43_healthz_is_safe_and_diagnostic():
    text = (ROOT / "functions/healthz.mjs").read_text()
    assert 'phase: "32.43"' in text
    assert 'netlify_auth_token_present: presence("NETLIFY_AUTH_TOKEN")' in text
    assert 'site_id_runtime_present: presence("SITE_ID")' in text
    assert 'netlify_site_id_present: presence("NETLIFY_SITE_ID")' in text
    assert 'process.env.NETLIFY_AUTH_TOKEN' in text
    assert 'process.env.CONSTRUCTION_CONTROL_BLOBS_TOKEN' in text
    assert '"x-construction-control-function": "32.43-healthz"' in text
    # No secret value is serialised by the diagnostic.
    assert 'process.env.NETLIFY_AUTH_TOKEN,' not in text


def test_phase_32_43_blobs_prefers_netlify_zero_config_context():
    text = (ROOT / "lib/api-implementation.mjs").read_text()
    assert 'return getStore(STORE_NAME, { region: REGION });' in text
    assert 'return getStore(STORE_NAME, { region: REGION, siteID, token });' in text
    assert 'automatic Function context is unavailable' in text
    assert 'version: "32.43"' in text
