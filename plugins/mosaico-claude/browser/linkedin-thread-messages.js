const PUBLIC_IDENTIFIER = "";
// Mosaico Outreach: the conversation thread with one Lead, read from LinkedIn's own messaging data.
// Approved capture script. The plugin's browser-script gate allows it only word for word, with the
// first line's value changed to the Lead's public identifier (the part of the profile address after /in/).
// It runs inside the signed-in LinkedIn page: the CSRF token is read here, sent only to LinkedIn's own
// who-am-I, profile and messaging calls, and never returned. It finds the one-to-one conversation between
// the signed-in account and the Lead among LinkedIn's recent conversations, and returns that conversation's
// participants (member URNs) and its messages oldest first, each with only its delivery time, its sender's
// member URN and its text. Names, pictures, reactions, attachments and every other field are dropped before
// anything leaves the page. When none of the recent conversations is with the Lead, state is
// "no-conversation" and the lists are empty. Any error returns the status, state "error" and empty lists:
// the script never throws.
const API = "https://www.linkedin.com/voyager/api";
const PROFILE_QUERY_ID = "voyagerIdentityDashProfiles.34ead06db82a2cc9a778fac97f69ad6a";
const CONVERSATIONS_QUERY_ID = "messengerConversations.0d5e6781bbee71c3e51c8843c6519f48";
const MESSAGES_QUERY_ID = "messengerMessages.5846eeb71c981f11e0134cb6626cc314";
const MAX_MESSAGES = 98;
const isObj = (v) => typeof v === "object" && v !== null && !Array.isArray(v);
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
let status = 0;
let state = "error";
let conversationUrn = null;
let participants = [];
let messages = [];
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
    const conversations = await getJson(API + "/voyagerMessagingGraphQL/graphql?queryId=" + CONVERSATIONS_QUERY_ID + "&variables=(mailboxUrn:" + encodeURIComponent(ownerUrn) + ")", GRAPHQL);
    const listNode = isObj(conversations && conversations.data) ? conversations.data.messengerConversationsBySyncToken : null;
    let best = null;
    for (const c of listOf(isObj(listNode) ? listNode.elements : null)) {
      if (!isObj(c) || typeof c.entityUrn !== "string") continue;
      const urns = listOf(c.conversationParticipants !== undefined ? c.conversationParticipants : c.participants).map(participantUrn);
      const unique = urns.filter((u, i) => u !== null && urns.indexOf(u) === i);
      if (unique.length !== 2 || urns.length !== 2 || !unique.includes(ownerUrn) || !unique.includes(leadUrn)) continue;
      const activity = typeof c.lastActivityAt === "number" ? c.lastActivityAt : 0;
      if (best === null || activity > best.activity) best = { urn: c.entityUrn, urns: unique, activity };
    }
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
} catch (e) { status = typeof e === "number" ? e : 0; state = "error"; conversationUrn = null; participants = []; messages = []; }
({ status, signedIn: csrf !== "", capturedAt, state, source: "linkedin-voyager-messages", publicIdentifier: PUBLIC_IDENTIFIER, conversationUrn, participants, messages })
