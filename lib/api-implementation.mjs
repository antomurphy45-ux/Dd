import { getStore } from "@netlify/blobs";
import { loadPyodide } from "pyodide";
import { readFile, mkdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const WORK = "/tmp/construction-control";
const DB_FILE = `${WORK}/construction_control.db`;
const UPLOAD_DIR = `${WORK}/uploads`;
const DB_KEY = "database/construction_control.db";
const STORE_NAME = "construction-control";
const REGION = "eu-central-1";

let runtimePromise;
async function runtime() {
  if (!runtimePromise) runtimePromise = (async () => {
    await mkdir(WORK, { recursive: true });
    await mkdir(UPLOAD_DIR, { recursive: true });
    const pyodide = await loadPyodide({
      indexURL: "https://cdn.jsdelivr.net/pyodide/v0.29.5/full/",
    });
    const appPath = path.join(ROOT, "app.py");
    const appSource = await readFile(appPath, "utf8");
    pyodide.FS.writeFile(`${WORK}/app.py`, appSource);
    pyodide.FS.writeFile(`${WORK}/render_seed.db`, await readFile(path.join(ROOT, "netlify_seed.db")));
    await pyodide.runPythonAsync(`
import os, sys
os.environ["CONSTRUCTION_CONTROL_DB"] = ${JSON.stringify(DB_FILE)}
os.environ["CONSTRUCTION_CONTROL_UPLOADS"] = ${JSON.stringify(UPLOAD_DIR)}
os.environ["CONSTRUCTION_CONTROL_BACKUPS"] = ${JSON.stringify(`${WORK}/backups`)}
os.environ["SECURE_COOKIES"] = "1"
os.environ["CONSTRUCTION_CONTROL_NETLIFY"] = "1"
sys.path.insert(0, ${JSON.stringify(WORK)})
`);
    await pyodide.runPythonAsync(`import app`);
    return pyodide;
  })();
  return runtimePromise;
}

function json(status, data, extra={}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", "x-construction-control-function": "32.37", ...extra },
  });
}

function normalizePath(pathname) {
  if (pathname === "/.netlify/functions/api" || pathname === "/.netlify/functions/api/") return "/healthz";
  const prefix = "/.netlify/functions/api/";
  if (pathname.startsWith(prefix)) return "/api/" + pathname.slice(prefix.length);
  return pathname;
}

async function seedIfMissing(store) {
  const existing = await store.getWithMetadata(DB_KEY, { type: "arrayBuffer", consistency: "strong" });
  if (existing?.data) return existing.etag;
  const seed = await readFile(path.join(ROOT, "netlify_seed.db"));
  const result = await store.set(DB_KEY, seed, { metadata: { format: "sqlite", version: "32.37" } });
  return result.etag;
}


async function restoreUploads(store) {
  const listing = await store.list({ prefix: "uploads/" });
  for (const item of listing.blobs || []) {
    const name = item.key.slice("uploads/".length);
    if (!name || name.includes("..") || name.includes("/")) continue;
    const data = await store.get(item.key, { type: "arrayBuffer", consistency: "strong" });
    if (data) await (await import("node:fs/promises")).writeFile(path.join(UPLOAD_DIR, name), new Uint8Array(data));
  }
}

async function syncUploads(store) {
  const { readdir, readFile, unlink } = await import("node:fs/promises");
  const local = new Set(await readdir(UPLOAD_DIR));
  const existing = await store.list({ prefix: "uploads/" });
  for (const item of existing.blobs || []) {
    const name = item.key.slice("uploads/".length);
    if (!local.has(name)) await store.delete(item.key);
  }
  for (const name of local) {
    const bytes = await readFile(path.join(UPLOAD_DIR, name));
    if (bytes.length > 5 * 1024 * 1024) throw new Error(`Upload ${name} exceeds the Netlify Blobs 5 MB value limit`);
    await store.set(`uploads/${name}`, bytes, { metadata: { kind: "construction-control-upload" } });
  }
}

async function loadDatabase(store) {
  const entry = await store.getWithMetadata(DB_KEY, { type: "arrayBuffer", consistency: "strong" });
  if (!entry?.data) {
    const etag = await seedIfMissing(store);
    const seeded = await store.getWithMetadata(DB_KEY, { type: "arrayBuffer", consistency: "strong" });
    return { etag: seeded.etag || etag, bytes: new Uint8Array(seeded.data) };
  }
  return { etag: entry.etag, bytes: new Uint8Array(entry.data) };
}

async function putDatabase(store, bytes, etag) {
  const options = { metadata: { format: "sqlite", version: "32.37" }, onlyIfMatch: etag };
  return store.set(DB_KEY, bytes, options);
}

async function invoke(pyodide, method, pathname, headers, body) {
  pyodide.globals.set("_net_method", method);
  pyodide.globals.set("_net_path", pathname);
  pyodide.globals.set("_net_headers_json", JSON.stringify(Object.fromEntries(headers.entries())));
  pyodide.globals.set("_net_body_b64", Buffer.from(body).toString("base64"));
  const result = await pyodide.runPythonAsync(`
import app, json, base64
_status, _headers, _body = app.netlify_handle(_net_method, _net_path, json.loads(_net_headers_json), base64.b64decode(_net_body_b64))
(_status, _headers, _body)
`);
  const js = result.toJs({ dict_converter: Object.fromEntries });
  result.destroy();
  const status = Number(js[0]);
  const headersOut = js[1] || {};
  const bodyOut = js[2] instanceof Uint8Array ? js[2] : new Uint8Array(js[2]);
  return { status, headers: headersOut, body: bodyOut };
}

async function handleRequest(req) {
  try {
    const url = new URL(req.url);
    const pathname = normalizePath(url.pathname);
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: { "access-control-allow-origin": "*", "access-control-allow-headers": "Content-Type, Cookie", "access-control-allow-methods": "GET,POST,PUT,DELETE,OPTIONS" } });
    if (pathname === "/healthz") return json(200, { status: "ok", platform: "netlify", storage: "netlify-blobs" });
    if (!pathname.startsWith("/api/")) return json(404, { error: "Not found" });

    const store = getStore(STORE_NAME, { region: REGION });
    const requestBody = new Uint8Array(await req.arrayBuffer());
    let attempts = 0;
    while (attempts++ < 3) {
      const db = await loadDatabase(store);
      const py = await runtime();
      await restoreUploads(store);
      py.FS.writeFile(DB_FILE, db.bytes);
      const result = await invoke(py, req.method, pathname + url.search, req.headers, requestBody);
      const updated = new Uint8Array(py.FS.readFile(DB_FILE));
      const saved = await putDatabase(store, updated, db.etag);
      await syncUploads(store);
      if (saved?.modified) {
        const headers = new Headers(result.headers);
        headers.delete("content-length");
        return new Response(result.body, { status: result.status, headers });
      }
      // Another invocation updated the database. Retry the same request against the latest state.
    }
    return json(409, { error: "Database was updated concurrently. Please retry the request." });
  } catch (error) {
    console.error("Construction Control API error", error);
    return json(500, { error: "Server error while processing the request. Check the Netlify Function logs." });
  }
};

export async function invokeLambda(event) {
  const headers = new Headers(event?.headers || {});
  const rawUrl = event?.rawUrl || `https://${headers.get("host") || "localhost"}${event?.path || "/"}`;
  let body = new Uint8Array();
  if (event?.body) {
    const decoded = event.isBase64Encoded
      ? Buffer.from(event.body, "base64")
      : Buffer.from(event.body, "utf8");
    body = new Uint8Array(decoded);
  }
  const req = new Request(rawUrl, {
    method: event?.httpMethod || "GET",
    headers,
    body: ["GET", "HEAD"].includes(event?.httpMethod || "GET") ? undefined : body,
  });
  const response = await handleRequest(req);
  const responseBytes = new Uint8Array(await response.arrayBuffer());
  return {
    statusCode: response.status,
    headers: Object.fromEntries(response.headers.entries()),
    body: Buffer.from(responseBytes).toString("base64"),
    isBase64Encoded: true,
  };
}

export async function handler(event) {
  return invokeLambda(event);
}

export const config = {
  path: ["/api/*", "/healthz"],
  memory: "2gb",
};
