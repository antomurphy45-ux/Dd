# Phase 32.32 QA — Netlify login routing

## Problem
The live Netlify frontend loaded, but login displayed `Invalid server response`. The frontend was receiving a non-JSON response from the API path, masking the actual HTTP response.

## Fix
- Preserve `/api/*` splat when rewriting to the Netlify Function.
- Preserve `/healthz` as an explicit function route.
- Normalize both direct `/api/...` requests and `/.netlify/functions/api/...` rewritten requests inside the Function.
- Guarantee JSON error responses from the Function.
- Frontend now includes HTTP status and a short response snippet for any non-JSON API response.
- Requests explicitly use same-origin credentials for the session cookie.

## Validation
- Python syntax PASS
- JavaScript syntax PASS
- Build PASS
- Public frontend assets synchronised PASS
- Netlify routing regression tests PASS
- Existing Phase 32.20–32.31 targeted tests run below
