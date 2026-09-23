# Construction Control — Netlify deployment

This build is Netlify-only. It does not require a Render service or Render persistent disk.

## Architecture

- Netlify hosts the static frontend.
- Netlify Functions expose `/api/*` and `/healthz`.
- The existing Python application logic is executed inside the Netlify Function through Pyodide/WebAssembly, so the existing API contract is retained.
- Netlify Blobs provides persistent storage for the SQLite database and uploaded documents.
- The database is stored as a site-wide Blob and uses strong consistency plus an ETag compare-and-write retry for concurrent updates.

Netlify Functions and Netlify Blobs are platform features documented by Netlify. See the official Netlify documentation for Functions and Blobs.

## First deployment

1. Push/overwrite the complete repository in GitHub.
2. Connect that repository to Netlify.
3. Set the site's publish directory to the repository root if Netlify asks for it. The supplied `netlify.toml` already sets this.
4. Do not configure Render.
5. Netlify installs the `package.json` dependencies during the build and deploys `netlify/functions/api.mjs`.
6. Open the site and log in.

The first API request creates the `construction-control` Blob store entry `database/construction_control.db` from `netlify_seed.db` if no database exists yet.

## Important

The application database is persistent only through Netlify Blobs. Do not rely on files written to the Function's `/tmp` directory for persistence; `/tmp` is only the working copy used during an invocation.

The app's document upload limit is 4 MB so that the request remains within Netlify Function payload limits and each uploaded object remains below the Netlify Blobs per-value limit.

## Health check

`/healthz` returns a Netlify-specific status and reports `netlify-blobs` as the persistence layer.
