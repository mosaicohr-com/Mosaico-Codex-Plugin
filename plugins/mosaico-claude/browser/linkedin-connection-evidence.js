const PUBLIC_IDENTIFIER = "PUBLIC_IDENTIFIER";
// Mosaico Outreach: connection evidence for one profile.
// Approved capture script. The plugin's browser-script gate allows it only word for word, with the
// first line's value changed. It runs inside the signed-in LinkedIn page: the CSRF token is read here,
// sent only to LinkedIn's own profile query, and never returned. The result carries only the fields
// Mosaico's evidence parser reads (type, URN, public identifier, relationship state); names, headlines
// and every other field are dropped before anything leaves the page.
// Identifier forms (0.8.6): the first line's value is either a vanity (jane-doe) or an opaque member id (ACoAA...; matched by
// ^ACoAA[A-Za-z0-9_-]+$, the id part of urn:li:fsd_profile:<id>). The profile query takes the value as its vanityName in both
// cases (the Voyager document documents no URN form of this query; LinkedIn accepts a member id there). For an opaque id the
// Profile entity is accepted only when the id of its entityUrn equals the requested id. For a vanity, the Profile entity whose
// publicIdentifier equals the vanity (any case) is used; otherwise, when the response holds exactly one Profile entity, it is
// taken as the redirect target (LinkedIn answers an old vanity with the person's new one); any other answer is an error.
// Output (0.8.6): state "ok" or "error"; errorStep "profile" when state is "error" (null otherwise); requestedIdentifier (the value
// as given), resolvedIdentifier (the response's publicIdentifier, or the opaque id) and memberUrn (urn:li:fsd_profile:<id>); all
// three are null when the Profile was not resolved. status is the HTTP status LinkedIn answered, or 0 when the call itself failed.
// On "error", entries is empty: the script never throws and never returns relationship entries it could not tie to the Profile.
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
const OPAQUE_ID = /^ACoAA[A-Za-z0-9_-]+$/;
const memberUrn = (v) => (typeof v === "string" && /^urn:li:fsd_profile:[A-Za-z0-9_-]+$/.test(v) ? v : null);
const resolveProfile = (profiles, requested) => {
  if (OPAQUE_ID.test(requested)) return profiles.find((e) => memberUrn(e.entityUrn) === "urn:li:fsd_profile:" + requested) || null;
  const exact = profiles.filter((e) => typeof e.publicIdentifier === "string" && e.publicIdentifier.toLowerCase() === requested.toLowerCase());
  if (exact.length > 0) return exact[exact.length - 1];
  return profiles.length === 1 && typeof profiles[0].publicIdentifier === "string" ? profiles[0] : null;
};
const csrf = (document.cookie.match(/JSESSIONID="?([^;"]+)/) || [])[1] || "";
const capturedAt = new Date().toISOString();
let status = 0;
let included = [];
try {
  const r = await fetch(ENDPOINT + "?includeWebMetadata=true&variables=(vanityName:" + encodeURIComponent(PUBLIC_IDENTIFIER) + ")&queryId=" + QUERY_ID, { credentials: "include", headers: { "csrf-token": csrf, "x-restli-protocol-version": "2.0.0", "accept": "application/vnd.linkedin.normalized+json+2.1" } });
  status = r.status;
  if (r.ok) { const j = await r.json(); included = Array.isArray(j && j.included) ? j.included : []; }
} catch (e) { status = typeof e === "number" ? e : 0; included = []; }
const resolved = status >= 200 && status < 300 ? resolveProfile(included.filter((e) => isObj(e) && /profile\.Profile$/.test(typeOf(e))), PUBLIC_IDENTIFIER) : null;
const leadUrn = resolved === null ? null : memberUrn(resolved.entityUrn);
const entries = [];
if (resolved !== null && leadUrn !== null) {
  for (const e of included) {
    if (!isObj(e)) continue;
    if (/MemberRelationship$/.test(typeOf(e))) entries.push(reduceRelationship(e));
    else if (e === resolved) entries.push(reduceProfile(e));
  }
}
const ok = resolved !== null && leadUrn !== null;
const payload = { status, signedIn: csrf !== "", capturedAt, state: ok ? "ok" : "error", errorStep: ok ? null : "profile", profileIdentifier: PUBLIC_IDENTIFIER, requestedIdentifier: PUBLIC_IDENTIFIER, resolvedIdentifier: ok ? (OPAQUE_ID.test(PUBLIC_IDENTIFIER) ? PUBLIC_IDENTIFIER : resolved.publicIdentifier) : null, memberUrn: ok ? leadUrn : null, entries };
({ ...payload, integrity: { algorithm: "fnv1a32", digest: fnv1a32(canonical(payload)) } })
