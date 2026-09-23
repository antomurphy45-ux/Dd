# Phase 32.34 QA — Netlify Function Handler Compatibility

## Root cause confirmed
Netlify production reported `Runtime.HandlerNotFound - api.handler is undefined or not exported`.
The deployed function is therefore expecting a Lambda-compatible `handler` export.

## Fix
`netlify/functions/api.mjs` now exports both:
- the existing modern Web Request default handler; and
- a Lambda-compatible named `handler` adapter.

The adapter converts the Netlify event into a standard Request and converts the Response back to a Lambda-compatible response object.

## Validation
- JavaScript syntax check passed.
- Required default export retained.
- Required named `handler` export added.
- ZIP integrity checked.

## Deployment
Upload/overwrite the complete repository with this ZIP and allow Netlify to build from the GitHub commit. Then test `/healthz` and login.
