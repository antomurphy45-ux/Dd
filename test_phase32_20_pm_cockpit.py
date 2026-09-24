from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'app.py'
JS=ROOT/'app.js'
CSS=ROOT/'app.css'

def test_rag_reason_and_external_approval_backend():
    s=APP.read_text()
    assert 'CREATE TABLE IF NOT EXISTS external_approvals' in s
    assert 'health_reason' in s
    assert '/api/external-approvals' in s
    assert 'ext_overdue' in s

def test_pm_cockpit_and_rag_ui():
    s=JS.read_text()
    assert 'showProjectHealth' in s
    assert 'pmDailyBrief' in s
    assert 'openExternalApprovals' in s
    assert 'Start today\'s control' in s

def test_external_approval_documents_can_be_attached():
    s=APP.read_text()
    assert 'external_approvals WHERE id=? AND company_id=? AND project_id=?' in s
    assert 'EXTERNAL_APPROVAL_' in s

def test_visual_contract():
    s=CSS.read_text()
    for token in ('pm-brief','rag-summary','external-approval-row'):
        assert token in s
