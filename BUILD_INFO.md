Construction Control — Phase 32.29

Target: NETLIFY ONLY

Changes:
- Converted the deployment architecture from Render to Netlify.
- Added a Netlify Function API adapter at `netlify/functions/api.mjs`.
- Retained the existing Python API/business logic through Pyodide 0.29.5 rather than rewriting the application's 40+ API routes.
- Added Netlify Blobs persistence for the SQLite database with strong consistency and ETag compare-and-write retry.
- Added Netlify Blob persistence for uploaded documents.
- Moved the published frontend into `public/` so backend source, tests and database files are not exposed as static assets.
- Removed Render deployment files (`Dockerfile`, `render.yaml`, `RENDER_DEPLOY.md`).
- Renamed the bundled bootstrap database to `netlify_seed.db`.
- Retained Phase 32.28 frontend cache-busting and save/persistence fixes.
- Bumped frontend cache version to 32.29.
- Added Netlify deployment and adapter regression tests.

Validation:
- Python syntax PASS
- JavaScript syntax PASS
- Focused Netlify + Phase 32.20–32.28 regression tests: 22 passed
- Root/static/public frontend asset sync PASS
- Netlify configuration checks PASS
- ZIP integrity PASS after packaging

Live Netlify deployment was not performed from this environment.
Historical full pytest suite not claimed as clean because older tests contain stale data/deployment assumptions.


## Phase 32.30
- Fixed Netlify build failure caused by `public` not existing at publish time.
- Added `npm run build` / `netlify-build.mjs` to create and synchronise the public frontend before publishing.
- Kept `publish = "public"` so backend source and database files are not statically published.
- Validation: Node syntax PASS; Netlify build PASS; required publish assets PASS; ZIP integrity PASS.


## Phase 32.33 — Netlify login invocation fix
- Fixed Netlify Function startup by removing the obsolete `pyodide.loadPackage("sqlite3")` call from the Pyodide 0.29.5 runtime.
- Added JSON error handling so `/api/*` returns a JSON error instead of an HTML/non-JSON response if a function exception occurs.
- Target issue: mobile login displayed `Invalid server response` after Netlify deployment.
- This remains Netlify-only; no Render deployment is used.


Phase 32.33: Netlify login routing hardening. API rewrites now preserve :splat, the function normalizes both direct and rewritten paths, and the frontend reports HTTP status/body snippets instead of masking non-JSON responses as a generic error.


## Phase 32.35 — Lambda handler resolution
The Netlify API function now uses an explicit CommonJS `api.cjs` entry point exporting `exports.handler`, with the existing ESM implementation moved outside the functions directory.


## Phase 32.36 — CommonJS Lambda entry hardening
- Replaced `api.cjs` with the canonical `netlify/functions/api.js` CommonJS Lambda entry.
- Changed the root package module type to CommonJS so `.js` function entry files are unambiguously CommonJS.
- Forced Netlify's JavaScript bundler to `zisi` for this legacy Lambda-compatible entry.
- Explicitly included the ESM API implementation in the function bundle because it is loaded dynamically.
- Existing application/API implementation is unchanged.

Validation:
- CommonJS handler export check PASS
- JavaScript syntax PASS
- Python syntax PASS
- Netlify configuration checks PASS
- ZIP integrity PASS

## Phase 32.38 — Netlify function discovery hardening
- Added an independent dependency-free `healthz` function.
- Restored a CommonJS `api.js` function entry exporting `exports.handler`.
- Switched the functions bundler configuration to esbuild with Pyodide externalised.
- Added explicit runtime included files and current deployment-readiness tests.
