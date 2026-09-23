# Phase 32.27 QA

## Purpose
Repair the dashboard boot chain after the Render screenshot showed `layout is not defined`.

## Fix
- Restored the shared `layout()` renderer before dashboard rendering.
- Restored the shared `page()` navigation dispatcher before dashboard rendering.
- Kept the generic hover-tooltip generator removed.
- Synchronized `app.js` and `static/app.js`.

## Validation
- Python syntax: PASS (`python -m py_compile app.py`)
- JavaScript syntax: PASS (`node --check app.js`)
- Root/static JavaScript identical: PASS
- Core JS smoke with dashboard render: PASS
- Local HTTP `/healthz`: PASS
- Local `/` static page: PASS
- Local `/app.js`: PASS
- Local login: PASS
- Local `/api/dashboard`: PASS (4 project summaries returned)
- Targeted regression tests: **12 passed**

Targeted suite:
- Phase 32.20 PM cockpit
- Phase 32.21 programme tabs
- Phase 32.22 calendar display
- Phase 32.23 roles/UI
- Phase 32.24 dashboard boot
- Phase 32.25 dashboard cards
- Phase 32.26 dashboard value
- Phase 32.27 core navigation boot

## Browser note
A headless Chromium navigation attempt is blocked by the execution environment with `ERR_BLOCKED_BY_ADMINISTRATOR`; therefore no physical browser click-through is claimed. Runtime HTTP and JavaScript dashboard-render smoke tests were completed successfully.

## Important
The complete historical pytest suite is not claimed as passing. Only the targeted current regression suite above is certified for this phase.
