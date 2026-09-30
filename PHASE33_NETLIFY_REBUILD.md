# Phase 33 — Native Netlify rebuild

This repository is now structured around Netlify's native Functions model:

`Request + Context -> handleRequest(Request) -> Response`

## Changes

- Removed the Lambda compatibility dependency.
- Replaced the API entry point with a native Netlify Function.
- Uses `context.cookies.get("cc_session")` for the incoming session.
- Uses `context.cookies.set(...)` for the outgoing session cookie.
- Keeps the existing Python application/business logic and Pyodide bridge.
- Keeps Netlify Blobs for persistent SQLite storage.
- Keeps Node `crypto.scryptSync` compatibility used by the existing password format.
- Uses the current Netlify functions directory configuration.
- Keeps Pyodide runtime assets in the Function bundle.

## Validation

Run:

```bash
python -m pytest tests/test_phase33_native_netlify.py -q
node --check functions/api.mjs
node --check lib/api-implementation.mjs
python -m py_compile app.py
```

No Netlify deployment is performed by this package. Deploy only after the local checks pass.
