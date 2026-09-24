# Phase 32.40 validation

Target: Netlify-only Construction Control deployment.

Production error diagnosed from Netlify logs:
- `fileURLToPath(import.meta.url)` was receiving an undefined URL after Netlify bundled the ESM API implementation into the CommonJS Lambda runtime.
- This caused the API Function to return HTTP 502 before login processing.

Fix:
- API implementation root resolution now uses `LAMBDA_TASK_ROOT` when present, falling back to `process.cwd()` for local execution.
- Removed the `import.meta.url` / `fileURLToPath` dependency from the Netlify runtime path.

Validated locally:
- JavaScript syntax checks passed.
- Python compile check passed for app.py.
- Netlify build command completed successfully.
- Root/static/public frontend assets are byte-identical.
- Dependency-free API and healthz function probes return HTTP 200.
- Deployment/application regression suite remains green for the same 27 targeted tests used as the Netlify deployment gate.
- New regression checks confirm the bundled-runtime-safe root resolution contract.

Note: the repository contains historical phase tests with older fixture expectations; the complete historical suite is not used as the deployment gate.
