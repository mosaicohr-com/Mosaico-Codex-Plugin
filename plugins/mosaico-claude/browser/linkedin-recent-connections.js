const STOP_AT = 0;
// Mosaico Outreach: the owner's recent connections, newest first, until Mosaico's stop marker.
// Approved capture script. The plugin's browser-script gate allows it only word for word, with the
// first line's value changed. It runs inside the signed-in LinkedIn page: the CSRF token is read here,
// sent only to LinkedIn's own connections list, and never returned. Each page carries LinkedIn's own
// list order plus only the fields Mosaico's snapshot parser reads (type, URN, created time, member
// link, public identifier); names, headlines and every other field are dropped before anything leaves
// the page. Each page is sealed on its own (its own integrity field) as well as in the whole result.
// Integrity: the result's last field, integrity, is { algorithm: "fnv1a32", digest }: FNV-1a 32-bit over the UTF-8 bytes of
// the canonical JSON (keys sorted, no spaces) of everything else the script returns, as 8 lowercase hex characters.
// Pass the whole result to Mosaico exactly as returned: Mosaico recomputes the digest and refuses an altered copy.
const ENDPOINT = "https://www.linkedin.com/voyager/api/relationships/dash/connections";
const PAGE_SIZE = 40;
const MAX_PAGES = 5;
const isObj = (v) => typeof v === "object" && v !== null && !Array.isArray(v);
const canonical = (v) => (Array.isArray(v) ? "[" + v.map((x) => (x === undefined ? "null" : canonical(x))).join(",") + "]" : isObj(v) ? "{" + Object.keys(v).filter((k) => v[k] !== undefined).sort().map((k) => JSON.stringify(k) + ":" + canonical(v[k])).join(",") + "}" : JSON.stringify(v));
const fnv1a32 = (s) => { let h = 0x811c9dc5; for (const b of new TextEncoder().encode(s)) { h = Math.imul(h ^ b, 0x01000193) >>> 0; } return h.toString(16).padStart(8, "0"); };
const sealed = (o) => ({ ...o, integrity: { algorithm: "fnv1a32", digest: fnv1a32(canonical(o)) } });
const typeOf = (e) => (isObj(e) && typeof e["$type"] === "string" ? e["$type"] : "");
const keep = (src, keys) => { const out = {}; for (const k of keys) { if (src[k] !== undefined) out[k] = src[k]; } return out; };
const csrf = (document.cookie.match(/JSESSIONID="?([^;"]+)/) || [])[1] || "";
const H = { "csrf-token": csrf, "x-restli-protocol-version": "2.0.0", "accept": "application/vnd.linkedin.normalized+json+2.1" };
const capturedAt = new Date().toISOString();
const pages = [];
let start = 0;
let done = false;
let status = 0;
try {
  while (!done && pages.length < MAX_PAGES) {
    const r = await fetch(ENDPOINT + "?decorationId=com.linkedin.voyager.dash.deco.web.mynetwork.ConnectionListWithProfile-16&count=" + PAGE_SIZE + "&q=search&sortType=RECENTLY_ADDED&start=" + start, { credentials: "include", headers: H });
    status = r.status;
    if (!r.ok) break;
    const j = await r.json();
    const elements = (isObj(j.data) && Array.isArray(j.data["*elements"]) ? j.data["*elements"] : []).filter((x) => typeof x === "string");
    const entries = [];
    for (const e of Array.isArray(j.included) ? j.included : []) {
      if (!isObj(e)) continue;
      if (/relationships\.Connection$/.test(typeOf(e))) entries.push(keep(e, ["$type", "entityUrn", "createdAt", "*connectedMemberResolutionResult"]));
      else if (typeof e.publicIdentifier === "string" && /profile\.Profile$/.test(typeOf(e))) entries.push(keep(e, ["$type", "entityUrn", "publicIdentifier"]));
    }
    pages.push(sealed({ elements, entries }));
    const created = entries.filter((e) => /relationships\.Connection$/.test(typeOf(e))).map((e) => (typeof e.createdAt === "number" ? e.createdAt : 0));
    const oldest = created.length ? Math.min(...created) : 0;
    done = elements.length < PAGE_SIZE || oldest <= STOP_AT;
    start += PAGE_SIZE;
  }
} catch (e) { status = 0; }
const payload = { status, signedIn: csrf !== "", capturedAt, pages };
({ ...payload, integrity: { algorithm: "fnv1a32", digest: fnv1a32(canonical(payload)) } })
