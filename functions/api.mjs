// Construction Control API entry point.
// Phase 32.53: bypass Lambda compatibility so native Response headers,
// especially Set-Cookie, are passed directly through Netlify Functions.
const implementation = await import("../lib/api-implementation.mjs");

export default async function handler(req, context) {
  const headers = new Headers(req.headers);
  const rawUrl = req.url || `https://${headers.get("host") || "localhost"}/`;
  const bytes = new Uint8Array(await req.arrayBuffer());

  const event = {
    path: new URL(rawUrl).pathname,
    rawPath: new URL(rawUrl).pathname,
    rawUrl,
    httpMethod: req.method,
    headers: Object.fromEntries(headers.entries()),
    body: Buffer.from(bytes).toString("base64"),
    isBase64Encoded: true
  };

  const result = await implementation.handler(event, context);

  const responseHeaders = new Headers(result.headers || {});
  responseHeaders.delete("content-length");

  const body = result.isBase64Encoded
    ? Buffer.from(result.body || "", "base64")
    : result.body || "";

  return new Response(body, {
    status: Number(result.statusCode || 200),
    headers: responseHeaders
  });
}
