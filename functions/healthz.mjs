// Construction Control — Phase 32.43 deployment diagnostic.
// This endpoint is intentionally dependency-free so it can prove that the
// current Netlify production function sees the expected runtime environment.
// It reports presence/absence only; it never returns secret values.

function presence(name) {
  return Boolean(process.env[name]);
}

export default async function handler() {
  return new Response(JSON.stringify({
    status: "ok",
    platform: "netlify",
    function: "healthz",
    storage: "netlify-blobs",
    phase: "32.43",
    blob_credentials: {
      site_id_present: Boolean(
        process.env.CONSTRUCTION_CONTROL_SITE_ID ||
        process.env.SITE_ID ||
        process.env.NETLIFY_SITE_ID
      ),
      token_present: Boolean(
        process.env.CONSTRUCTION_CONTROL_BLOBS_TOKEN ||
        process.env.NETLIFY_AUTH_TOKEN ||
        process.env.NETLIFY_BLOBS_TOKEN
      ),
      netlify_auth_token_present: presence("NETLIFY_AUTH_TOKEN"),
      site_id_runtime_present: presence("SITE_ID"),
      netlify_site_id_present: presence("NETLIFY_SITE_ID")
    }
  }), {
    status: 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-construction-control-function": "32.43-healthz"
    }
  });
}
