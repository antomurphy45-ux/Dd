# Phase 32.28 QA

## Purpose
Fix frontend cache staleness and make Render data persistence explicit.

## Changes
- Root and static HTML now load `app.js`/`app.css` with `v=32.28`.
- Netlify does not cache `/` or `/index.html`, preventing an old HTML shell from continuing to reference retired assets.
- Render blueprint attaches a 1 GB persistent disk at `/var/data`, matching SQLite and upload paths.
- Render sets `CONSTRUCTION_CONTROL_REQUIRE_PERSISTENT_STORAGE=1`.
- `/healthz` returns HTTP 503 when persistence is required but the `/var/data` disk is not mounted, rather than silently running on ephemeral storage.
- Added focused Phase 32.28 regression tests.

## Validation
- Python syntax: PASS
- JavaScript syntax: PASS
- Phase 32.28 regression tests: PASS (4 passed)
- Existing targeted Phase 32.20–32.27 tests: PASS (16 passed)
- Persistence API save/restart smoke: PASS (company colours/logo, staff, assignment and Daily Control survived restart)
- ZIP integrity: PASS

- Additional targeted suites: PASS (13 passed). One legacy Phase 32.4 test expects an independently running service on hard-coded port 3013 and failed with connection refused; it does not exercise the current in-process test server or the Phase 32.28 changes.
