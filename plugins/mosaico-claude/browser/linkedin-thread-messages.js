const PUBLIC_IDENTIFIER = "";
// Mosaico Outreach: the conversation thread with one Lead, read from LinkedIn's own messaging data.
// Approved capture script. The plugin's browser-script gate allows it only word for word, with the
// first line's value changed to the Lead's public identifier (the part of the profile address after /in/).
// It runs inside the signed-in LinkedIn page: the CSRF token is read here, sent only to LinkedIn's own
// who-am-I, profile and messaging calls, and never returned. It finds the one-to-one conversation between
// the signed-in account and the Lead by paging LinkedIn's conversation list, and returns that conversation's
// participants (member URNs) and its messages oldest first, each with only its delivery time, its sender's
// member URN and its text. Names, pictures, reactions, attachments and every other field are dropped before
// anything leaves the page. Any error returns the status, state "error" and empty lists: the script never throws.
// Paging (validated: paging call observed 6 Oct 2026): page 1 is the owner's mailbox query as is (messengerConversations
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
// coverage says what a "no-conversation" proves: "complete" when the conversation was found or the list was exhausted
// without it; "page-limit" only when reading stopped at MAX_CONVERSATION_PAGES with new elements still arriving, when a
// full page held no readable lastActivityAt so the cursor could not move, or on an error. pagesRead is the number of
// conversation-list pages read.
// state "no-conversation" means "not found in the pages read": only coverage "complete" makes it mean that the
// PRIMARY_INBOX holds none. The list is read from whichever single value of the response's data holds an elements array.
// Integrity: the result's last field, integrity, is { algorithm: "fnv1a32", digest }: FNV-1a 32-bit over the UTF-8 bytes of
// the canonical JSON (keys sorted, no spaces) of everything else the script returns, as 8 lowercase hex characters.
// Pass the whole result to Mosaico exactly as returned: Mosaico recomputes the digest and refuses an altered copy.
const API = "https://www.linkedin.com/voyager/api";
const PROFILE_QUERY_ID = "voyagerIdentityDashProfiles.34ead06db82a2cc9a778fac97f69ad6a";
const CONVERSATIONS_QUERY_ID = "messengerConversations.0d5e6781bbee71c3e51c8843c6519f48";
const CONVERSATIONS_PAGED_QUERY_ID = "messengerConversations.9501074288a12f3ae9e3c7ea243bccbf";
const MESSAGES_QUERY_ID = "messengerMessages.5846eeb71c981f11e0134cb6626cc314";
const MAX_MESSAGES = 98;
const MAX_CONVERSATION_PAGES = 8;
const isObj = (v) => typeof v === "object" && v !== null && !Array.isArray(v);
const canonical = (v) => (Array.isArray(v) ? "[" + v.map((x) => (x === undefined ? "null" : canonical(x))).join(",") + "]" : isObj(v) ? "{" + Object.keys(v).filter((k) => v[k] !== undefined).sort().map((k) => JSON.stringify(k) + ":" + canonical(v[k])).join(",") + "}" : JSON.stringify(v));
const fnv1a32 = (s) => { let h = 0x811c9dc5; for (const b of new TextEncoder().encode(s)) { h = Math.imul(h ^ b, 0x01000193) >>> 0; } return h.toString(16).padStart(8, "0"); };
const typeOf = (e) => (isObj(e) && typeof e["$type"] === "string" ? e["$type"] : "");
const csrf = (document.cookie.match(/JSESSIONID="?([^;"]+)/) || [])[1] || "";
const capturedAt = new Date().toISOString();
const NORMALIZED = { "csrf-token": csrf, "x-restli-protocol-version": "2.0.0", "accept": "application/vnd.linkedin.normalized+json+2.1" };
const GRAPHQL = { "csrf-token": csrf, "x-restli-protocol-version": "2.0.0", "accept": "application/graphql" };
const getJson = async (url, headers) => { const r = await fetch(url, { credentials: "include", headers }); if (!r.ok) throw r.status; return r.json(); };
const memberUrn = (v) => (typeof v === "string" && /^urn:li:fsd_profile:[A-Za-z0-9_-]+$/.test(v) ? v : null);
const participantUrn = (p) => memberUrn(typeof p === "string" ? p : isObj(p) ? p.hostIdentityUrn : null);
const isoOf = (ms) => (typeof ms === "number" && ms > 0 && ms < 8.64e15 ? new Date(ms).toISOString() : null);
const listOf = (v) => (Array.isArray(v) ? v : []);
const elementsIn = (data) => { for (const v of isObj(data) ? Object.values(data) : []) { if (isObj(v) && Array.isArray(v.elements)) return v.elements; } return []; };
let status = 0;
let state = "error";
let conversationUrn = null;
let participants = [];
let messages = [];
let coverage = "page-limit";
let pagesRead = 0;
try {
  if (csrf !== "" && PUBLIC_IDENTIFIER !== "") {
    const me = await getJson(API + "/me", NORMALIZED);
    let ownerUrn = null;
    for (const e of listOf(me && me.included)) { if (isObj(e) && /MiniProfile$/.test(typeOf(e))) ownerUrn = memberUrn(e.dashEntityUrn); }
    const profile = await getJson(API + "/graphql?includeWebMetadata=true&variables=(vanityName:" + encodeURIComponent(PUBLIC_IDENTIFIER) + ")&queryId=" + PROFILE_QUERY_ID, NORMALIZED);
    let leadUrn = null;
    for (const e of listOf(profile && profile.included)) {
      if (isObj(e) && /profile\.Profile$/.test(typeOf(e)) && typeof e.publicIdentifier === "string" && e.publicIdentifier.toLowerCase() === PUBLIC_IDENTIFIER.toLowerCase()) leadUrn = memberUrn(e.entityUrn);
    }
    if (ownerUrn === null || leadUrn === null || ownerUrn === leadUrn) throw 0;
    let best = null;
    let cursor = null;
    let exhausted = false;
    let stalled = false;
    while (best === null && !exhausted && !stalled && pagesRead < MAX_CONVERSATION_PAGES) {
      const mailbox = encodeURIComponent(ownerUrn);
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
        if (!isObj(c)) continue;
        const activity = typeof c.lastActivityAt === "number" ? c.lastActivityAt : 0;
        if (Number.isSafeInteger(activity) && activity > 0 && (oldest === null || activity < oldest)) oldest = activity;
        if (typeof c.entityUrn !== "string") continue;
        const urns = listOf(c.conversationParticipants !== undefined ? c.conversationParticipants : c.participants).map(participantUrn);
        const unique = urns.filter((u, i) => u !== null && urns.indexOf(u) === i);
        if (unique.length !== 2 || urns.length !== 2 || !unique.includes(ownerUrn) || !unique.includes(leadUrn)) continue;
        if (best === null || activity > best.activity) best = { urn: c.entityUrn, urns: unique, activity };
      }
      if (best === null && !exhausted) {
        if (oldest === null) stalled = true;
        else cursor = oldest;
      }
    }
    coverage = best !== null || exhausted ? "complete" : "page-limit";
    if (best === null) {
      state = "no-conversation";
    } else {
      const encodedUrn = encodeURIComponent(best.urn).replace(/\(/g, "%28").replace(/\)/g, "%29");
      const thread = await getJson(API + "/voyagerMessagingGraphQL/graphql?queryId=" + MESSAGES_QUERY_ID + "&variables=(conversationUrn:" + encodedUrn + ")", GRAPHQL);
      const messageNode = isObj(thread && thread.data) ? thread.data.messengerMessagesBySyncToken : null;
      const read = [];
      for (const m of listOf(isObj(messageNode) ? messageNode.elements : null)) {
        if (!isObj(m)) continue;
        const text = isObj(m.body) && typeof m.body.text === "string" ? m.body.text : "";
        if (text.trim() === "") continue;
        read.push({ at: typeof m.deliveredAt === "number" ? m.deliveredAt : 0, messageUrn: typeof m.entityUrn === "string" ? m.entityUrn : null, deliveredAt: isoOf(m.deliveredAt), senderUrn: isObj(m.sender) ? memberUrn(m.sender.hostIdentityUrn) : null, text });
      }
      read.sort((a, b) => a.at - b.at);
      conversationUrn = best.urn;
      participants = best.urns;
      messages = read.slice(-MAX_MESSAGES).map((m) => ({ messageUrn: m.messageUrn, deliveredAt: m.deliveredAt, senderUrn: m.senderUrn, text: m.text }));
      state = "ok";
    }
    status = 200;
  }
} catch (e) { status = typeof e === "number" ? e : 0; state = "error"; conversationUrn = null; participants = []; messages = []; coverage = "page-limit"; }
const payload = { status, signedIn: csrf !== "", capturedAt, state, source: "linkedin-voyager-messages", publicIdentifier: PUBLIC_IDENTIFIER, conversationUrn, participants, messages, coverage, pagesRead };
({ ...payload, integrity: { algorithm: "fnv1a32", digest: fnv1a32(canonical(payload)) } })
