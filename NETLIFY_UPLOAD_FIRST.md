# Construction Control — Phase 32.41 Netlify upload

## Why this version exists

The live Netlify project was reporting **0 functions in production**. The linked GitHub `main` branch had `netlify.toml`, but the function files were not present in the repository. This build removes the extra `netlify/` directory level for Functions and uses a simple root `functions/` directory.

## Required repository root

After extracting this package, the GitHub repository root must contain:

- `netlify.toml`
- `package.json`
- `app.py`
- `functions/api.js`
- `functions/healthz.js`
- `lib/api-implementation.mjs`
- `public/index.html`
- `public/app.js`
- `public/app.css`

Do not upload the ZIP itself as the application source. Extract it first.

## Netlify settings

The repository `netlify.toml` is authoritative:

- Build command: `npm run build`
- Publish directory: `public`
- Functions directory: `functions`

Do not manually change the Functions directory to `netlify/functions`.

## First production test

Before testing login, check Netlify > Functions. It should show:

- `api`
- `healthz`

Then open `/healthz` on the live site. Expected JSON contains:

`"status":"ok"`

`"platform":"netlify"`

`"function":"healthz"`

Only after that should `/api/login` be tested.


## Phase 32.41 production fix
The API 502 was traced to Netlify's bundled CommonJS runtime evaluating `import.meta.url` as undefined. The API implementation no longer uses `fileURLToPath(import.meta.url)`; it resolves the Lambda root from `LAMBDA_TASK_ROOT` and falls back to the local working directory.
