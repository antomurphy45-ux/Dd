// Dependency-free Netlify deployment probe for Construction Control.
exports.handler = async function handler() {
  return {
    statusCode: 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-construction-control-function": "32.38-healthz"
    },
    body: JSON.stringify({
      status: "ok",
      platform: "netlify",
      function: "healthz",
      storage: "netlify-blobs"
    })
  };
};
