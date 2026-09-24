# Construction Control — Phase 32.38 QA

## Objective
Stabilise the Netlify-only deployment and make function discovery independently testable before the repository is uploaded to GitHub.

## Deployment architecture
- Frontend publish directory: `public`
- Netlify Functions directory: `netlify/functions`
- API function: `netlify/functions/api.js`
- Independent deployment probe: `netlify/functions/healthz.js`
- Python application: `app.py`, loaded by the API adapter through Pyodide
- Persistence: Netlify Blobs through `@netlify/blobs`
- No Render service, Docker build, or Render persistent disk is required by the Netlify deployment.

## Changes
1. Added a dependency-free `healthz` Netlify Function so function discovery can be verified without loading Pyodide.
2. Hardened `api.js` as a CommonJS Lambda entry exporting `exports.handler`.
3. Kept the heavier API implementation outside the function entry point at `netlify/lib/api-implementation.mjs`.
4. Configured Netlify to use `esbuild` and package Pyodide as an external Node module.
5. Added explicit function included files for the Python application, seed database and runtime support files.
6. Routed `/healthz` to the independent health function and `/api/*` to the API function.
7. Added no-store headers for the shell and frontend assets.
8. Synchronized root, `static/`, and `public/` frontend copies.
9. Added current deployment-readiness tests.

## Local validation performed
- `node --check netlify/functions/api.js` — PASS
- `node --check netlify/functions/healthz.js` — PASS
- `node --check netlify/lib/api-implementation.mjs` — PASS
- `node --check netlify-build.mjs` — PASS
- `node --check app.js` — PASS
- `node --check public/app.js` — PASS
- `node --check static/app.js` — PASS
- `python -m py_compile app.py` — PASS
- Current Netlify readiness suite — **7 passed**
- Production readiness + security serialization + current Netlify readiness — **16 passed**
- Direct local invocation of both Netlify functions — PASS; both returned HTTP 200 JSON health responses.

## Important test-gate note
The repository contains historical phase tests from earlier iterations of the application. Some of those tests assert obsolete filenames, old cache-buster versions, old seed fixtures, or old permission expectations. They are not used as the Phase 32.38 deployment gate. The current deployment-readiness tests are the gate for this phase.

## Required production verification after upload
1. Netlify → Functions must show both `api` and `healthz` in Production.
2. `https://antopmt.netlify.app/healthz` must return JSON with `status: "ok"` and `platform: "netlify"`.
3. `https://antopmt.netlify.app/.netlify/functions/healthz` must also return HTTP 200 JSON.
4. Only after those checks pass should login be tested.
