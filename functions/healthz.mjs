// Dependency-free Netlify deployment probe for Construction Control.
// Exported through the modern Functions runtime so Netlify platform context,
// including Blobs primitives, is available consistently to this project.
export default async function handler() {
  return new Response(JSON.stringify({
    status: "ok",
    platform: "netlify",
    function: "healthz",
    storage: "netlify-blobs",
    blob_credentials: {
      site_id_present: Boolean(process.env.CONSTRUCTION_CONTROL_SITE_ID || process.env.SITE_ID || process.env.NETLIFY_SITE_ID),
      token_present: Boolean(process.env.CONSTRUCTION_CONTROL_BLOBS_TOKEN || process.env.NETLIFY_AUTH_TOKEN || process.env.NETLIFY_BLOBS_TOKEN)
    }
  }), {
    status: 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-construction-control-function": "32.42-healthz"
    }
  });
}
