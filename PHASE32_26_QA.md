# Construction Control — Phase 32.26 QA

## Fix
Resolved the next Render dashboard boot error shown by the user:
`dashValue is not defined`

The dashboard project-card renderer uses `dashValue(...)` for KPI counts. The helper was missing from the Phase 32.25 frontend. It has been restored before `dashboardProjectCards(...)` in both `app.js` and `static/app.js`.

## Validation
- Python syntax: PASS
- JavaScript syntax (`app.js`): PASS
- JavaScript syntax (`static/app.js`): PASS
- Root/static JS synchronisation: PASS
- Targeted Phase 32.20–32.26 tests: **11 passed**
- Local runtime `/healthz`: PASS
- Local runtime `/`: PASS
- Full historical pytest suite: not claimed

## Packaging
LOCAL and RENDER packages are built from the same tested source tree.
