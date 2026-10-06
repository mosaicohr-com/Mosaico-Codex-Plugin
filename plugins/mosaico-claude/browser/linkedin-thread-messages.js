const PUBLIC_IDENTIFIER = "";
// Mosaico Outreach: the conversation thread with one Lead, read from LinkedIn's own messaging data.
// Approved capture script. The plugin's browser-script gate allows it only word for word, with the
// first line's value changed to the Lead's public identifier (the part of the profile address after /in/).
// Identifier forms (0.8.6): the first line's value is either a vanity (jane-doe) or an opaque member id (ACoAA...; matched by
// ^ACoAA[A-Za-z0-9_-]+$, the id part of urn:li:fsd_profile:<id>). An opaque id builds the member URN directly
// (urn:li:fsd_profile:<id>) and skips the vanity lookup, so no name is known and the search path is not used (the list path
// runs; a miss then reads page-limit unless the list is exhausted). A vanity is looked up with the profile query: when the
// response holds a Profile whose publicIdentifier equals the vanity (any case) that one is used; otherwise, when the response
// holds exactly one Profile entity, it is taken as the redirect target (LinkedIn answers an old vanity with the person's new
// one); any other answer is an error with errorStep "profile". Every output carries requestedIdentifier (the value as given),
// resolvedIdentifier (the response's publicIdentifier, or the opaque id) and memberUrn (the Lead's member URN, null when it
// was not resolved). The Lead's conversation is matched by that member URN.
// It runs inside the signed-in LinkedIn page: the CSRF token is read here, sent only to LinkedIn's own
// who-am-I, profile and messaging calls, and never returned. It finds the one-to-one conversation between
// the signed-in account and the Lead, first by searching LinkedIn's messaging search by the Lead's name and then, when the
// search finds nothing, by paging LinkedIn's conversation list, and returns that conversation's
// participants (member URNs) and its messages oldest first, each with only its delivery time, its sender's
// member URN and its text. Names, pictures, reactions, attachments and every other field are dropped before
// anything leaves the page. Any error returns the status, state "error" and empty lists: the script never throws.
// Error reporting (0.8.6): state "error" carries status (the HTTP status LinkedIn answered, or 0 when the call itself failed or
// nobody is signed in) and errorStep, the step that failed: "me" (who-am-I, or no signed-in session), "profile" (the Lead's
// profile lookup or identifier), "conversations" (the conversation list) or "messages" (the thread's messages). errorStep is
// null when state is not "error". A failed search does not end the run: the list path is tried.
// Search path (validated: search call observed 6 Oct 2026, the call LinkedIn's own messaging search box sends): the query
// messengerConversations.737b27144cf922499202658a5345016f with the variables
// (categories:List(INBOX,SPAM,ARCHIVE),count:20,firstDegreeConnections:false,mailboxUrn:<owner URN>,keywords:<text>); each next
// page adds nextCursor:<opaque cursor from the previous response> before keywords. The cursor is read defensively: the first
// string field named nextCursor (or a paging cursor) in the response's data node; no cursor ends the search. The script reads
// at most MAX_SEARCH_PAGES (3) search pages. The keywords are the Lead's first and last name from the Lead's Profile entity.
// The names are used ONLY inside the page as the search keywords: they are never returned, never hashed and never leave the
// page. The same participant match as the list path is applied to the search results (two participants: the owner and the
// Lead). The search covers INBOX, SPAM and ARCHIVE, so it finds conversations the PRIMARY_INBOX list does not hold.
// List path (the fallback, run only when the search found nothing; validated: paging call observed 6 Oct 2026): page 1 is the owner's mailbox query as is (messengerConversations
// with only mailboxUrn, about 20 conversations), which ignores any cursor. Pages 2 to MAX_CONVERSATION_PAGES use
// LinkedIn's DIFFERENT paged query id, with the exact variables form LinkedIn's own inbox sends when it scrolls:
// (query:(predicateUnions:List((conversationCategoryPredicate:(category:PRIMARY_INBOX)))),count:20,mailboxUrn:<owner URN>,
// lastUpdatedBefore:<ms>). The cursor <ms> is the smallest lastActivityAt (epoch milliseconds) seen so far, used as is:
// LinkedIn treats it as strictly before. The script reads at most MAX_CONVERSATION_PAGES pages (about 160
// conversations). After each page it keeps only the NEW elements, those whose lastActivityAt is strictly older than the
// cursor (every element of page 1), and searches the Lead among the new elements only. Only the PRIMARY_INBOX category is
// searched: message requests and the Other tab are NOT searched.
// Coverage semantics corrected 6 Oct 2026: a list that does not move on is the END of the list, not a limit. LinkedIn
// answers a cursor older than every conversation with the tail again or with an empty tail. So the list is exhausted, and
// coverage is "complete", when a page returns no elements, or no new elements, or fewer than 20 elements in total.
// coverage says what a "no-conversation" proves: "complete" when the conversation was found by either path, or when the
// search returned at least one page without error and the list was exhausted without the conversation; "page-limit"
// otherwise: when the search failed, was not possible (no name) or stopped at its page cap AND the list stopped at
// MAX_CONVERSATION_PAGES with new elements still arriving or could not move its cursor, and on any error.
// lookup says how the conversation was found: "search", "list" or "none". pagesRead is the number of conversation-list pages
// read; searchPagesRead is the number of search pages read.
// state "no-conversation" means "not found in the pages read": only coverage "complete" makes it mean that the
// PRIMARY_INBOX holds none. The list is read from whichever single value of the response's data holds an elements array.
// Text normalisation (0.8.5; the application mirrors this rule): every free-text field that leaves the page is normalised with
// normalizeText before it is hashed and returned, in this order: (1) Unicode NFC; (2) every space separator (U+00A0, U+1680,
// U+2000-U+200A, U+202F, U+205F, U+3000) becomes a plain space; (3) zero-width characters (U+200B-U+200D, U+2060, U+FEFF) are
// removed; (4) CRLF and CR become LF; (5) every other C0 or C1 control character (U+0000-U+001F, U+007F-U+009F) except LF and TAB
// is removed; (6) each run of plain spaces becomes one space; (7) spaces and tabs at the end of each line are removed. URNs, URLs,
// identifiers and timestamps are never touched. The integrity digest is computed after normalisation.
// Integrity: the result's last field, integrity, is { algorithm: "fnv1a32", digest }: FNV-1a 32-bit over the UTF-8 bytes of
// the canonical JSON (keys sorted, no spaces) of everything else the script returns, as 8 lowercase hex characters.
// Pass the whole result to Mosaico exactly as returned: Mosaico recomputes the digest and refuses an altered copy.
const API = "https://www.linkedin.com/voyager/api";
const PROFILE_QUERY_ID = "voyagerIdentityDashProfiles.34ead06db82a2cc9a778fac97f69ad6a";
const CONVERSATIONS_QUERY_ID = "messengerConversations.0d5e6781bbee71c3e51c8843c6519f48";
const CONVERSATIONS_PAGED_QUERY_ID = "messengerConversations.9501074288a12f3ae9e3c7ea243bccbf";
const CONVERSATIONS_SEARCH_QUERY_ID = "messengerConversations.737b27144cf922499202658a5345016f";
const MESSAGES_QUERY_ID = "messengerMessages.5846eeb71c981f11e0134cb6626cc314";
const MAX_MESSAGES = 98;
const MAX_CONVERSATION_PAGES = 8;
const MAX_SEARCH_PAGES = 3;
const isObj = (v) => typeof v === "object" && v !== null && !Array.isArray(v);
const canonical = (v) => (Array.isArray(v) ? "[" + v.map((x) => (x === undefined ? "null" : canonical(x))).join(",") + "]" : isObj(v) ? "{" + Object.keys(v).filter((k) => v[k] !== undefined).sort().map((k) => JSON.stringify(k) + ":" + canonical(v[k])).join(",") + "}" : JSON.stringify(v));
const fnv1a32 = (s) => { let h = 0x811c9dc5; for (const b of new TextEncoder().encode(s)) { h = Math.imul(h ^ b, 0x01000193) >>> 0; } return h.toString(16).padStart(8, "0"); };
const normalizeText = (s) => String(s).normalize("NFC").replace(/[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000]/g, " ").replace(/[\u200B-\u200D\u2060\uFEFF]/g, "").replace(/\r\n?/g, "\n").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F]/g, "").replace(/ {2,}/g, " ").replace(/[ \t]+(?=\n|$)/g, "");
const typeOf = (e) => (isObj(e) && typeof e["$type"] === "string" ? e["$type"] : "");
const csrf = (document.cookie.match(/JSESSIONID="?([^;"]+)/) || [])[1] || "";
const capturedAt = new Date().toISOString();
const NORMALIZED = { "csrf-token": csrf, "x-restli-protocol-version": "2.0.0", "accept": "application/vnd.linkedin.normalized+json+2.1" };
const GRAPHQL = { "csrf-token": csrf, "x-restli-protocol-version": "2.0.0", "accept": "application/graphql" };
let status = 0;
const getJson = async (url, headers) => { const r = await fetch(url, { credentials: "include", headers }); status = r.status; if (!r.ok) throw r.status; return r.json(); };
const OPAQUE_ID = /^ACoAA[A-Za-z0-9_-]+$/;
const memberUrn = (v) => (typeof v === "string" && /^urn:li:fsd_profile:[A-Za-z0-9_-]+$/.test(v) ? v : null);
const participantUrn = (p) => memberUrn(typeof p === "string" ? p : isObj(p) ? p.hostIdentityUrn : null);
const isoOf = (ms) => (typeof ms === "number" && ms > 0 && ms < 8.64e15 ? new Date(ms).toISOString() : null);
const listOf = (v) => (Array.isArray(v) ? v : []);
const encoded = (v) => encodeURIComponent(v).replace(/\(/g, "%28").replace(/\)/g, "%29");
const cursorIn = (v, depth = 0) => {
  if (!isObj(v) || depth > 3) return null;
  if (typeof v.nextCursor === "string" && v.nextCursor !== "") return v.nextCursor;
  if (isObj(v.paging) && typeof v.paging.cursor === "string" && v.paging.cursor !== "") return v.paging.cursor;
  for (const c of Object.values(v)) { const found = cursorIn(c, depth + 1); if (found !== null) return found; }
  return null;
};
const elementsIn = (data) => { for (const v of isObj(data) ? Object.values(data) : []) { if (isObj(v) && Array.isArray(v.elements)) return v.elements; } return []; };
let state = "error";
let errorStep = csrf === "" ? "me" : "profile";
let resolvedIdentifier = null;
let leadMemberUrn = null;
let conversationUrn = null;
let participants = [];
let messages = [];
let coverage = "page-limit";
let pagesRead = 0;
let lookup = "none";
let searchPagesRead = 0;
try {
  if (csrf !== "" && PUBLIC_IDENTIFIER !== "") {
    errorStep = "me";
    const me = await getJson(API + "/me", NORMALIZED);
    let ownerUrn = null;
    for (const e of listOf(me && me.included)) { if (isObj(e) && /MiniProfile$/.test(typeOf(e))) ownerUrn = memberUrn(e.dashEntityUrn); }
    if (ownerUrn === null) throw null;
    errorStep = "profile";
    let leadUrn = null;
    let keywords = "";
    if (OPAQUE_ID.test(PUBLIC_IDENTIFIER)) {
      leadUrn = "urn:li:fsd_profile:" + PUBLIC_IDENTIFIER;
      resolvedIdentifier = PUBLIC_IDENTIFIER;
    } else {
      const profile = await getJson(API + "/graphql?includeWebMetadata=true&variables=(vanityName:" + encodeURIComponent(PUBLIC_IDENTIFIER) + ")&queryId=" + PROFILE_QUERY_ID, NORMALIZED);
      const profiles = listOf(profile && profile.included).filter((e) => isObj(e) && /profile\.Profile$/.test(typeOf(e)));
      const exact = profiles.filter((e) => typeof e.publicIdentifier === "string" && e.publicIdentifier.toLowerCase() === PUBLIC_IDENTIFIER.toLowerCase());
      const hit = exact.length > 0 ? exact[exact.length - 1] : profiles.length === 1 && typeof profiles[0].publicIdentifier === "string" ? profiles[0] : null;
      if (hit !== null) {
        leadUrn = memberUrn(hit.entityUrn);
        if (leadUrn !== null) {
          resolvedIdentifier = hit.publicIdentifier;
          keywords = normalizeText([hit.firstName, hit.lastName].filter((n) => typeof n === "string").join(" ")).trim();
        }
      }
    }
    leadMemberUrn = leadUrn;
    if (leadUrn === null || ownerUrn === leadUrn) throw null;
    errorStep = "conversations";
    const mailbox = encodeURIComponent(ownerUrn);
    const match = (page) => {
      let hit = null;
      for (const c of page) {
        if (!isObj(c) || typeof c.entityUrn !== "string") continue;
        const urns = listOf(c.conversationParticipants !== undefined ? c.conversationParticipants : c.participants).map(participantUrn);
        const unique = urns.filter((u, i) => u !== null && urns.indexOf(u) === i);
        if (unique.length !== 2 || urns.length !== 2 || !unique.includes(ownerUrn) || !unique.includes(leadUrn)) continue;
        const activity = typeof c.lastActivityAt === "number" ? c.lastActivityAt : 0;
        if (hit === null || activity > hit.activity) hit = { urn: c.entityUrn, urns: unique, activity };
      }
      return hit;
    };
    let best = null;
    let searchOk = false;
    if (keywords !== "") {
      let searchCursor = null;
      try {
        while (best === null && searchPagesRead < MAX_SEARCH_PAGES) {
          const variables = "(categories:List(INBOX,SPAM,ARCHIVE),count:20,firstDegreeConnections:false,mailboxUrn:" + mailbox + (searchCursor === null ? "" : ",nextCursor:" + encoded(searchCursor)) + ",keywords:" + encoded(keywords) + ")";
          const found = await getJson(API + "/voyagerMessagingGraphQL/graphql?queryId=" + CONVERSATIONS_SEARCH_QUERY_ID + "&variables=" + variables, GRAPHQL);
          searchPagesRead++;
          searchOk = true;
          const page = elementsIn(found && found.data);
          best = match(page);
          const next = cursorIn(found && found.data);
          if (best !== null) lookup = "search";
          else if (page.length === 0 || next === null || next === searchCursor) break;
          else searchCursor = next;
        }
      } catch (e) { searchOk = false; }
    }
    let cursor = null;
    let exhausted = false;
    let stalled = false;
    while (best === null && !exhausted && !stalled && pagesRead < MAX_CONVERSATION_PAGES) {
      const request = cursor === null
        ? "queryId=" + CONVERSATIONS_QUERY_ID + "&variables=(mailboxUrn:" + mailbox + ")"
        : "queryId=" + CONVERSATIONS_PAGED_QUERY_ID + "&variables=(query:(predicateUnions:List((conversationCategoryPredicate:(category:PRIMARY_INBOX)))),count:20,mailboxUrn:" + mailbox + ",lastUpdatedBefore:" + cursor + ")";
      const conversations = await getJson(API + "/voyagerMessagingGraphQL/graphql?" + request, GRAPHQL);
      pagesRead++;
      const page = elementsIn(conversations && conversations.data);
      const fresh = cursor === null ? page : page.filter((c) => isObj(c) && typeof c.lastActivityAt === "number" && c.lastActivityAt < cursor);
      if (fresh.length === 0 || page.length < 20) exhausted = true;
      let oldest = null;
      for (const c of fresh) {
        const activity = isObj(c) && typeof c.lastActivityAt === "number" ? c.lastActivityAt : 0;
        if (Number.isSafeInteger(activity) && activity > 0 && (oldest === null || activity < oldest)) oldest = activity;
      }
      best = match(fresh);
      if (best !== null) lookup = "list";
      if (best === null && !exhausted) {
        if (oldest === null) stalled = true;
        else cursor = oldest;
      }
    }
    coverage = best !== null || (searchOk && exhausted) ? "complete" : "page-limit";
    if (best === null) {
      state = "no-conversation";
    } else {
      errorStep = "messages";
      const encodedUrn = encodeURIComponent(best.urn).replace(/\(/g, "%28").replace(/\)/g, "%29");
      const thread = await getJson(API + "/voyagerMessagingGraphQL/graphql?queryId=" + MESSAGES_QUERY_ID + "&variables=(conversationUrn:" + encodedUrn + ")", GRAPHQL);
      const messageNode = isObj(thread && thread.data) ? thread.data.messengerMessagesBySyncToken : null;
      const read = [];
      for (const m of listOf(isObj(messageNode) ? messageNode.elements : null)) {
        if (!isObj(m)) continue;
        const text = isObj(m.body) && typeof m.body.text === "string" ? normalizeText(m.body.text) : "";
        if (text.trim() === "") continue;
        read.push({ at: typeof m.deliveredAt === "number" ? m.deliveredAt : 0, messageUrn: typeof m.entityUrn === "string" ? m.entityUrn : null, deliveredAt: isoOf(m.deliveredAt), senderUrn: isObj(m.sender) ? memberUrn(m.sender.hostIdentityUrn) : null, text });
      }
      read.sort((a, b) => a.at - b.at);
      conversationUrn = best.urn;
      participants = best.urns;
      messages = read.slice(-MAX_MESSAGES).map((m) => ({ messageUrn: m.messageUrn, deliveredAt: m.deliveredAt, senderUrn: m.senderUrn, text: m.text }));
      state = "ok";
    }
    errorStep = null;
    status = 200;
  }
} catch (e) { status = typeof e === "number" ? e : e === null ? status : 0; state = "error"; conversationUrn = null; participants = []; messages = []; coverage = "page-limit"; lookup = "none"; }
const payload = { status, signedIn: csrf !== "", capturedAt, state, errorStep: state === "error" ? errorStep : null, source: "linkedin-voyager-messages", publicIdentifier: PUBLIC_IDENTIFIER, requestedIdentifier: PUBLIC_IDENTIFIER, resolvedIdentifier, memberUrn: leadMemberUrn, conversationUrn, participants, messages, coverage, lookup, pagesRead, searchPagesRead };
({ ...payload, integrity: { algorithm: "fnv1a32", digest: fnv1a32(canonical(payload)) } })
