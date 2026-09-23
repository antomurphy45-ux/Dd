# Phase 32.36 QA — Canonical CommonJS Lambda entry

## Purpose
Harden the Netlify function entry after the deployed Phase 32.35 `api.cjs` continued to report `api.handler is undefined or not exported` at runtime.

## Changes
- Function entry is now `netlify/functions/api.js`.
- Root `package.json` uses `"type": "commonjs"`.
- `netlify.toml` explicitly selects the legacy `zisi` JavaScript bundler.
- The dynamically imported ESM implementation is explicitly included in the function bundle.

## Validation
- `node --check netlify/functions/api.js`: PASS
- CommonJS `require()` handler export check: PASS
- `node --check netlify/lib/api-implementation.mjs`: PASS
- `python -m py_compile app.py`: PASS
- No `api.cjs` or `api.mjs` remains in `netlify/functions/`.
