# Construction Control

Private construction project-control web application.

## Current deployment target

**Netlify-only.** The application is designed to run from a single Netlify project:

- Static frontend: Netlify CDN
- Backend: Netlify Functions
- Python application logic: `app.py`, executed inside the Function through Pyodide/WebAssembly
- Persistent data: Netlify Blobs
- Database model: SQLite working copy restored from and written back to Netlify Blobs
- Uploaded documents: Netlify Blobs
- No Render service, Docker deployment or Render persistent disk is required

Live site used for production testing:

`https://antopmt.netlify.app`

## Phase 32.43

This is the current repository build.

### Production problem being diagnosed

The live API previously failed at login because the Function reported that `NETLIFY_AUTH_TOKEN` was unavailable. Current Netlify documentation states that when `@netlify/blobs` is used from a Function, the Blobs `siteID`, `deployID` and `token` are normally supplied automatically.

Phase 32.43 therefore does two things:

1. The API tries the documented zero-configuration `getStore()` path first.
2. If that platform context is unavailable, the API can use explicitly supplied site/token variables as a fallback without storing a secret in the repository.

`/healthz` now reports only boolean presence information for relevant runtime variables. It never returns a token or site ID value.

## Repository layout

```text
app.py
app.js
app.css
index.html
static/              mirrored frontend assets
public/              Netlify publish output
functions/
  api.mjs            main API entry point
  healthz.mjs        dependency-free deployment diagnostic
lib/
  api-implementation.mjs
netlify_seed.db      baseline application database
netlify-build.mjs    prepares public/
netlify.toml         Netlify build, function and routing configuration
package.json         Netlify runtime dependencies
requirements.txt     Python application dependencies
source/              source/support files
data/                application seed/support data
tests/               automated tests
QA.md                consolidated QA and development record
README.md            project and deployment documentation
```

## Netlify configuration

`netlify.toml` is authoritative:

- Build command: `npm run build`
- Publish directory: `public`
- Functions directory: `functions`
- `/api/*` → `/.netlify/functions/api/:splat`
- `/healthz` → `/.netlify/functions/healthz`
- Pyodide is bundled as an external Node module

Do not change the Functions directory to `netlify/functions`.

## First production checks after uploading

1. Deploy the complete repository.
2. Open `/healthz`.
3. Confirm HTTP 200 and JSON containing:
   - `status: "ok"`
   - `platform: "netlify"`
   - `function: "healthz"`
   - `phase: "32.43"`
4. Inspect `blob_credentials`.
5. Test login only after the health check is correct.
6. If login still fails, the health response tells us whether the deployed Function can see the relevant runtime variables without exposing their values.

### Environment variables

Do **not** put a secret in GitHub or `netlify.toml`.

Netlify's current documentation says Functions receive the Blobs credentials automatically. An explicit fallback can use:

- `CONSTRUCTION_CONTROL_SITE_ID` or `SITE_ID` / `NETLIFY_SITE_ID`
- `CONSTRUCTION_CONTROL_BLOBS_TOKEN` or `NETLIFY_AUTH_TOKEN` / `NETLIFY_BLOBS_TOKEN`

If an environment variable is changed in Netlify, create a new deploy before testing because Function environment values are applied at deploy time.

## Data persistence

The Function uses `/tmp` only as a working area. The persistent application database is the Netlify Blob key:

`database/construction_control.db`

The application uses an ETag compare-and-write when saving the SQLite database so concurrent requests can retry against the latest version.

## Validation gate

Before a new phase is packaged:

- Python syntax must pass.
- JavaScript syntax must pass.
- Current Netlify readiness tests must pass.
- Security serialization tests must pass.
- Relevant regression tests must pass.
- Frontend root/static/public copies must match.
- `netlify-build.mjs` must successfully regenerate `public/`.
- ZIP contents must be verified before delivery.

The full historical test suite is not automatically treated as the deployment gate because it contains older phase-specific fixtures and expectations. The current deployment gate is documented in `QA.md`.

## Labour roles

The application uses the established labour vocabulary:

- Construction Manager
- Foreman
- Charge Hand
- Electrician
- 4th Year
- 3rd Year
- 2nd Year
- 1st Year
- GO

## Development rule

Make changes in phases. Test the current phase completely before moving forward. Never claim a production fix has been verified until the live Netlify deployment has actually been tested.
