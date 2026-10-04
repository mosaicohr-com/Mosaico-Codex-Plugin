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
const route = (conversations, messages) => (url) => {
  if (url.includes('/voyager/api/me')) return me;
  if (url.includes('voyagerIdentityDashProfiles')) return profile;
  if (url.includes('messengerConversations')) return ok({ data: { messengerConversationsBySyncToken: { elements: conversations } } });
  if (url.includes('messengerMessages')) return ok({ data: { messengerMessagesBySyncToken: { elements: messages } } });
  return bad(404);
};
const message = (at, text, sender) => ({
  entityUrn: 'urn:li:msg_message:(' + at + ')', deliveredAt: at, sender: sender ? { hostIdentityUrn: sender, firstName: 'Name' } : undefined,
  actor: { hostIdentityUrn: OWNER }, body: { text, attributes: [1] }, reactionSummaries: [1], renderContent: [{ file: 'x' }],
});
const one = { entityUrn: CONV, conversationParticipants: [{ hostIdentityUrn: OWNER, participantType: { member: { firstName: { text: 'A' } } } }, { hostIdentityUrn: LEAD }], lastActivityAt: 5 };
const group = { entityUrn: 'urn:li:msg_conversation:(x,G)', conversationParticipants: [{ hostIdentityUrn: OWNER }, { hostIdentityUrn: LEAD }, { hostIdentityUrn: OTHER }], lastActivityAt: 99 };
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
  console.log(JSON.stringify(out));
})();
"""


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> None:
    node = shutil.which("node")
    if node is None:
        print("SKIP: node is not installed, so the thread script was not run against a fake LinkedIn.")
        return
    done = subprocess.run([node, "-e", HARNESS, str(SCRIPT)], capture_output=True, text=True, check=False)
    check(done.returncode == 0, f"harness failed: {done.stderr[-400:]}")
    out = json.loads(done.stdout)

    found = out["found"]
    check(list(found) == ["status", "signedIn", "capturedAt", "state", "source", "publicIdentifier", "conversationUrn", "participants", "messages"],
          f"unexpected keys {list(found)}")
    check(found["status"] == 200 and found["signedIn"] is True and found["state"] == "ok", "found thread not ok")
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
    check("mailboxUrn:urn%3Ali%3Afsd_profile%3AOWNERID1)" in out["urls"][2], "conversation list not asked for the owner's mailbox")
    check("%28" in out["urls"][3] and "%29" in out["urls"][3] and "%2C" in out["urls"][3] and "(urn:li" not in out["urls"][3].split("conversationUrn:")[1],
          "conversation URN not percent-encoded in the messages call")

    none = out["none"]
    check(none["state"] == "no-conversation" and none["status"] == 200 and none["conversationUrn"] is None
          and none["participants"] == [] and none["messages"] == [], "no-conversation not reported")
    for name, status in (("forbidden", 403), ("network", 0), ("sameMember", 0)):
        record = out[name]
        check(record["status"] == status and record["state"] == "error" and record["conversationUrn"] is None
              and record["participants"] == [] and record["messages"] == [], f"{name}: error not reduced to status and empty lists")
    check(out["signedOut"]["signedIn"] is False and out["signedOut"]["status"] == 0 and out["signedOutCalls"] == 0, "signed-out script still called LinkedIn")
    check(out["emptyId"]["state"] == "error" and out["emptyIdCalls"] == 0, "empty identifier still called LinkedIn")
    check(out["capped"] == 98, "messages not capped at the newest 98")
    print("PASS: the thread script returns only the evidence record, oldest first, never the token, and never throws.")


if __name__ == "__main__":
    main()
