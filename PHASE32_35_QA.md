# Phase 32.35 QA — Netlify Lambda handler resolution

## Purpose
Replace the ESM function entry point with an explicit CommonJS `api.cjs` Lambda entry point. The entry point exports `exports.handler` synchronously and dynamically loads the existing ESM implementation. This removes ambiguity in Netlify's Lambda-compatible handler resolver while preserving the existing application logic.

## Validation
- `netlify/functions/api.cjs` exists and exports `handler` using CommonJS.
- Implementation moved to `netlify/lib/api-implementation.mjs` so it is not discovered as a second function.
- Implementation retains the existing Web/Request routing and Netlify Blobs persistence logic.
- Function response adapter remains Lambda-compatible.
