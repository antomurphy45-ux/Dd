// Construction Control — native Netlify Function entry point.
// Phase 33: Request + Context -> Response.
// No Lambda compatibility layer is used.

import { handleRequest } from "../lib/api-implementation.mjs";

function copyIncomingCookie(req, context) {
  const headers = new Headers(req.headers);
  // app.py's existing adapter uses the canonical Cookie key in a plain dict.
  // Netlify's native cookie API is authoritative for incoming cookies.
  if (!headers.get("cookie") && context?.cookies?.get) {
    const session = context.cookies.get("cc_session");
    if (session) headers.set("Cookie", `cc_session=${session}`);
  } else if (headers.get("cookie")) {
    headers.set("Cookie", headers.get("cookie"));
  }
  return headers;
}

function forwardSessionCookie(response, context) {
  if (!context?.cookies?.set) return;
  const setCookie = response.headers.get("set-cookie");
  if (!setCookie) return;

  const match = setCookie.match(/(?:^|;\s*)cc_session=([^;]*)/);
  if (!match) return;

  const cookie = {
    name: "cc_session",
    value: match[1],
    httpOnly: true,
    sameSite: "strict",
    path: "/"
  };

  const maxAge = setCookie.match(/(?:^|;\s*)Max-Age=(\d+)/i);
  if (maxAge) cookie.maxAge = Number(maxAge[1]);
  if (/(?:^|;\s*)Secure(?:;|$)/i.test(setCookie)) cookie.secure = true;

  context.cookies.set(cookie);
}

export default async function handler(req, context) {
  const headers = copyIncomingCookie(req, context);
  const nativeRequest = new Request(req.url, {
    method: req.method,
    headers,
    body: ["GET", "HEAD"].includes(req.method) ? undefined : await req.arrayBuffer()
  });

  const response = await handleRequest(nativeRequest);
  forwardSessionCookie(response, context);

  // Let Netlify's native cookie API own Set-Cookie delivery. Other response
  // headers and the body are passed through unchanged.
  const responseHeaders = new Headers(response.headers);
  if (responseHeaders.has("set-cookie") && context?.cookies?.set) {
    responseHeaders.delete("set-cookie");
  }
  responseHeaders.delete("content-length");

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders
  });
}
