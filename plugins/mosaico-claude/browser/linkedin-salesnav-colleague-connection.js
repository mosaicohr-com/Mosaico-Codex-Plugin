const PUBLIC_IDENTIFIER = "";
const COLLEAGUE_IDENTIFIER = "";
// Mosaico Outreach: is one sourcing candidate already a connection of a colleague, according to Sales Navigator's "Connections of" filter.
// Approved capture script (0.9.5). The plugin's browser-script gate allows it only word for word, with the first line's value changed to
// the candidate's public identifier (the part of the profile address after /in/, or the opaque member id Mosaico hands over as the
// script identifier) and the second line's value changed to the colleague's registered LinkedIn public identifier, which Mosaico
// supplies (outreach_get_day, workflowStatus.colleagueChecks): the run never chooses the colleague.
// It runs inside the signed-in Sales Navigator page (any https://www.linkedin.com/sales/ page): the CSRF token is read here, sent only to
// LinkedIn's own endpoints listed below, and never returned. It makes at most these calls to LinkedIn, one after the other with a short
// pause between the Sales Navigator ones, and never retries:
//   1. LinkedIn's profile query (voyager/api/graphql), asked exactly as linkedin-connection-evidence.js asks it (same address, same query id,
//      same headers, same reading of the answer; since 0.9.5, including the normalized-JSON accept header the answer's `included` list needs: 0.9.4
//      sent a plain JSON accept header, LinkedIn answered without `included`, and every person looked unknown) once for the colleague and once for the
//      candidate. It gives each person's member URN (urn:li:fsd_profile:ACoAA...), from which the numeric member id is decoded, and the
//      name. The name never leaves the page except as the search text sent back to LinkedIn.
//   2. sales-api/salesApiFacetTypeahead?type=CONNECTION_OF: the picker behind the "Connections of" filter. It searches by text, not by
//      public identifier, so the colleague's name is the text and the colleague is the entry whose id decodes to HER numeric member id. A
//      similar name is never taken: nothing is ever chosen by name.
//   3. sales-api/salesApiLeadSearch with the one filter CONNECTION_OF (the colleague's Sales Navigator id) and the candidate's name as the
//      keyword, 25 results a page, at most 2 pages. The API has no way to restrict a search to one member, so the keyword narrows it and
//      the candidate is recognised by member id, never by name: a result is the candidate when its Sales Navigator id (ACw...) decodes to
//      the candidate's numeric member id (bytes 00 2C 00 00, then the member id as 4 big-endian bytes, then 21 more bytes).
//   4. When step 3 does not list the candidate: the same keyword search without the filter, one page, only to read the candidate's
//      Sales Navigator id (the result whose id decodes to the candidate's member id). Mosaico requires that id when the search completed.
// Output: state "ok", "colleague-not-resolved" (the colleague has no profile, name or typeahead entry with her member id),
// "candidate-not-resolved" (the candidate has no profile, name or member id, is the colleague, or is not in the unfiltered results) or
// "error" (the page is signed out, LinkedIn answered with an error status, an answer was not in the expected shape, or the filter was not
// applied). colleague and candidate each carry input (the first or second line's value as given), salesNavId (the ACw id, or null) and
// memberId (the numeric member id, or null). filter is { type: "CONNECTION_OF" }. found is true only when state is "ok" and the candidate
// is listed in the colleague's connections: it is never true otherwise. found false is NOT a proof that they are not connected: the
// colleague may hide her connections, the candidate may hide his, and Sales Navigator may not list everyone. resultsTotal is the filtered
// search's metadata.totalDisplayCount as text ("2K+" when large), or null. pagesRead counts every Sales Navigator results page read.
// status is the HTTP status of the last call LinkedIn answered (200 when all went well), or 0 when no call was made, a call got no
// answer, or an answer was not JSON. The script never throws and never returns a name, headline, picture, URL or any other result row.
// Checks that fail closed (state "error", found false): the filtered answer does not echo the colleague's id in its metadata (the
// filter was not applied, so a "found" could be wrong); the answer has results but none whose id can be read; an id and its numeric
// member id disagree.
// What the 2026-10-07 captures did not show (the capture tool cut long bodies and hid the query and decorationId): the exact spelling
// of the keywords field inside the query, the decorationId LinkedIn's page sends (DECORATION below is the value the Sales Navigator
// page is known to send, not read from a capture), and the shape of a result row (entityUrn urn:li:fs_salesProfile:(<ACw id>,...) and
// objectUrn urn:li:member:<n> are read as the profile call shows them). A wrong guess ends in state "error", never in a wrong "found".
// Text normalisation (0.8.5; the application mirrors this rule): every free-text field that leaves the page is normalised with
// normalizeText before it is hashed and returned, in this order: (1) Unicode NFC; (2) every space separator (U+00A0, U+1680,
// U+2000-U+200A, U+202F, U+205F, U+3000) becomes a plain space; (3) zero-width characters (U+200B-U+200D, U+2060, U+FEFF) are
// removed; (4) CRLF and CR become LF; (5) every other C0 or C1 control character (U+0000-U+001F, U+007F-U+009F) except LF and TAB
// is removed; (6) each run of plain spaces becomes one space; (7) spaces and tabs at the end of each line are removed. URNs, URLs,
// identifiers and timestamps are never touched. The integrity digest is computed after normalisation.
// This script returns no free-text field. normalizeText is applied only to the two names used as search text (never returned), so a stray space
// or zero-width character cannot spoil the search; it is kept so every approved script carries the same rule.
// Integrity: the result's last field, integrity, is { algorithm: "fnv1a32", digest }: FNV-1a 32-bit over the UTF-8 bytes of
// the canonical JSON (keys sorted, no spaces, with null-valued keys omitted) of everything else the script returns, as 8 lowercase hex characters.
// Pass the whole result to Mosaico exactly as returned: Mosaico recomputes the digest and refuses an altered copy.
const PROFILE_ENDPOINT = "https://www.linkedin.com/voyager/api/graphql";
const PROFILE_QUERY_ID = "voyagerIdentityDashProfiles.34ead06db82a2cc9a778fac97f69ad6a";
const TYPEAHEAD_ENDPOINT = "https://www.linkedin.com/sales-api/salesApiFacetTypeahead";
const SEARCH_ENDPOINT = "https://www.linkedin.com/sales-api/salesApiLeadSearch";
const DECORATION = "com.linkedin.sales.deco.desktop.searchv2.LeadSearchResult-14";
const PAGE_SIZE = 25;
const MAX_FILTERED_PAGES = 2;
const PAUSE_MS = 500;
const OPAQUE_ID = /^ACoAA[A-Za-z0-9_-]+$/;
const isObj = (v) => typeof v === "object" && v !== null && !Array.isArray(v);
const canonical = (v) => (Array.isArray(v) ? "[" + v.map((x) => (x === undefined ? "null" : canonical(x))).join(",") + "]" : isObj(v) ? "{" + Object.keys(v).filter((k) => v[k] !== undefined && v[k] !== null).sort().map((k) => JSON.stringify(k) + ":" + canonical(v[k])).join(",") + "}" : JSON.stringify(v));
const fnv1a32 = (s) => { let h = 0x811c9dc5; for (const b of new TextEncoder().encode(s)) { h = Math.imul(h ^ b, 0x01000193) >>> 0; } return h.toString(16).padStart(8, "0"); };
const normalizeText = (s) => String(s).normalize("NFC").replace(/[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000]/g, " ").replace(/[\u200B-\u200D\u2060\uFEFF]/g, "").replace(/\r\n?/g, "\n").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F]/g, "").replace(/ {2,}/g, " ").replace(/[ \t]+(?=\n|$)/g, "");
const typeOf = (e) => (isObj(e) && typeof e["$type"] === "string" ? e["$type"] : "");
const listOf = (v) => (Array.isArray(v) ? v : []);
const profileUrnId = (v) => { const m = typeof v === "string" ? /^urn:li:fsd_profile:([A-Za-z0-9_-]+)$/.exec(v) : null; return m === null ? null : m[1]; };
const memberIdOfOpaque = (opaque) => {
  // An opaque LinkedIn id is 29 base64 bytes: 4 prefix bytes (00 2C 00 00 for Sales Navigator's ACw..., 00 2A 00 00 for ACoAA...), the numeric member id as 4 big-endian bytes, then 21 more.
  if (typeof opaque !== "string" || !/^AC[ow][A-Za-z0-9_-]{30,}$/.test(opaque)) return null;
  let bytes;
  try { bytes = Array.from(atob(opaque.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0)); } catch (e) { return null; }
  if (bytes.length !== 29 || bytes[0] !== 0 || (bytes[1] !== 0x2c && bytes[1] !== 0x2a) || bytes[2] !== 0 || bytes[3] !== 0) return null;
  const n = ((bytes[4] * 256 + bytes[5]) * 256 + bytes[6]) * 256 + bytes[7];
  return n > 0 ? n : null;
};
const salesId = (v) => (typeof v === "string" && /^AC[w][A-Za-z0-9_-]{30,}$/.test(v) ? v : null);
const restli = (s) => encodeURIComponent(s).replace(/[!'()*]/g, (c) => "%" + c.charCodeAt(0).toString(16).toUpperCase());
const nameOf = (p) => normalizeText([p.firstName, p.lastName].filter((n) => typeof n === "string").join(" ")).trim();
const resolveProfile = (profiles, requested) => {
  if (OPAQUE_ID.test(requested)) return profiles.find((e) => profileUrnId(e.entityUrn) === requested) || null;
  const exact = profiles.filter((e) => typeof e.publicIdentifier === "string" && e.publicIdentifier.toLowerCase() === requested.toLowerCase());
  if (exact.length > 0) return exact[exact.length - 1];
  return profiles.length === 1 && typeof profiles[0].publicIdentifier === "string" ? profiles[0] : null;
};
const csrf = (document.cookie.match(/JSESSIONID="?([^;"]+)/) || [])[1] || "";
const capturedAt = new Date().toISOString();
const HEADERS = { "csrf-token": csrf, "x-restli-protocol-version": "2.0.0", "accept": "application/json" };
const PROFILE_HEADERS = { "csrf-token": csrf, "x-restli-protocol-version": "2.0.0", "accept": "application/vnd.linkedin.normalized+json+2.1" };
const colleague = { input: COLLEAGUE_IDENTIFIER, salesNavId: null, memberId: OPAQUE_ID.test(COLLEAGUE_IDENTIFIER) ? memberIdOfOpaque(COLLEAGUE_IDENTIFIER) : null };
const candidate = { input: PUBLIC_IDENTIFIER, salesNavId: null, memberId: OPAQUE_ID.test(PUBLIC_IDENTIFIER) ? memberIdOfOpaque(PUBLIC_IDENTIFIER) : null };
let status = 0;
let state = "error";
let found = false;
let resultsTotal = null;
let pagesRead = 0;
let calls = 0;
const get = async (url, headers) => {
  if (calls > 0 && url.indexOf("/sales-api/") > 0) await new Promise((resolve) => setTimeout(resolve, PAUSE_MS));
  calls++;
  let r;
  try { r = await fetch(url, { credentials: "include", headers }); } catch (e) { status = 0; throw "no-answer"; }
  status = r.status;
  if (!r.ok) throw "http";
  try { return await r.json(); } catch (e) { status = 0; throw "not-json"; }
};
const lookup = async (identifier) => {
  // The profile query, request and reading exactly as linkedin-connection-evidence.js does them. null when LinkedIn knows no such profile; a thrown status on an error.
  const j = await get(PROFILE_ENDPOINT + "?includeWebMetadata=true&variables=(vanityName:" + encodeURIComponent(identifier) + ")&queryId=" + PROFILE_QUERY_ID, PROFILE_HEADERS);
  const hit = resolveProfile(listOf(j && j.included).filter((e) => isObj(e) && /profile\.Profile$/.test(typeOf(e))), identifier);
  const id = hit === null ? null : profileUrnId(hit.entityUrn);
  return id === null ? null : { memberId: memberIdOfOpaque(id), name: nameOf(hit) };
};
const rowOf = (e) => {
  // One search result: its Sales Navigator id and the numeric member id it carries. null when it cannot be read or its parts disagree.
  if (!isObj(e)) return null;
  const m = typeof e.entityUrn === "string" ? /^urn:li:fs_salesProfile:\((ACw[A-Za-z0-9_-]+),/.exec(e.entityUrn) : null;
  const id = m === null ? null : salesId(m[1]);
  const member = id === null ? null : memberIdOfOpaque(id);
  if (member === null) return null;
  const o = typeof e.objectUrn === "string" ? /^urn:li:member:([0-9]+)$/.exec(e.objectUrn) : null;
  return o !== null && Number(o[1]) !== member ? null : { id, member };
};
const search = async (name, filterId, filterText, start) => {
  const filter = filterId === null ? "" : "filters:List((type:CONNECTION_OF,values:List((id:" + filterId + ",text:" + restli(filterText) + ",selectionType:INCLUDED)))),";
  const j = await get(SEARCH_ENDPOINT + "?q=searchQuery&query=(" + filter + "keywords:" + restli(name) + ")&start=" + start + "&count=" + PAGE_SIZE + "&decorationId=" + DECORATION, HEADERS);
  pagesRead++;
  if (!isObj(j)) throw "shape";
  const elements = listOf(j.elements);
  const rows = elements.map(rowOf);
  // Results of which none has a readable id mean the answer is not in the shape this script understands: stop, never guess.
  if (elements.length > 0 && rows.every((r) => r === null)) throw "shape";
  const meta = isObj(j.metadata) ? j.metadata : {};
  if (filterId !== null && JSON.stringify(meta).indexOf(filterId) < 0) throw "filter-not-applied";
  return { rows: rows.filter((r) => r !== null), count: elements.length, total: typeof meta.totalDisplayCount === "string" ? meta.totalDisplayCount : null };
};
try {
  if (csrf !== "" && PUBLIC_IDENTIFIER !== "" && COLLEAGUE_IDENTIFIER !== "") {
    state = "colleague-not-resolved";
    const c = await lookup(COLLEAGUE_IDENTIFIER);
    if (c !== null) colleague.memberId = c.memberId;
    let entry = null;
    if (c !== null && c.memberId !== null && c.name !== "") {
      const t = await get(TYPEAHEAD_ENDPOINT + "?q=query&start=0&count=10&type=CONNECTION_OF&query=" + restli(c.name), HEADERS);
      // Only an entry whose id decodes to her own member id is her; a similar name is not.
      entry = listOf(isObj(t) ? t.elements : null).find((x) => isObj(x) && salesId(x.id) !== null && memberIdOfOpaque(x.id) === c.memberId) || null;
    }
    if (entry !== null) {
      colleague.salesNavId = entry.id;
      state = "candidate-not-resolved";
      const p = await lookup(PUBLIC_IDENTIFIER);
      if (p !== null) candidate.memberId = p.memberId;
      if (p !== null && p.memberId !== null && p.name !== "" && p.memberId !== colleague.memberId) {
        const filterText = typeof entry.displayValue === "string" ? entry.displayValue : "";
        let hit = null;
        let page = null;
        for (let n = 0; n < MAX_FILTERED_PAGES && hit === null; n++) {
          page = await search(p.name, colleague.salesNavId, filterText, n * PAGE_SIZE);
          hit = page.rows.find((r) => r.member === p.memberId) || null;
          if (page.count < PAGE_SIZE) break;
        }
        resultsTotal = page === null ? null : page.total;
        if (hit === null) {
          // Not listed: read the candidate's own Sales Navigator id from the unfiltered keyword results (one page).
          const plain = await search(p.name, null, "", 0);
          hit = plain.rows.find((r) => r.member === p.memberId) || null;
          found = false;
        } else {
          found = true;
        }
        if (hit !== null) { candidate.salesNavId = hit.id; state = "ok"; } else { found = false; }
      }
    }
    status = state === "error" ? status : 200;
  }
} catch (e) { state = "error"; found = false; resultsTotal = null; }
const payload = { status, signedIn: csrf !== "", capturedAt, state, colleague, candidate, filter: { type: "CONNECTION_OF" }, found: state === "ok" && found, resultsTotal, pagesRead };
({ ...payload, integrity: { algorithm: "fnv1a32", digest: fnv1a32(canonical(payload)) } })
