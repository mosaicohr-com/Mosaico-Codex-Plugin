const NOOP = 0;
// Mosaico Outreach: who the signed-in LinkedIn account is.
// Approved capture script. The plugin's browser-script gate allows it only word for word, with the
// first line's value changed. It runs inside the signed-in LinkedIn page: the CSRF token is read here,
// sent only to LinkedIn's own "who am I" call, and never returned. The result carries only the
// identifiers Mosaico compares (numeric id, type, URNs, public identifier); names, pictures, headlines
// and every other field are dropped before anything leaves the page.
const ENDPOINT = "https://www.linkedin.com/voyager/api/me";
const isObj = (v) => typeof v === "object" && v !== null && !Array.isArray(v);
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
({ status, signedIn: csrf !== "", capturedAt, plainId, entries })
