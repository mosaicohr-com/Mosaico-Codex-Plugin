const NOOP = 0;
// Mosaico Outreach: who the signed-in LinkedIn account is.
// Approved capture script. The plugin's browser-script gate allows it only word for word, with the
// first line's value changed. It runs inside the signed-in LinkedIn page: the CSRF token is read here,
// sent only to LinkedIn's own "who am I" call, and never returned. The result carries only the
// identifiers Mosaico compares (numeric id, type, URNs, public identifier); names, pictures, headlines
// and every other field are dropped before anything leaves the page.
// Text normalisation (0.8.5; the application mirrors this rule): every free-text field that leaves the page is normalised with
// normalizeText before it is hashed and returned, in this order: (1) Unicode NFC; (2) every space separator (U+00A0, U+1680,
// U+2000-U+200A, U+202F, U+205F, U+3000) becomes a plain space; (3) zero-width characters (U+200B-U+200D, U+2060, U+FEFF) are
// removed; (4) CRLF and CR become LF; (5) every other C0 or C1 control character (U+0000-U+001F, U+007F-U+009F) except LF and TAB
// is removed; (6) each run of plain spaces becomes one space; (7) spaces and tabs at the end of each line are removed. URNs, URLs,
// identifiers and timestamps are never touched. The integrity digest is computed after normalisation.
// This script returns no free-text field today, so normalizeText is not applied to any value; it is kept so every approved script carries the same rule.
// Integrity: the result's last field, integrity, is { algorithm: "fnv1a32", digest }: FNV-1a 32-bit over the UTF-8 bytes of
// the canonical JSON (keys sorted, no spaces) of everything else the script returns, as 8 lowercase hex characters.
// Pass the whole result to Mosaico exactly as returned: Mosaico recomputes the digest and refuses an altered copy.
const ENDPOINT = "https://www.linkedin.com/voyager/api/me";
const isObj = (v) => typeof v === "object" && v !== null && !Array.isArray(v);
const canonical = (v) => (Array.isArray(v) ? "[" + v.map((x) => (x === undefined ? "null" : canonical(x))).join(",") + "]" : isObj(v) ? "{" + Object.keys(v).filter((k) => v[k] !== undefined).sort().map((k) => JSON.stringify(k) + ":" + canonical(v[k])).join(",") + "}" : JSON.stringify(v));
const fnv1a32 = (s) => { let h = 0x811c9dc5; for (const b of new TextEncoder().encode(s)) { h = Math.imul(h ^ b, 0x01000193) >>> 0; } return h.toString(16).padStart(8, "0"); };
const normalizeText = (s) => String(s).normalize("NFC").replace(/[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000]/g, " ").replace(/[\u200B-\u200D\u2060\uFEFF]/g, "").replace(/\r\n?/g, "\n").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F]/g, "").replace(/ {2,}/g, " ").replace(/[ \t]+(?=\n|$)/g, "");
const typeOf = (e) => (isObj(e) && typeof e["$type"] === "string" ? e["$type"] : "");
const keep = (src, keys) => { const out = {}; for (const k of keys) { if (src[k] !== undefined) out[k] = src[k]; } return out; };
const csrf = (document.cookie.match(/JSESSIONID="?([^;"]+)/) || [])[1] || "";
const capturedAt = new Date().toISOString();
let status = 0;
let plainId = null;
let entries = [];
try {
  const r = await fetch(ENDPOINT, { credentials: "include", headers: { "csrf-token": csrf, "x-restli-protocol-version": "2.0.0", "accept": "application/vnd.linkedin.normalized+json+2.1" } });
  status = r.status;
  if (r.ok) {
    const j = await r.json();
    plainId = isObj(j && j.data) && typeof j.data.plainId === "number" ? j.data.plainId : null;
    for (const e of Array.isArray(j && j.included) ? j.included : []) {
      if (isObj(e) && /MiniProfile$/.test(typeOf(e))) entries.push(keep(e, ["$type", "entityUrn", "dashEntityUrn", "publicIdentifier"]));
    }
  }
} catch (e) { status = 0; plainId = null; entries = []; }
const payload = { status, signedIn: csrf !== "", capturedAt, plainId, entries };
({ ...payload, integrity: { algorithm: "fnv1a32", digest: fnv1a32(canonical(payload)) } })
