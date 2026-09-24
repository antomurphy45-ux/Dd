# Construction Control persistence — Netlify

The production deployment target is Netlify.

The frontend and API are served from the same Netlify site. API requests use `/api/*` and are routed to the Netlify Function in `netlify/functions/api.mjs`.

Persistent application data is stored in Netlify Blobs. The SQLite database is copied into the function's temporary working directory for each request, the existing Python application handles the request, and the resulting database is written back using a strong-consistency Blob read and ETag compare-and-write.

Uploaded documents are stored as separate Netlify Blob objects and restored into the function's temporary upload directory before API processing.

No Render service or Render disk is required by this build.
