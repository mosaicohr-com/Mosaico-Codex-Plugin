const PUBLIC_IDENTIFIER = "";
// Mosaico Outreach: is one Lead on LinkedIn's Sent invitations list, and when was the invitation sent.
// Approved capture script. The plugin's browser-script gate allows it only word for word, with the
// first line's value changed to the Lead's public identifier (the part of the profile address after /in/).
// validated: pending. The endpoint below is LinkedIn's long-standing sent-invitations list (the one behind
// the Sent invitations page and its Withdraw links). It has not been run against a live account in this
// work, so the response shape it reads is the documented expectation until a capture confirms it.
// It runs inside the signed-in LinkedIn page: the CSRF token is read here, sent only to that LinkedIn
// endpoint, and never returned. It reads the list newest first, 100 invitations a page, up to five pages,
// until the Lead is found. Each invitation carries its invitee (a MiniProfile with a public identifier)
// and its send time. Only the Lead's own invitation is returned: its send time as an ISO time, the
// invitee's member URN and the invitation URN. Names, messages, pictures and every other invitation are
// dropped before anything leaves the page. state is "found" when the Lead is on the list, "not-found" when
// the pages read do not hold the Lead, and "error" when LinkedIn did not answer or nobody is signed in.
// Any error returns the status, state "error" and no invitation: the script never throws.
// Identifier forms (0.8.6): the first line's value is either a vanity (jane-doe) or an opaque member id (ACoAA...; matched by
// ^ACoAA[A-Za-z0-9_-]+$, the id part of urn:li:fsd_profile:<id>). An opaque id builds the member URN directly
// (urn:li:fsd_profile:<id>) and skips the profile lookup. A vanity is looked up first with the profile query (vanityName):
// the Profile whose publicIdentifier equals the vanity (any case) is used; otherwise, when the response holds exactly one
// Profile entity, it is taken as the redirect target (LinkedIn answers an old vanity with the person's new one); any other
// answer is an error with errorStep "profile". An invitation is the Lead's when its invitee's member id equals the Lead's, or
// when the invitee's publicIdentifier equals the requested or the resolved identifier. Every output carries
// requestedIdentifier (the value as given), resolvedIdentifier (the response's publicIdentifier, or the opaque id) and
// memberUrn (the Lead's member URN, null when it was not resolved).
// Error reporting (0.8.6): state "error" carries status (the HTTP status LinkedIn answered, or 0 when the call itself failed)
// and errorStep: "profile" (the vanity lookup or the identifier it resolved) or "sent-invitations" (the list, no signed-in
// session, or an empty identifier, when nothing could be asked). errorStep is null when state is not "error".
// Text normalisation (0.8.5; the application mirrors this rule): every free-text field that leaves the page is normalised with
// normalizeText before it is hashed and returned, in this order: (1) Unicode NFC; (2) every space separator (U+00A0, U+1680,
// U+2000-U+200A, U+202F, U+205F, U+3000) becomes a plain space; (3) zero-width characters (U+200B-U+200D, U+2060, U+FEFF) are
// removed; (4) CRLF and CR become LF; (5) every other C0 or C1 control character (U+0000-U+001F, U+007F-U+009F) except LF and TAB
// is removed; (6) each run of plain spaces becomes one space; (7) spaces and tabs at the end of each line are removed. URNs, URLs,
// identifiers and timestamps are never touched. The integrity digest is computed after normalisation.
// This script returns no free-text field today, so normalizeText is not applied to any value; it is kept so every approved script carries the same rule.
// Integrity: the result's last field, integrity, is { algorithm: "fnv1a32", digest }: FNV-1a 32-bit over the UTF-8 bytes of
// the canonical JSON (keys sorted, no spaces, with null-valued keys omitted) of everything else the script returns, as 8 lowercase hex characters.
// Pass the whole result to Mosaico exactly as returned: Mosaico recomputes the digest and refuses an altered copy.
const ENDPOINT = "https://www.linkedin.com/voyager/api/relationships/sentInvitationViewsV2";
const PROFILE_ENDPOINT = "https://www.linkedin.com/voyager/api/graphql";
const PROFILE_QUERY_ID = "voyagerIdentityDashProfiles.34ead06db82a2cc9a778fac97f69ad6a";
const OPAQUE_ID = /^ACoAA[A-Za-z0-9_-]+$/;
const PAGE_SIZE = 100;
const MAX_PAGES = 5;
const isObj = (v) => typeof v === "object" && v !== null && !Array.isArray(v);
const canonical = (v) => (Array.isArray(v) ? "[" + v.map((x) => (x === undefined ? "null" : canonical(x))).join(",") + "]" : isObj(v) ? "{" + Object.keys(v).filter((k) => v[k] !== undefined && v[k] !== null).sort().map((k) => JSON.stringify(k) + ":" + canonical(v[k])).join(",") + "}" : JSON.stringify(v));
const fnv1a32 = (s) => { let h = 0x811c9dc5; for (const b of new TextEncoder().encode(s)) { h = Math.imul(h ^ b, 0x01000193) >>> 0; } return h.toString(16).padStart(8, "0"); };
const normalizeText = (s) => String(s).normalize("NFC").replace(/[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000]/g, " ").replace(/[\u200B-\u200D\u2060\uFEFF]/g, "").replace(/\r\n?/g, "\n").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F]/g, "").replace(/ {2,}/g, " ").replace(/[ \t]+(?=\n|$)/g, "");
const typeOf = (e) => (isObj(e) && typeof e["$type"] === "string" ? e["$type"] : "");
const listOf = (v) => (Array.isArray(v) ? v : []);
const text = (v) => (typeof v === "string" && v !== "" ? v : null);
const urnOf = (v) => (typeof v === "string" && /^urn:li:[A-Za-z_]+:[A-Za-z0-9_,:()=.-]+$/.test(v) ? v : null);
const isoOf = (ms) => (typeof ms === "number" && ms > 0 && ms < 8.64e15 ? new Date(ms).toISOString() : null);
const decoded = (v) => { try { return decodeURIComponent(v).toLowerCase(); } catch (e) { return String(v).toLowerCase(); } };
const sameIdentifier = (a, b) => typeof a === "string" && (a.toLowerCase() === b.toLowerCase() || decoded(a) === decoded(b));
const memberUrn = (v) => (typeof v === "string" && /^urn:li:fsd_profile:[A-Za-z0-9_-]+$/.test(v) ? v : null);
const idOf = (v) => { const m = typeof v === "string" ? /^urn:li:(?:fsd_profile|fs_miniProfile):([A-Za-z0-9_-]+)$/.exec(v) : null; return m === null ? null : m[1]; };
const csrf = (document.cookie.match(/JSESSIONID="?([^;"]+)/) || [])[1] || "";
const capturedAt = new Date().toISOString();
const HEADERS = { "csrf-token": csrf, "x-restli-protocol-version": "2.0.0", "accept": "application/vnd.linkedin.normalized+json+2.1" };
let status = 0;
let state = "error";
let errorStep = "sent-invitations";
let resolvedIdentifier = null;
let leadMemberUrn = null;
let invitation = null;
let pagesRead = 0;
try {
  if (csrf !== "" && PUBLIC_IDENTIFIER !== "") {
    errorStep = "profile";
    if (OPAQUE_ID.test(PUBLIC_IDENTIFIER)) {
      leadMemberUrn = "urn:li:fsd_profile:" + PUBLIC_IDENTIFIER;
      resolvedIdentifier = PUBLIC_IDENTIFIER;
    } else {
      const p = await fetch(PROFILE_ENDPOINT + "?includeWebMetadata=true&variables=(vanityName:" + encodeURIComponent(PUBLIC_IDENTIFIER) + ")&queryId=" + PROFILE_QUERY_ID, { credentials: "include", headers: HEADERS });
      status = p.status;
      if (!p.ok) throw p.status;
      const pj = await p.json();
      const profiles = listOf(pj && pj.included).filter((e) => isObj(e) && /profile\.Profile$/.test(typeOf(e)));
      const exact = profiles.filter((e) => typeof e.publicIdentifier === "string" && e.publicIdentifier.toLowerCase() === PUBLIC_IDENTIFIER.toLowerCase());
      const hit = exact.length > 0 ? exact[exact.length - 1] : profiles.length === 1 && typeof profiles[0].publicIdentifier === "string" ? profiles[0] : null;
      if (hit === null || memberUrn(hit.entityUrn) === null) throw null;
      leadMemberUrn = memberUrn(hit.entityUrn);
      resolvedIdentifier = hit.publicIdentifier;
    }
    errorStep = "sent-invitations";
    const leadId = idOf(leadMemberUrn);
    let found = null;
    for (let page = 0; page < MAX_PAGES && found === null; page++) {
      const r = await fetch(ENDPOINT + "?count=" + PAGE_SIZE + "&invitationType=CONNECTION&q=invitationType&start=" + page * PAGE_SIZE, { credentials: "include", headers: HEADERS });
      if (!r.ok) throw r.status;
      const j = await r.json();
      pagesRead = page + 1;
      status = r.status;
      const included = listOf(j && j.included).filter(isObj);
      const byUrn = {};
      for (const e of included) { if (typeof e.entityUrn === "string") byUrn[e.entityUrn] = e; }
      let listed = 0;
      const resolve = (v) => (isObj(v) ? v : typeof v === "string" && isObj(byUrn[v]) ? byUrn[v] : null);
      for (const e of included) {
        if (!/Invitation/.test(typeOf(e))) continue;
        listed++;
        const inner = resolve(e.invitation !== undefined ? e.invitation : e["*invitation"]);
        const inv = inner !== null ? inner : e;
        let invitee = null;
        for (const c of [e.invitee, e["*invitee"], e.toMember, e["*toMember"], inv.invitee, inv["*invitee"], inv.toMember, inv["*toMember"]]) {
          const r2 = resolve(c);
          if (r2 !== null) { invitee = r2; break; }
        }
        if (invitee === null) continue;
        const mini = typeof invitee.publicIdentifier === "string" ? invitee : resolve(invitee.miniProfile !== undefined ? invitee.miniProfile : invitee["*miniProfile"]);
        if (mini === null) continue;
        const sameMember = [mini.dashEntityUrn, invitee.dashEntityUrn, mini.entityUrn, invitee.entityUrn].some((u) => idOf(u) === leadId);
        if (!sameMember && !sameIdentifier(mini.publicIdentifier, PUBLIC_IDENTIFIER) && !sameIdentifier(mini.publicIdentifier, resolvedIdentifier)) continue;
        const sentMs = typeof inv.sentTime === "number" ? inv.sentTime : e.sentTime;
        const sentTime = isoOf(sentMs);
        if (sentTime === null) continue;
        if (found === null || Date.parse(sentTime) > Date.parse(found.sentTime)) {
          found = { sentTime, inviteeUrn: urnOf(mini.dashEntityUrn) || urnOf(invitee.dashEntityUrn) || urnOf(mini.entityUrn) || urnOf(invitee.entityUrn), invitationUrn: urnOf(inv.entityUrn) || urnOf(e.entityUrn) };
        }
      }
      const elements = Math.max(listOf(isObj(j && j.data) ? j.data.elements : null).length, listed);
      if (found === null && elements < PAGE_SIZE) break;
    }
    if (found !== null) { state = "found"; invitation = found; } else { state = "not-found"; }
    errorStep = null;
    status = 200;
  }
} catch (e) { status = typeof e === "number" ? e : e === null ? status : 0; state = "error"; invitation = null; }
const payload = { status, signedIn: csrf !== "", capturedAt, state, errorStep: state === "error" ? errorStep : null, publicIdentifier: PUBLIC_IDENTIFIER, requestedIdentifier: PUBLIC_IDENTIFIER, resolvedIdentifier, memberUrn: leadMemberUrn, invitation, pagesRead };
({ ...payload, integrity: { algorithm: "fnv1a32", digest: fnv1a32(canonical(payload)) } })
