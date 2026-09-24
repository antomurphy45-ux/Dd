// Construction Control Netlify Function entry point.
// CommonJS is used deliberately so Netlify's Lambda runtime can discover
// exports.handler without ESM/Lambda interop ambiguity.
exports.handler = async function handler(event, context) {
  const path = event?.path || event?.rawPath || "/";

  // Keep a dependency-free health probe. This lets Netlify prove that the
  // function itself is deployed before the heavier Pyodide application loads.
  if (path === "/healthz" || path === "/.netlify/functions/api/healthz") {
    return {
      statusCode: 200,
      headers: {
        "content-type": "application/json; charset=utf-8",
        "cache-control": "no-store",
        "x-construction-control-function": "32.38"
      },
      body: JSON.stringify({
        status: "ok",
        platform: "netlify",
        function: "api",
        storage: "netlify-blobs"
      })
    };
  }

  const implementation = await import("../lib/api-implementation.mjs");
  return implementation.handler(event, context);
};
