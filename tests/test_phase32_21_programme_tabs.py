from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_programme_views_are_local_tabs_and_no_visible_info_icons():
    js=(ROOT/'app.js').read_text()
    css=(ROOT/'app.css').read_text()
    static_js=(ROOT/'static/app.js').read_text()
    static_css=(ROOT/'static/app.css').read_text()

    for label in ['Programme','Resources','Look-ahead','Baseline vs Current','Live Progress','Update Programme','Calendar','Control Centre']:
        assert label in js
    assert 'function programmeTabs' in js
    assert 'function openProgrammeTab' in js
    assert 'renderProgrammePanel(id,\'resources\'' in js
    assert 'renderProgrammePanel(id,\'lookahead\'' in js
    assert 'renderProgrammePanel(id,\'comparison\'' in js
    assert 'renderProgrammePanel(id,\'integration\'' in js
    assert 'renderProgrammePanel(id,\'update\'' in js
    assert 'renderProgrammePanel(id,\'calendar\'' in js
    assert 'renderProgrammePanel(id,\'control\'' in js
    assert 'programme-tabs' in css
    assert 'programme-tab.active' in css

    # The visible circled-i decoration was removed; hover explanations remain via title/data-help.
    assert 'ⓘ' not in js
    assert 'ⓘ' not in css
    assert "content:'ⓘ'" not in css

    # Root and static copies must stay identical because both are shipped in the deployment package.
    assert js == static_js
    assert css == static_css
