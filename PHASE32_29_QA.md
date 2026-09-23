# Phase 32.29 QA — Netlify-only deployment

## Purpose
Move the production deployment model from Render to Netlify while retaining the existing application/API contract and the Phase 32.28 save/cache fixes.

## Architecture
- Netlify static hosting publishes only `public/`.
- `/api/*` and `/healthz` are handled by `netlify/functions/api.mjs`.
- The existing Python business logic in `app.py` is executed inside the Netlify Function using Pyodide/WebAssembly.
- SQLite is kept as the application data model in a temporary function filesystem and persisted back to a site-wide Netlify Blob using strong reads and ETag compare-and-write.
- Uploaded documents are synchronised to a separate Netlify Blob store.
- No Render service, Render disk, Dockerfile or `render.yaml` is required.

## Validation
- Python syntax: PASS
- JavaScript syntax: PASS
- Root/static/public index cache-buster synchronisation: PASS
- Netlify deployment configuration: PASS
- Netlify adapter health/login smoke: PASS
- Netlify settings persistence through fresh Python process: PASS
- Focused Phase 32.20–32.28 regression suite: PASS — 22 tests
- ZIP integrity: pending final packaging

## Known validation limitation
The execution environment does not have the npm dependencies installed and cannot perform a live Netlify Functions invocation against Netlify Blobs. The function source is syntax-checked and its Python handler is exercised directly. The production Netlify deployment will install `pyodide` 0.29.5 and `@netlify/blobs` 11.1.0 from `package.json`.

The historical full pytest suite is not claimed as clean. It contains older tests with stale assumptions (for example, a manager's expected project list that predates the current DUB84 data). Those are historical test expectations, not a Phase 32.29 Netlify regression.
