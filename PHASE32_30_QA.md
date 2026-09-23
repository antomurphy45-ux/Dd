# Phase 32.30 QA — Netlify deployment directory fix

## Purpose
Make Netlify deployment resilient when the repository is uploaded/overwritten without preserving the `public/` directory entry.

## Changes
- Added `netlify-build.mjs`.
- Added `npm run build` to `package.json`.
- `netlify.toml` now explicitly runs `npm run build` before publishing.
- Build creates `public/` and synchronises `index.html`, `app.js`, and `app.css` from the repository root.
- Publish target remains `public/`, so backend source, database and tests are not published as static files.

## Validation
- Build command PASS
- public/index.html exists PASS
- public/app.js exists PASS
- public/app.css exists PASS
- Netlify publish target remains `public` PASS
- Netlify functions path remains `netlify/functions` PASS


## Post-deploy login fix / Phase 32.31 preparation
- Removed the obsolete `pyodide.loadPackage("sqlite3")` call. Pyodide 0.29.x includes sqlite3 in the standard library; attempting to load it as a separate package can cause a Function invocation failure.
- Added a JSON 500 response wrapper around the Netlify Function so backend failures cannot surface to the frontend as an HTML/non-JSON response.
- Netlify Function JavaScript syntax check PASS.
