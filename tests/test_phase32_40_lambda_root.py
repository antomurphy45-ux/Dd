from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_api_implementation_does_not_depend_on_import_meta_url():
    text = (ROOT / "lib" / "api-implementation.mjs").read_text(encoding="utf-8")
    assert "fileURLToPath" not in text
    assert "import.meta.url" not in text
    assert "process.env.LAMBDA_TASK_ROOT || process.cwd()" in text


def test_required_lambda_files_are_present():
    assert (ROOT / "functions" / "api.js").exists()
    assert (ROOT / "functions" / "healthz.js").exists()
    assert (ROOT / "lib" / "api-implementation.mjs").exists()
