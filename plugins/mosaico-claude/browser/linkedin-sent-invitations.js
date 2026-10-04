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
const ENDPOINT = "https://www.linkedin.com/voyager/api/relationships/sentInvitationViewsV2";
const PAGE_SIZE = 100;
const MAX_PAGES = 5;
const isObj = (v) => typeof v === "object" && v !== null && !Array.isArray(v);
const typeOf = (e) => (isObj(e) && typeof e["$type"] === "string" ? e["$type"] : "");
const listOf = (v) => (Array.isArray(v) ? v : []);
const text = (v) => (typeof v === "string" && v !== "" ? v : null);
const urnOf = (v) => (typeof v === "string" && /^urn:li:[A-Za-z_]+:[A-Za-z0-9_,:()=.-]+$/.test(v) ? v : null);
const isoOf = (ms) => (typeof ms === "number" && ms > 0 && ms < 8.64e15 ? new Date(ms).toISOString() : null);
const decoded = (v) => { try { return decodeURIComponent(v).toLowerCase(); } catch (e) { return String(v).toLowerCase(); } };
const sameIdentifier = (a, b) => typeof a === "string" && (a.toLowerCase() === b.toLowerCase() || decoded(a) === decoded(b));
const csrf = (document.cookie.match(/JSESSIONID="?([^;"]+)/) || [])[1] || "";
const capturedAt = new Date().toISOString();
const HEADERS = { "csrf-token": csrf, "x-restli-protocol-version": "2.0.0", "accept": "application/vnd.linkedin.normalized+json+2.1" };
let status = 0;
let state = "error";
let invitation = null;
let pagesRead = 0;
try {
  if (csrf !== "" && PUBLIC_IDENTIFIER !== "") {
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
        if (mini === null || !sameIdentifier(mini.publicIdentifier, PUBLIC_IDENTIFIER)) continue;
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
    status = 200;
  }
} catch (e) { status = typeof e === "number" ? e : 0; state = "error"; invitation = null; }
({ status, signedIn: csrf !== "", capturedAt, state, publicIdentifier: PUBLIC_IDENTIFIER, invitation, pagesRead })
