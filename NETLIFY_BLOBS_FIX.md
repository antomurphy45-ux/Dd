# Phase 32.41 — Netlify Blobs runtime fix

The previous production error was:

`MissingBlobsEnvironmentError: The environment has not been configured to use Netlify Blobs. To use it manually, supply the following properties when creating a store: siteID, token`

The root cause is that the API was being deployed as a legacy Lambda-style Netlify Function (`exports.handler`). Netlify documents that the modern Functions runtime provides the platform primitives automatically, while legacy Lambda compatibility mode has different Blobs behavior.

Phase 32.41 keeps the existing Lambda event/response code but wraps it with the official `@netlify/aws-lambda-compat` package and exports it as a modern Function. This preserves the application code while moving the function onto the modern runtime.

After deployment, test `/healthz` first and then sign in. If the API still reports a Blobs environment error, the remaining issue is at the Netlify project/runtime configuration layer rather than the application routing layer.
