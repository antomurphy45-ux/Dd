from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_programme_screenshot_buttons_are_present_and_gantt_has_end_actions():
    js=(ROOT/'app.js').read_text()
    for label in ['+ Activity','Set baseline','Resources','Look-ahead','Baseline vs Current','Live Progress','Update Programme','Calendar','Control Centre','Import Excel','Export Excel']:
        assert label in js
    assert 'Activity → Progress / Critical Path → Scheduled → Edit / Move / Delete' in js
    assert '<div>Options</div>' in js
    assert 'gantt-actions' in js

def test_staff_training_has_document_upload_controls():
    js=(ROOT/'app.js').read_text()
    py=(ROOT/'app.py').read_text()
    assert 'Upload document' in js
    assert 'chooseTrainingDocument' in js
    assert 'parts[5]=="documents"' in py
    assert 'STAFF_TRAINING_DOCUMENT_UPLOAD' in py
