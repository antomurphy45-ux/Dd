# Phase 32.41 — Netlify Blobs runtime fix

The previous production error was:

`MissingBlobsEnvironmentError: The environment has not been configured to use Netlify Blobs. To use it manually, supply the following properties when creating a store: siteID, token`

The root cause is that the API was being deployed as a legacy Lambda-style Netlify Function (`exports.handler`). Netlify documents that the modern Functions runtime provides the platform primitives automatically, while legacy Lambda compatibility mode has different Blobs behavior.

Phase 32.41 keeps the existing Lambda event/response code but wraps it with the official `@netlify/aws-lambda-compat` package and exports it as a modern Function. This preserves the application code while moving the function onto the modern runtime.

After deployment, test `/healthz` first and then sign in. If the API still reports a Blobs environment error, the remaining issue is at the Netlify project/runtime configuration layer rather than the application routing layer.


## Phase 32.42 — explicit production credential fallback

Production logs still showed `MissingBlobsEnvironmentError` after the modern runtime migration. Phase 32.42 therefore passes the Netlify site ID and Blobs-capable Netlify auth token explicitly to `getStore()` when available. The code never stores a token in the repository. It first accepts the project-specific `CONSTRUCTION_CONTROL_SITE_ID` and `CONSTRUCTION_CONTROL_BLOBS_TOKEN` variables, then falls back to Netlify-provided `SITE_ID`/`NETLIFY_SITE_ID` and `NETLIFY_AUTH_TOKEN`/`NETLIFY_BLOBS_TOKEN`.

Netlify documents `SITE_ID` as a read-only runtime variable and documents `NETLIFY_AUTH_TOKEN` as the standard name for a Netlify personal access token. The token must be configured in the Netlify UI with Functions scope and a new deploy is required after changing it.

The public `/healthz` probe reports only whether the site ID and token are present; it never returns their values.
