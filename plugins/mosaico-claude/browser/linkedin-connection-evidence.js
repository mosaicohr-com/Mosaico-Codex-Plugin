const PUBLIC_IDENTIFIER = "PUBLIC_IDENTIFIER";
// Mosaico Outreach: connection evidence for one profile.
// Approved capture script. The plugin's browser-script gate allows it only word for word, with the
// first line's value changed. It runs inside the signed-in LinkedIn page: the CSRF token is read here,
// sent only to LinkedIn's own profile query, and never returned. The result carries only the fields
// Mosaico's evidence parser reads (type, URN, public identifier, relationship state); names, headlines
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
const ENDPOINT = "https://www.linkedin.com/voyager/api/graphql";
const QUERY_ID = "voyagerIdentityDashProfiles.34ead06db82a2cc9a778fac97f69ad6a";
const isObj = (v) => typeof v === "object" && v !== null && !Array.isArray(v);
const canonical = (v) => (Array.isArray(v) ? "[" + v.map((x) => (x === undefined ? "null" : canonical(x))).join(",") + "]" : isObj(v) ? "{" + Object.keys(v).filter((k) => v[k] !== undefined).sort().map((k) => JSON.stringify(k) + ":" + canonical(v[k])).join(",") + "}" : JSON.stringify(v));
const fnv1a32 = (s) => { let h = 0x811c9dc5; for (const b of new TextEncoder().encode(s)) { h = Math.imul(h ^ b, 0x01000193) >>> 0; } return h.toString(16).padStart(8, "0"); };
const normalizeText = (s) => String(s).normalize("NFC").replace(/[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000]/g, " ").replace(/[\u200B-\u200D\u2060\uFEFF]/g, "").replace(/\r\n?/g, "\n").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F]/g, "").replace(/ {2,}/g, " ").replace(/[ \t]+(?=\n|$)/g, "");
const typeOf = (e) => (isObj(e) && typeof e["$type"] === "string" ? e["$type"] : "");
const keep = (src, keys) => { const out = {}; for (const k of keys) { if (src[k] !== undefined) out[k] = src[k]; } return out; };
const marker = (v) => (isObj(v) ? {} : v);
const reduceInvitationBox = (box) => {
  // The box holds exactly one of `invitation` (with its state) or `noInvitation`; both are kept as sent.
  if (!isObj(box)) return box;
  const out = keep(box, ["invitation", "noInvitation"]);
  if (isObj(out.invitation)) out.invitation = keep(out.invitation, ["invitationState", "invitationId"]);
  if ("noInvitation" in out) out.noInvitation = marker(out.noInvitation);
  return out;
};
const reduceNoConnection = (nc) => {
  if (!isObj(nc)) return nc;
  const out = keep(nc, ["memberDistance", "invitation"]);
  if ("invitation" in out) out.invitation = reduceInvitationBox(out.invitation);
  return out;
};
const reduceRelationship = (e) => {
  const out = keep(e, ["$type", "entityUrn"]);
  const body = e.memberRelationship;
  if (!isObj(body)) { if (body !== undefined) out.memberRelationship = body; return out; }
  const b = keep(body, ["self", "connection", "*connection", "noConnection"]);
  if ("self" in b) b.self = marker(b.self);
  if ("connection" in b) b.connection = marker(b.connection);
  if ("noConnection" in b) b.noConnection = reduceNoConnection(b.noConnection);
  out.memberRelationship = b;
  return out;
};
const reduceProfile = (e) => keep(e, ["$type", "publicIdentifier", "entityUrn"]);
const csrf = (document.cookie.match(/JSESSIONID="?([^;"]+)/) || [])[1] || "";
const capturedAt = new Date().toISOString();
let status = 0;
let included = [];
try {
  const r = await fetch(ENDPOINT + "?includeWebMetadata=true&variables=(vanityName:" + encodeURIComponent(PUBLIC_IDENTIFIER) + ")&queryId=" + QUERY_ID, { credentials: "include", headers: { "csrf-token": csrf, "x-restli-protocol-version": "2.0.0", "accept": "application/vnd.linkedin.normalized+json+2.1" } });
  status = r.status;
  if (r.ok) { const j = await r.json(); included = Array.isArray(j && j.included) ? j.included : []; }
} catch (e) { status = 0; }
const entries = [];
for (const e of included) {
  if (!isObj(e)) continue;
  if (/MemberRelationship$/.test(typeOf(e))) entries.push(reduceRelationship(e));
  else if (e.publicIdentifier === PUBLIC_IDENTIFIER && /profile\.Profile$/.test(typeOf(e))) entries.push(reduceProfile(e));
}
const payload = { status, signedIn: csrf !== "", capturedAt, profileIdentifier: PUBLIC_IDENTIFIER, entries };
({ ...payload, integrity: { algorithm: "fnv1a32", digest: fnv1a32(canonical(payload)) } })
