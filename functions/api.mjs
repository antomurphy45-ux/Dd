// Construction Control API entry point.
// Phase 32.47: load the Pyodide sqlite3 package before importing app.py.
import { withLambda } from "@netlify/aws-lambda-compat";

const lambdaHandler = async function handler(event, context) {
  const path = event?.path || event?.rawPath || "/";

  if (path === "/healthz" || path === "/.netlify/functions/api/healthz") {
    return {
      statusCode: 200,
      headers: {
        "content-type": "application/json; charset=utf-8",
        "cache-control": "no-store",
        "x-construction-control-function": "32.47"
      },
      body: JSON.stringify({
        status: "ok",
        platform: "netlify",
        function: "api",
        storage: "netlify-blobs",
        phase: "32.47"
      })
    };
  }

  const implementation = await import("../lib/api-implementation.mjs");
  return implementation.handler(event, context);
};

export default withLambda(lambdaHandler);
