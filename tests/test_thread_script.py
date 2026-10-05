#!/usr/bin/env python3
"""The approved thread script reduces LinkedIn's messaging answers to the evidence record and nothing else.

It is run under node against a fake page and a fake LinkedIn: no network, no real cookie. The check is skipped
(and says so) when node is not installed.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins" / "mosaico-claude" / "browser" / "linkedin-thread-messages.js"

HARNESS = r"""
const fs = require('fs');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const SRC = fs.readFileSync(process.argv[1], 'utf8');
const OWNER = 'urn:li:fsd_profile:OWNERID1', LEAD = 'urn:li:fsd_profile:LEADID01', OTHER = 'urn:li:fsd_profile:OTHERID1';
const CONV = 'urn:li:msg_conversation:(urn:li:fsd_profile:OWNERID1,2-ABC==)';
const TOKEN = 'ajax:SECRET-TOKEN';
async function run(id, routes, cookie = 'JSESSIONID="' + TOKEN + '"') {
  const calls = [];
  const body = SRC.replace('const PUBLIC_IDENTIFIER = "";', 'const PUBLIC_IDENTIFIER = ' + JSON.stringify(id) + ';');
  const wrapped = new AsyncFunction('document', 'fetch', '(async () => {})();' + 'return await (async () => {' + body.replace(/\n\(\{/, '\nreturn ({') + '})();');
  const result = await wrapped({ cookie }, async (url, init) => { calls.push({ url, init }); return routes(url, init); });
  return { result, calls };
}
const ok = (j) => ({ ok: true, status: 200, json: async () => j });
const bad = (s) => ({ ok: false, status: s, json: async () => ({}) });
const me = ok({ included: [{ $type: 'com.linkedin.voyager.identity.shared.MiniProfile', dashEntityUrn: OWNER, firstName: 'Owner' }] });
const profile = ok({ included: [{ $type: 'com.linkedin.voyager.dash.identity.profile.Profile', publicIdentifier: 'Jane-Doe', entityUrn: LEAD, firstName: 'Jane' }] });
const PAGE = 20;
// A fake conversation list like LinkedIn's: the first-page query id ignores any cursor; only the PAGED query id (with its
// predicate, count and lastUpdatedBefore) pages: newest first, PAGE conversations a page, an empty page at the end.
// With ignoreCursor it answers the first page every time, as a server that did not move the cursor would.
const FIRST_ID = 'messengerConversations.0d5e6781bbee71c3e51c8843c6519f48', PAGED_ID = 'messengerConversations.9501074288a12f3ae9e3c7ea243bccbf';
const route = (conversations, messages, options = {}) => (url) => {
  if (url.includes('/voyager/api/me')) return me;
  if (url.includes('voyagerIdentityDashProfiles')) return profile;
  if (url.includes('messengerConversations')) {
    const paged = url.includes('queryId=' + PAGED_ID) && url.includes('(query:(predicateUnions:List((conversationCategoryPredicate:(category:PRIMARY_INBOX)))),count:20,mailboxUrn:');
    if (!paged && !url.includes('queryId=' + FIRST_ID)) return bad(400);
    const m = paged ? /lastUpdatedBefore:(\d+)/.exec(url) : null;
    let list = conversations.slice().sort((a, b) => (b.lastActivityAt || 0) - (a.lastActivityAt || 0));
    const all = list;
    if (m && !options.ignoreCursor) list = list.filter((c) => (c.lastActivityAt || 0) < Number(m[1]));
    if (m && options.tailRepeat && list.length === 0) list = all.slice(-PAGE);
    if (options.failFrom !== undefined && m && !options.ignoreCursor && options.failFrom <= (options.counter.n = (options.counter.n || 0) + 1)) return bad(500);
    const node = { elements: options.unpaged ? conversations : list.slice(0, PAGE) };
    return ok({ data: paged && options.pagedKey ? { [options.pagedKey]: node } : { messengerConversationsBySyncToken: node } });
  }
  if (url.includes('messengerMessages')) return options.failMessages ? bad(500) : ok({ data: { messengerMessagesBySyncToken: { elements: messages } } });
  return bad(404);
};
const message = (at, text, sender) => ({
  entityUrn: 'urn:li:msg_message:(' + at + ')', deliveredAt: at, sender: sender ? { hostIdentityUrn: sender, firstName: 'Name' } : undefined,
  actor: { hostIdentityUrn: OWNER }, body: { text, attributes: [1] }, reactionSummaries: [1], renderContent: [{ file: 'x' }],
});
const one = { entityUrn: CONV, conversationParticipants: [{ hostIdentityUrn: OWNER, participantType: { member: { firstName: { text: 'A' } } } }, { hostIdentityUrn: LEAD }], lastActivityAt: 5 };
const group = { entityUrn: 'urn:li:msg_conversation:(x,G)', conversationParticipants: [{ hostIdentityUrn: OWNER }, { hostIdentityUrn: LEAD }, { hostIdentityUrn: OTHER }], lastActivityAt: 99 };
const filler = (n, lastActivityAt) => ({ entityUrn: 'urn:li:msg_conversation:(x,F' + n + ')', conversationParticipants: [{ hostIdentityUrn: OWNER }, { hostIdentityUrn: 'urn:li:fsd_profile:FILL' + n }], lastActivityAt });
const fillers = (count) => Array.from({ length: count }, (_, i) => filler(i, 1000000 - i * 1000));
const elsewhere = { entityUrn: 'urn:li:msg_conversation:(x,E)', conversationParticipants: [{ hostIdentityUrn: OWNER }, { hostIdentityUrn: OTHER }], lastActivityAt: 50 };
(async () => {
  const out = {};
  let r = await run('jane-doe', route([group, elsewhere, one], [message(2000, 'hello back', LEAD), message(1000, 'hi', OWNER), message(3000, '   ', OWNER), message(4000, 'no sender', null)]));
  out.found = r.result;
  out.urls = r.calls.map((c) => c.url.replace('https://www.linkedin.com/voyager/api', ''));
  out.credentials = r.calls.map((c) => c.init.credentials);
  out.leaked = JSON.stringify(r.result).includes(TOKEN);
  out.none = (await run('jane-doe', route([group, elsewhere], []))).result;
  out.forbidden = (await run('jane-doe', () => bad(403))).result;
  r = await run('jane-doe', route([one], []), '');
  out.signedOut = r.result; out.signedOutCalls = r.calls.length;
  r = await run('', route([one], []));
  out.emptyId = r.result; out.emptyIdCalls = r.calls.length;
  out.network = (await run('jane-doe', () => { throw new Error('net'); })).result;
  out.sameMember = (await run('jane-doe', (url) => (url.includes('voyagerIdentityDashProfiles')
    ? ok({ included: [{ $type: 'com.linkedin.voyager.dash.identity.profile.Profile', publicIdentifier: 'jane-doe', entityUrn: OWNER }] }) : route([one], [])(url)))).result;
  const many = Array.from({ length: 120 }, (_, i) => message(1000 + i, 'm' + i, i % 2 ? LEAD : OWNER));
  out.capped = (await run('jane-doe', route([one], many))).result.messages.length;

  // Paging the conversation list.
  const strip = (r) => r.calls.map((c) => decodeURIComponent(c.url.replace('https://www.linkedin.com/voyager/api', '')));
  const deep = { ...one, lastActivityAt: 500000 };
  r = await run('jane-doe', route([...fillers(45), deep], [message(1000, 'hi', OWNER)]));
  out.page3 = r.result; out.page3Urls = strip(r);
  r = await run('jane-doe', route([...fillers(20), deep], [message(1000, 'hi', OWNER)]));
  out.page2 = r.result; out.page2Urls = strip(r);
  out.page2Raw = r.calls.map((c) => c.url);
  r = await run('jane-doe', route([...fillers(20), deep], [message(1000, 'hi', OWNER)], { pagedKey: 'messengerConversationsByCategory' }));
  out.altKey = r.result;
  r = await run('jane-doe', route(fillers(25), []));
  out.exhausted = r.result; out.exhaustedUrls = strip(r);
  r = await run('jane-doe', route([], []));
  out.emptyList = r.result; out.emptyListCalls = strip(r).length;
  r = await run('jane-doe', route([...fillers(200), deep], []));
  out.limit = r.result; out.limitUrls = strip(r);
  r = await run('jane-doe', route(fillers(30), [], { ignoreCursor: true }));
  out.stalled = r.result; out.stalledUrls = strip(r);
  r = await run('jane-doe', route(fillers(20), [], { tailRepeat: true }));
  out.tailRepeat = r.result; out.tailRepeatUrls = strip(r);
  r = await run('jane-doe', route([...fillers(20), { ...deep, lastActivityAt: 1 }], [], { ignoreCursor: true }));
  out.repeatHidesLead = r.result;
  r = await run('jane-doe', route(fillers(20).map((c) => ({ ...c, lastActivityAt: undefined })), []));
  out.fullNoActivity = r.result; out.fullNoActivityCalls = strip(r).length;
  r = await run('jane-doe', route(fillers(5).map((c) => ({ ...c, lastActivityAt: undefined })), []));
  out.noActivity = r.result; out.noActivityCalls = strip(r).length;
  r = await run('jane-doe', route([...fillers(45), deep], [], { failFrom: 1, counter: {} }));
  out.laterPageFails = r.result; out.laterPageFailsCalls = strip(r).length;
  r = await run('jane-doe', route([...fillers(25), deep], [message(1000, 'hi', OWNER)], { failMessages: true }));
  out.messagesFail = r.result;
  // A thread whose text carries zero-width and non-BMP characters must come back untouched and be digested as UTF-8.
  const odd = 'hi​there é 😀   "quoted" \\ back\tslash\u0001';
  r = await run('jane-doe', route([one], [message(1000, odd, LEAD)]));
  out.odd = r.result; out.oddText = odd;
  console.log(JSON.stringify(out));
})();
"""


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def fnv1a32(data: bytes) -> str:
    h = 0x811C9DC5
    for byte in data:
        h = ((h ^ byte) * 0x01000193) & 0xFFFFFFFF
    return f"{h:08x}"


def digest_of(payload: dict) -> str:
    """The integrity digest, computed independently of the script: canonical JSON of the payload without `integrity`."""
    body = {key: value for key, value in payload.items() if key != "integrity"}
    return fnv1a32(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def sealed_correctly(record: dict) -> bool:
    return (
        list(record)[-1] == "integrity"
        and record["integrity"] == {"algorithm": "fnv1a32", "digest": digest_of(record)}
        and len(record["integrity"]["digest"]) == 8
    )


KEYS = ["status", "signedIn", "capturedAt", "state", "source", "publicIdentifier", "conversationUrn", "participants", "messages",
        "coverage", "pagesRead", "integrity"]
FILLER_ACTIVITY = lambda i: 1000000 - i * 1000  # noqa: E731 - mirrors the harness


def PAGED_VARIABLES(cursor: int) -> str:
    return ("(query:(predicateUnions:List((conversationCategoryPredicate:(category:PRIMARY_INBOX)))),count:20,"
            f"mailboxUrn:urn:li:fsd_profile:OWNERID1,lastUpdatedBefore:{cursor})")


def conversation_urls(urls: list[str]) -> list[str]:
    return [u for u in urls if "messengerConversations" in u]


def main() -> None:
    node = shutil.which("node")
    if node is None:
        print("SKIP: node is not installed, so the thread script was not run against a fake LinkedIn.")
        return
    done = subprocess.run([node, "-e", HARNESS, str(SCRIPT)], capture_output=True, text=True, encoding="utf-8", check=False)
    check(done.returncode == 0, f"harness failed: {done.stderr[-400:]}")
    out = json.loads(done.stdout)

    found = out["found"]
    check(list(found) == KEYS, f"unexpected keys {list(found)}")
    check(found["status"] == 200 and found["signedIn"] is True and found["state"] == "ok", "found thread not ok")
    check(found["coverage"] == "complete" and found["pagesRead"] == 1, "a thread found on page 1 is not complete after one page")
    check(found["source"] == "linkedin-voyager-messages" and found["publicIdentifier"] == "jane-doe", "source or identifier wrong")
    check(found["conversationUrn"] == "urn:li:msg_conversation:(urn:li:fsd_profile:OWNERID1,2-ABC==)", "wrong conversation chosen")
    check(found["participants"] == ["urn:li:fsd_profile:OWNERID1", "urn:li:fsd_profile:LEADID01"], "participants are not the two member URNs")
    # Oldest first; the blank message is dropped; sender is the message's sender, never its actor (the viewer).
    check([m["text"] for m in found["messages"]] == ["hi", "hello back", "no sender"], "messages not oldest first or blank kept")
    check([m["senderUrn"] for m in found["messages"]] == ["urn:li:fsd_profile:OWNERID1", "urn:li:fsd_profile:LEADID01", None],
          "sender taken from the wrong field")
    check(all(list(m) == ["messageUrn", "deliveredAt", "senderUrn", "text"] for m in found["messages"]), "a message carries extra fields")
    check(found["messages"][0]["deliveredAt"] == "1970-01-01T00:00:01.000Z", "delivery time is not ISO")
    check(out["leaked"] is False, "the CSRF token reached the result")
    check(all(c == "include" for c in out["credentials"]), "a call did not use the page's own session")
    check(len(out["urls"]) == 4 and all(not u.startswith("http") for u in out["urls"]), "an unexpected call was made")
    check(out["urls"][0] == "/me" and "vanityName:jane-doe)" in out["urls"][1], "owner and Lead were not resolved first")
    check(out["urls"][2].endswith("variables=(mailboxUrn:urn%3Ali%3Afsd_profile%3AOWNERID1)"), "first conversation call is not exactly the owner's mailbox")
    check("lastUpdatedBefore" not in out["urls"][2], "first conversation call carried a cursor")
    check("%28" in out["urls"][3] and "%29" in out["urls"][3] and "%2C" in out["urls"][3] and "(urn:li" not in out["urls"][3].split("conversationUrn:")[1],
          "conversation URN not percent-encoded in the messages call")

    # Paging: the cursor is the oldest lastActivityAt of the page just read; reading stops at the conversation.
    page3 = out["page3"]
    urls = conversation_urls(out["page3Urls"])
    check(page3["state"] == "ok" and page3["coverage"] == "complete" and page3["pagesRead"] == 3 and len(urls) == 3, "conversation on page 3 not found after three pages")
    check("lastUpdatedBefore" not in urls[0], "first page carried a cursor")
    check(urls[1].endswith(f"variables={PAGED_VARIABLES(FILLER_ACTIVITY(19))}"), f"page 2 variables wrong: {urls[1]}")
    check(urls[2].endswith(f"variables={PAGED_VARIABLES(FILLER_ACTIVITY(39))}"), f"page 3 variables wrong: {urls[2]}")
    check("queryId=messengerConversations.0d5e6781bbee71c3e51c8843c6519f48&" in urls[0] and all("queryId=messengerConversations.9501074288a12f3ae9e3c7ea243bccbf&" in u for u in urls[1:]),
          "page 1 must use the first-page query id and pages 2 and up the paged one")
    raw = conversation_urls(out["page2Raw"])
    check(raw[1].endswith("&variables=(query:(predicateUnions:List((conversationCategoryPredicate:(category:PRIMARY_INBOX)))),count:20,"
                          f"mailboxUrn:urn%3Ali%3Afsd_profile%3AOWNERID1,lastUpdatedBefore:{FILLER_ACTIVITY(19)})"), f"page 2 address not exactly LinkedIn's form: {raw[1]}")
    check(out["page3Urls"][-1].count("messengerMessages") == 1, "messages not read after the conversation was found")
    check(out["altKey"]["state"] == "ok" and out["altKey"]["pagesRead"] == 2 and out["altKey"]["coverage"] == "complete",
          "a paged answer under another top-level key was not read")
    page2 = out["page2"]
    check(page2["state"] == "ok" and page2["pagesRead"] == 2 and page2["coverage"] == "complete", "conversation on page 2 not found after two pages")

    none = out["none"]
    check(none["state"] == "no-conversation" and none["status"] == 200 and none["conversationUrn"] is None
          and none["participants"] == [] and none["messages"] == [], "no-conversation not reported")
    check(none["coverage"] == "complete" and none["pagesRead"] == 1, "a short page (2 conversations) is not complete after one page")
    exhausted = out["exhausted"]
    check(exhausted["state"] == "no-conversation" and exhausted["coverage"] == "complete" and exhausted["pagesRead"] == 2
          and len(conversation_urls(out["exhaustedUrls"])) == 2, "a short last page (20, then 5) is not complete after two pages")
    check(out["emptyList"]["state"] == "no-conversation" and out["emptyList"]["coverage"] == "complete" and out["emptyList"]["pagesRead"] == 1
          and out["emptyListCalls"] == 3, "an empty list is not complete after one page")
    limit = out["limit"]
    check(limit["state"] == "no-conversation" and limit["coverage"] == "page-limit" and limit["pagesRead"] == 8
          and len(conversation_urls(out["limitUrls"])) == 8 and len(out["limitUrls"]) == 10,
          "not found after eight full pages is not no-conversation with page-limit and exactly eight conversation calls")
    check(limit["participants"] == [] and limit["messages"] == [] and limit["conversationUrn"] is None, "page-limit result carries a thread")
    stalled = out["stalled"]
    check(stalled["state"] == "no-conversation" and stalled["coverage"] == "complete" and stalled["pagesRead"] == 2
          and len(conversation_urls(out["stalledUrls"])) == 2, "a repeated page (no new elements) is not the end of the list, complete")
    tail = out["tailRepeat"]
    check(tail["state"] == "no-conversation" and tail["coverage"] == "complete" and tail["pagesRead"] == 2
          and len(conversation_urls(out["tailRepeatUrls"])) == 2, "the tail repeated for an older cursor is not complete after two pages")
    check(out["repeatHidesLead"]["state"] == "no-conversation" and out["repeatHidesLead"]["coverage"] == "complete",
          "the Lead was searched among elements that are not new")
    check(out["noActivity"]["coverage"] == "complete" and out["noActivity"]["pagesRead"] == 1 and out["noActivity"]["state"] == "no-conversation"
          and out["noActivityCalls"] == 3, "a short page without readable lastActivityAt is not the end of the list")
    check(out["fullNoActivity"]["coverage"] == "page-limit" and out["fullNoActivity"]["pagesRead"] == 1 and out["fullNoActivity"]["state"] == "no-conversation"
          and out["fullNoActivityCalls"] == 3, "a full page without readable lastActivityAt must stop as page-limit, since the cursor cannot move")

    for name, status, pages in (("forbidden", 403, 0), ("network", 0, 0), ("sameMember", 0, 0), ("laterPageFails", 500, 1), ("messagesFail", 500, 2)):
        record = out[name]
        check(record["status"] == status and record["state"] == "error" and record["conversationUrn"] is None
              and record["participants"] == [] and record["messages"] == [], f"{name}: error not reduced to status and empty lists")
        check(record["coverage"] == "page-limit" and record["pagesRead"] == pages, f"{name}: coverage or pagesRead wrong ({record['coverage']}, {record['pagesRead']})")
    check(out["laterPageFailsCalls"] == 4, "a failed conversation page was retried or not reached")
    for name in ("signedOut", "emptyId"):
        check(out[name]["coverage"] == "page-limit" and out[name]["pagesRead"] == 0, f"{name}: nothing was called, so nothing was read")
    check(out["signedOut"]["signedIn"] is False and out["signedOut"]["status"] == 0 and out["signedOutCalls"] == 0, "signed-out script still called LinkedIn")
    check(out["emptyId"]["state"] == "error" and out["emptyIdCalls"] == 0, "empty identifier still called LinkedIn")
    check(out["capped"] == 98, "messages not capped at the newest 98")

    # Unusual text survives untouched.
    odd = out["odd"]
    check(odd["messages"][0]["text"] == out["oddText"] and "​" in odd["messages"][0]["text"] and "\U0001f600" in odd["messages"][0]["text"],
          "zero-width or non-BMP characters were changed")

    # Integrity: every result is sealed, and the digest equals an independent implementation's.
    results = [v for key, v in out.items() if isinstance(v, dict) and "integrity" in v or key in ("signedOut", "emptyId")]
    check(len(results) >= 15, f"too few sealed results were checked ({len(results)})")
    for record in results:
        check(sealed_correctly(record), f"integrity missing, not last, or wrong on a {record['state']} result")
    check(odd["integrity"]["digest"] == digest_of(odd), "the digest of a thread with zero-width and non-BMP characters differs from the independent one")
    check(not any(key == "csrf" for key in found), "the result names a csrf key")
    altered = json.loads(json.dumps(found))
    altered["messages"][0]["text"] += "."
    check(digest_of(altered) != found["integrity"]["digest"], "altering a message did not change the digest")
    print("PASS: the thread script pages the conversation list with coverage, returns only the sealed evidence record, never the token, and never throws.")


if __name__ == "__main__":
    main()
