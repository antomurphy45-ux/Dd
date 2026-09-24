import { getStore } from "@netlify/blobs";
import { loadPyodide } from "pyodide";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { scryptSync } from "node:crypto";

const ROOT = path.resolve(process.env.LAMBDA_TASK_ROOT || process.cwd());
const WORK = "/tmp/construction-control";
const DB_FILE = `${WORK}/construction_control.db`;
const UPLOAD_DIR = `${WORK}/uploads`;
const PYODIDE_CACHE = "/tmp/pyodide-package-cache";
const DB_KEY = "database/construction_control.db";
const STORE_NAME = "construction-control";
const REGION = "eu-central-1";

// Phase 32.52: Pyodide does not expose OpenSSL-backed hashlib.scrypt.
// Override the application's password helpers directly so init_db() and
// password repair use Node's native scrypt while preserving the existing
// salt:digest database format.
function nodeScrypt(passwordB64, saltB64, n, r, p, dklen) {
  const key = scryptSync(
    Buffer.from(passwordB64, "base64"),
    Buffer.from(saltB64, "base64"),
    Number(dklen || 64),
    { N: Number(n), r: Number(r), p: Number(p), maxmem: 64 * 1024 * 1024 }
  );
  return key.toString("base64");
}

function blobStore() {
  const siteID = process.env.CONSTRUCTION_CONTROL_SITE_ID || process.env.SITE_ID || process.env.NETLIFY_SITE_ID;
  const token = process.env.CONSTRUCTION_CONTROL_BLOBS_TOKEN || process.env.NETLIFY_AUTH_TOKEN || process.env.NETLIFY_BLOBS_TOKEN;
  try { return getStore(STORE_NAME, { region: REGION }); }
  catch (automaticError) {
    if (siteID && token) return getStore(STORE_NAME, { region: REGION, siteID, token });
    const missing = [!siteID ? "SITE_ID" : null, !token ? "NETLIFY_AUTH_TOKEN" : null].filter(Boolean).join(", ");
    throw new Error(`Netlify Blobs automatic Function context is unavailable (missing explicit fallback: ${missing || "none"}). ${automaticError?.message || automaticError}`);
  }
}

let runtimePromise;
async function runtime() {
  if (!runtimePromise) runtimePromise = (async () => {
    await mkdir(WORK, { recursive: true });
    await mkdir(UPLOAD_DIR, { recursive: true });
    await mkdir(PYODIDE_CACHE, { recursive: true });
    const pyodide = await loadPyodide({ packageCacheDir: PYODIDE_CACHE });
    pyodide.FS.mkdirTree(WORK);
    pyodide.FS.mkdirTree(UPLOAD_DIR);
    pyodide.FS.mkdirTree(`${WORK}/backups`);
    const appPath = path.join(ROOT, "app.py");
    pyodide.FS.writeFile(`${WORK}/app.py`, await readFile(appPath, "utf8"));
    pyodide.FS.writeFile(`${WORK}/render_seed.db`, await readFile(path.join(ROOT, "netlify_seed.db")));
    await pyodide.loadPackage("sqlite3");
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
  return new Response(JSON.stringify(data), { status, headers: { "content-type":"application/json; charset=utf-8", "cache-control":"no-store", "x-construction-control-function":"32.52", ...extra } });
}
function normalizePath(pathname) {
  if (pathname === "/.netlify/functions/api" || pathname === "/.netlify/functions/api/") return "/healthz";
  const prefix = "/.netlify/functions/api/";
  if (pathname.startsWith(prefix)) return "/api/" + pathname.slice(prefix.length);
  return pathname;
}
async function seedIfMissing(store) {
  const existing = await store.getWithMetadata(DB_KEY, { type:"arrayBuffer", consistency:"strong" });
  if (existing?.data) return existing.etag;
  const seed = await readFile(path.join(ROOT, "netlify_seed.db"));
  const result = await store.set(DB_KEY, seed, { metadata:{format:"sqlite",version:"32.52"} });
  return result.etag;
}
async function restoreUploads(store) {
  const listing = await store.list({ prefix:"uploads/" });
  for (const item of listing.blobs || []) {
    const name = item.key.slice("uploads/".length);
    if (!name || name.includes("..") || name.includes("/")) continue;
    const data = await store.get(item.key, { type:"arrayBuffer", consistency:"strong" });
    if (data) await writeFile(path.join(UPLOAD_DIR, name), new Uint8Array(data));
  }
}
async function syncUploads(store) {
  const { readdir, readFile } = await import("node:fs/promises");
  const local = new Set(await readdir(UPLOAD_DIR));
  const existing = await store.list({ prefix:"uploads/" });
  for (const item of existing.blobs || []) {
    const name = item.key.slice("uploads/".length);
    if (!local.has(name)) await store.delete(item.key);
  }
  for (const name of local) {
    const bytes = await readFile(path.join(UPLOAD_DIR, name));
    if (bytes.length > 5 * 1024 * 1024) throw new Error(`Upload ${name} exceeds the Netlify Blobs 5 MB value limit`);
    await store.set(`uploads/${name}`, bytes, { metadata:{kind:"construction-control-upload"} });
  }
}
async function loadDatabase(store) {
  const entry = await store.getWithMetadata(DB_KEY, { type:"arrayBuffer", consistency:"strong" });
  if (!entry?.data) {
    const etag = await seedIfMissing(store);
    const seeded = await store.getWithMetadata(DB_KEY, { type:"arrayBuffer", consistency:"strong" });
    return { etag: seeded.etag || etag, bytes:new Uint8Array(seeded.data) };
  }
  return { etag:entry.etag, bytes:new Uint8Array(entry.data) };
}
async function putDatabase(store, bytes, etag) {
  return store.set(DB_KEY, bytes, { metadata:{format:"sqlite",version:"32.52"}, onlyIfMatch:etag });
}

// Phase 32.52: replace app.pw_hash/pw_ok directly rather than monkey-patching
// hashlib.scrypt. This avoids Pyodide's removed OpenSSL hashlib implementation.
async function initializePersistentDatabase(pyodide) {
  pyodide.globals.set("_node_scrypt", nodeScrypt);
  await pyodide.runPythonAsync(`
import app, base64, hmac, secrets

def _node_kdf(password_bytes, salt_bytes, n=2**14, r=8, p=1, dklen=64):
    password_b64 = base64.b64encode(bytes(password_bytes)).decode("ascii")
    salt_b64 = base64.b64encode(bytes(salt_bytes)).decode("ascii")
    result_b64 = _node_scrypt(password_b64, salt_b64, int(n), int(r), int(p), int(dklen))
    return base64.b64decode(result_b64)

def _netlify_pw_hash(password):
    salt = secrets.token_bytes(16)
    digest = _node_kdf(password.encode(), salt, 2**14, 8, 1, 64)
    return salt.hex() + ":" + digest.hex()

def _netlify_pw_ok(password, stored):
    try:
        salt, digest = stored.split(":")
        got = _node_kdf(password.encode(), bytes.fromhex(salt), 2**14, 8, 1, 64).hex()
        return hmac.compare_digest(got, digest)
    except Exception:
        return False

app.pw_hash = _netlify_pw_hash
app.pw_ok = _netlify_pw_ok

# Run the normal idempotent schema/migration/seed logic against the restored
# persistent database. It now uses the Node-backed password helpers above.
app.init_db()

# Repair the built-in demo accounts in an existing persistent database.
# Existing demo accounts keep their known demo password; other users are untouched.
c = app.db()
try:
    demo_users = [
        ("U1", "C1", "Company Owner", "owner@demo.local", "Company Administrator"),
        ("U2", "C1", "Construction Manager", "manager@demo.local", "Construction Manager"),
        ("U3", "C2", "Site User", "site@demo.local", "Site User"),
    ]
    for uid, company_id, name, email, role in demo_users:
        existing = c.execute("SELECT id,password_hash,active FROM users WHERE lower(email)=lower(?)", (email,)).fetchone()
        if existing:
            if not existing[2] or not app.pw_ok("DemoPass!123", existing[1]):
                c.execute("UPDATE users SET password_hash=?, active=1 WHERE id=?", (app.pw_hash("DemoPass!123"), existing[0]))
            continue
        if not c.execute("SELECT 1 FROM companies WHERE id=?", (company_id,)).fetchone():
            continue
        new_id = uid
        if c.execute("SELECT 1 FROM users WHERE id=?", (new_id,)).fetchone():
            new_id = "DEMO-" + email.split("@")[0].upper()
        c.execute(
            "INSERT INTO users(id,company_id,name,email,password_hash,active,role) VALUES(?,?,?,?,?,?,?)",
            (new_id, company_id, name, email, app.pw_hash("DemoPass!123"), 1, role)
        )
    c.commit()
finally:
    c.close()
`);

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
  const js = result.toJs({ dict_converter:Object.fromEntries });
  result.destroy();
  const status = Number(js[0]);
  const headersOut = js[1] || {};
  const bodyOut = js[2] instanceof Uint8Array ? js[2] : new Uint8Array(js[2]);
  return { status, headers:headersOut, body:bodyOut };
}

async function handleRequest(req) {
  try {
    const url = new URL(req.url);
    const pathname = normalizePath(url.pathname);
    if (req.method === "OPTIONS") return new Response(null,{status:204,headers:{"access-control-allow-origin":"*","access-control-allow-headers":"Content-Type, Cookie","access-control-allow-methods":"GET,POST,PUT,DELETE,OPTIONS"}});
    if (pathname === "/healthz") return json(200,{status:"ok",platform:"netlify",storage:"netlify-blobs",phase:"32.52"});
    if (!pathname.startsWith("/api/")) return json(404,{error:"Not found"});
    const store = blobStore();
    const requestBody = new Uint8Array(await req.arrayBuffer());
    let attempts=0;
    while (attempts++ < 3) {
      const db = await loadDatabase(store);
      const py = await runtime();
      await restoreUploads(store);
      py.FS.writeFile(DB_FILE, db.bytes);
      await initializePersistentDatabase(py);
      const result = await invoke(py, req.method, pathname + url.search, req.headers, requestBody);
      const updated = new Uint8Array(py.FS.readFile(DB_FILE));
      const saved = await putDatabase(store, updated, db.etag);
      await syncUploads(store);
      if (saved?.modified) {
        const headers = new Headers(result.headers);
        headers.delete("content-length");
        return new Response(result.body,{status:result.status,headers});
      }
    }
    return json(409,{error:"Database was updated concurrently. Please retry the request."});
  } catch (error) {
    console.error("Construction Control API error", error);
    return json(500,{error:"Server error while processing the request. Check the Netlify Function logs."});
  }
}
export async function invokeLambda(event) {
  const headers = new Headers(event?.headers || {});
  const rawUrl = event?.rawUrl || `https://${headers.get("host") || "localhost"}${event?.path || "/"}`;
  let body = new Uint8Array();
  if (event?.body) body = new Uint8Array(event.isBase64Encoded ? Buffer.from(event.body,"base64") : Buffer.from(event.body,"utf8"));
  const req = new Request(rawUrl,{method:event?.httpMethod || "GET",headers,body:["GET","HEAD"].includes(event?.httpMethod || "GET") ? undefined : body});
  const response = await handleRequest(req);
  const responseBytes = new Uint8Array(await response.arrayBuffer());
  return {statusCode:response.status,headers:Object.fromEntries(response.headers.entries()),body:Buffer.from(responseBytes).toString("base64"),isBase64Encoded:true};
}
export async function handler(event){ return invokeLambda(event); }
export const config = { path:["/api/*","/healthz"], memory:"2gb" };
