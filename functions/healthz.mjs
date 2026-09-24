// Dependency-free Netlify deployment probe for Construction Control.
// Exported through the modern Functions runtime so Netlify platform context,
// including Blobs primitives, is available consistently to this project.
export default async function handler() {
  return new Response(JSON.stringify({
    status: "ok",
    platform: "netlify",
    function: "healthz",
    storage: "netlify-blobs"
  }), {
    status: 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-construction-control-function": "32.41-healthz"
    }
  });
}
