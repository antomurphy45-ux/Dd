from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_calendar_matches_month_board_layout_and_activity_tabs():
    js = (ROOT / 'app.js').read_text()
    css = (ROOT / 'app.css').read_text()
    static_js = (ROOT / 'static/app.js').read_text()
    static_css = (ROOT / 'static/app.css').read_text()

    for token in [
        'function showCalendar',
        'calendarWeekNumber',
        'calendarMonthLabel',
        'calendarTaskTab',
        'calendarDayModal',
        'calendarShiftMonth',
        'calendar-week-number',
        'calendar-task-tab',
    ]:
        assert token in js

    for token in [
        '.calendar-grid',
        '.calendar-week-number',
        '.calendar-cell',
        '.calendar-task-tab',
        '.calendar-exception-tab',
        '.calendar-month-bar',
    ]:
        assert token in css

    assert js == static_js
    assert css == static_css
