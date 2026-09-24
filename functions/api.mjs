// Construction Control API entry point.
// Uses Netlify's modern Functions runtime while preserving the existing
// AWS Lambda-style event/response contract through the official compatibility wrapper.
import { withLambda } from "@netlify/aws-lambda-compat";

const lambdaHandler = async function handler(event, context) {
  const path = event?.path || event?.rawPath || "/";

  // Keep a dependency-free health probe. The application/API path below is
  // deliberately separate so a deployment can be verified before Pyodide loads.
  if (path === "/healthz" || path === "/.netlify/functions/api/healthz") {
    return {
      statusCode: 200,
      headers: {
        "content-type": "application/json; charset=utf-8",
        "cache-control": "no-store",
        "x-construction-control-function": "32.42"
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

export default withLambda(lambdaHandler);
