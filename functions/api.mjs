// Construction Control API entry point.
// Phase 32.54: use Netlify's native context.cookies API for the session cookie.
// This removes ambiguity around Set-Cookie forwarding through the Lambda-shaped adapter.
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
  const setCookie = responseHeaders.get("set-cookie");

  // Phase 32.54: Netlify Functions provide a native cookie API.
  // Use it explicitly for cc_session so the browser receives the session
  // even if an adapter/Headers conversion would otherwise drop Set-Cookie.
  if (setCookie && context?.cookies?.set) {
    const match = setCookie.match(/(?:^|;\\s*)cc_session=([^;]*)/);
    if (match) {
      const cookie = {
        name: "cc_session",
        value: match[1],
        httpOnly: true,
        sameSite: "strict",
        path: "/"
      };

      const maxAge = setCookie.match(/(?:^|;\\s*)Max-Age=(\\d+)/i);
      if (maxAge) cookie.maxAge = Number(maxAge[1]);

      if (/(?:^|;\\s*)Secure(?:;|$)/i.test(setCookie)) {
        cookie.secure = true;
      }

      context.cookies.set(cookie);
      responseHeaders.delete("set-cookie");
    }
  }

  responseHeaders.delete("content-length");

  const body = result.isBase64Encoded
    ? Buffer.from(result.body || "", "base64")
    : result.body || "";

  return new Response(body, {
    status: Number(result.statusCode || 200),
    headers: responseHeaders
  });
}
