# Phase 32.41 validation

Target: Netlify-only Construction Control deployment.

Change in this phase:
- Migrated the Netlify Functions entry points to the modern Netlify Functions runtime.
- Added `@netlify/aws-lambda-compat` 2.0.0 so the existing AWS Lambda-style handler contract can remain unchanged.
- This is specifically to ensure Netlify platform primitives, including automatic Netlify Blobs context, are available to the API handler.
- The application still initializes `getStore()` inside the request path.

Validated locally:
- JavaScript syntax checks passed for functions/api.mjs, functions/healthz.mjs, and lib/api-implementation.mjs.
- Python compile check passed for app.py.
- Netlify frontend build preparation completed.
- Root/static/public frontend assets are byte-identical.
- Required deployment files are present.
- No Render deployment files are required by the Netlify build configuration.

Note:
- The full historical test suite is not the deployment gate because it contains older fixture expectations and long-running tests.
- The environment-specific Netlify Blobs auto-injection cannot be fully reproduced without a live Netlify runtime in this local validation environment; production verification is therefore required after deployment.
