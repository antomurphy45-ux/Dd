# Upload this repository as one complete replacement

This ZIP is a complete repository snapshot for Construction Control Phase 32.38.

## GitHub
Replace the repository contents with the contents of this ZIP and commit them to `main`.
Do not put the repository inside an extra folder.

The following paths must exist at the repository root after upload:

- `netlify.toml`
- `package.json`
- `app.py`
- `netlify/functions/api.js`
- `netlify/functions/healthz.js`
- `netlify/lib/api-implementation.mjs`
- `public/index.html`
- `public/app.js`
- `public/app.css`

## Netlify
Netlify must use:
- Build command: `npm run build`
- Publish directory: `public`
- Functions directory: `netlify/functions`

Do not add a Render service or Docker build.

## First production test
After the deploy finishes, open:

`/healthz`

Expected response is JSON, not a Netlify Page Not Found HTML page.

Then open Netlify → Functions. Production should list:
- `api`
- `healthz`

If Functions still shows zero, stop there: the repository has not been deployed from the expected root/function directory and login testing is premature.
