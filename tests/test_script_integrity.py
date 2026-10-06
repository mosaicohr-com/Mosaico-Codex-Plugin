#!/usr/bin/env python3
"""Every approved browser script seals what it returns with an integrity digest Mosaico can recompute.

Each script is run under node against a fake page and a fake LinkedIn: no network, no real cookie. The digest is
FNV-1a 32-bit over the UTF-8 bytes of the canonical JSON (keys sorted, no spaces, object keys whose value is null
or undefined omitted at every depth, array items kept) of the returned payload without its `integrity` field.
The omission matters because the claude.ai connector drops null-valued keys in transit. The check below recomputes it with an independent Python implementation. Skipped (and says
so) when node is not installed.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BROWSER = ROOT / "plugins" / "mosaico-claude" / "browser"
SCRIPTS = {
    "whoami": "linkedin-whoami.js",
    "evidence": "linkedin-connection-evidence.js",
    "connections": "linkedin-recent-connections.js",
    "thread": "linkedin-thread-messages.js",
    "sent": "linkedin-sent-invitations.js",
}

HARNESS = r"""
const fs = require('fs');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const DIR = process.argv[1];
const TOKEN = 'ajax:SECRET-TOKEN';
async function run(file, firstLine, routes, cookie = 'JSESSIONID="' + TOKEN + '"') {
  const calls = [];
  const src = fs.readFileSync(DIR + '/' + file, 'utf8');
  const body = firstLine + '\n' + src.split('\n').slice(1).join('\n');
  const wrapped = new AsyncFunction('document', 'fetch', 'return await (async () => {' + body.replace(/\n\(\{/, '\nreturn ({') + '})();');
  const result = await wrapped({ cookie }, async (url, init) => { calls.push(url); return routes(url, init); });
  return { result, calls };
}
const ok = (j) => ({ ok: true, status: 200, json: async () => j });
const bad = (s) => ({ ok: false, status: s, json: async () => ({}) });
const OWNER = 'urn:li:fsd_profile:OWNERID1', LEAD = 'urn:li:fsd_profile:LEADID01';
const ODD = 'hi​there é 😀 "q" \\ x\u0001';
(async () => {
const out = {};

// whoami
const whoamiRoute = () => ok({ data: { plainId: 1234 }, included: [
  { $type: 'com.linkedin.voyager.identity.shared.MiniProfile', entityUrn: 'urn:li:fs_miniProfile:M', dashEntityUrn: OWNER, publicIdentifier: 'owner', firstName: 'Secret' }] });
out.whoami = (await run('linkedin-whoami.js', 'const NOOP = 0;', whoamiRoute)).result;
out.whoamiFailed = (await run('linkedin-whoami.js', 'const NOOP = 0;', () => bad(403))).result;
out.whoamiSignedOut = (await run('linkedin-whoami.js', 'const NOOP = 0;', whoamiRoute, '')).result;

// connection evidence
const evidenceRoute = () => ok({ included: [
  { $type: 'com.linkedin.voyager.dash.relationships.MemberRelationship', entityUrn: 'urn:li:fsd_memberRelationship:X', memberRelationship: { connection: {} }, extra: 'dropped' },
  { $type: 'com.linkedin.voyager.dash.identity.profile.Profile', publicIdentifier: 'jane-doe', entityUrn: LEAD, firstName: 'Jane' }] });
out.evidence = (await run('linkedin-connection-evidence.js', 'const PUBLIC_IDENTIFIER = "jane-doe";', evidenceRoute)).result;
out.evidenceFailed = (await run('linkedin-connection-evidence.js', 'const PUBLIC_IDENTIFIER = "jane-doe";', () => { throw new Error('net'); })).result;

// recent connections: a full first page, a short second page
const connection = (n, at) => ({ $type: 'com.linkedin.voyager.dash.relationships.Connection', entityUrn: 'urn:li:fsd_connection:C' + n, createdAt: at, '*connectedMemberResolutionResult': 'urn:li:fsd_profile:P' + n, noise: 'dropped' });
const member = (n) => ({ $type: 'com.linkedin.voyager.dash.identity.profile.Profile', entityUrn: 'urn:li:fsd_profile:P' + n, publicIdentifier: 'person-' + n, firstName: 'Secret' });
const connectionsPage = (from, count) => ok({
  data: { '*elements': Array.from({ length: count }, (_, i) => 'urn:li:fsd_connection:C' + (from + i)) },
  included: Array.from({ length: count }, (_, i) => [connection(from + i, 1759000000000 - (from + i) * 1000), member(from + i)]).flat(),
});
const connectionsRoute = (url) => (new URL(url).searchParams.get('start') === '0' ? connectionsPage(0, 40) : connectionsPage(40, 3));
out.connections = (await run('linkedin-recent-connections.js', 'const STOP_AT = 0;', connectionsRoute)).result;
out.connectionsStopped = (await run('linkedin-recent-connections.js', 'const STOP_AT = 1759000000000;', connectionsRoute)).result;
out.connectionsFailed = (await run('linkedin-recent-connections.js', 'const STOP_AT = 0;', () => bad(500))).result;

// thread
const message = (at, text, sender) => ({ entityUrn: 'urn:li:msg_message:(' + at + ')', deliveredAt: at, sender: { hostIdentityUrn: sender }, body: { text } });
const threadRoute = (url) => {
  if (url.includes('/voyager/api/me')) return ok({ included: [{ $type: 'x.MiniProfile', dashEntityUrn: OWNER }] });
  if (url.includes('voyagerIdentityDashProfiles')) return ok({ included: [{ $type: 'x.profile.Profile', publicIdentifier: 'jane-doe', entityUrn: LEAD }] });
  if (url.includes('messengerConversations')) return ok({ data: { messengerConversationsBySyncToken: { elements: /messengerConversations\.9501074288a12f3ae9e3c7ea243bccbf/.test(url) ? [] : [
    { entityUrn: 'urn:li:msg_conversation:(a,B)', conversationParticipants: [{ hostIdentityUrn: OWNER }, { hostIdentityUrn: LEAD }], lastActivityAt: 7 }] } } });
  if (url.includes('messengerMessages')) return ok({ data: { messengerMessagesBySyncToken: { elements: [message(2000, ODD, LEAD), message(1000, 'hello', OWNER)] } } });
  return bad(404);
};
out.thread = (await run('linkedin-thread-messages.js', 'const PUBLIC_IDENTIFIER = "jane-doe";', threadRoute)).result;
out.threadFailed = (await run('linkedin-thread-messages.js', 'const PUBLIC_IDENTIFIER = "jane-doe";', () => bad(403))).result;

// sent invitations
const sentRoute = (url) => url.includes('voyagerIdentityDashProfiles') ? ok({ included: [{ $type: 'x.profile.Profile', publicIdentifier: /vanityName:([^)]*)\)/.exec(url)[1], entityUrn: /vanityName:jane-doe\)/.test(url) ? LEAD : 'urn:li:fsd_profile:NOBODY01' }] }) : ok({ data: { elements: ['v'] }, included: [
  { $type: 'x.invitation.SentInvitationView', entityUrn: 'urn:li:fs_relInvitationView:V', '*invitation': 'urn:li:fs_relInvitation:I', '*toMember': 'urn:li:fs_miniProfile:M' },
  { $type: 'x.invitation.Invitation', entityUrn: 'urn:li:fs_relInvitation:I', sentTime: 1759700000000, '*toMember': 'urn:li:fs_miniProfile:M' },
  { $type: 'x.MiniProfile', entityUrn: 'urn:li:fs_miniProfile:M', dashEntityUrn: LEAD, publicIdentifier: 'jane-doe' }] });
out.sent = (await run('linkedin-sent-invitations.js', 'const PUBLIC_IDENTIFIER = "jane-doe";', sentRoute)).result;
out.sentNotFound = (await run('linkedin-sent-invitations.js', 'const PUBLIC_IDENTIFIER = "nobody";', sentRoute)).result;
out.sentFailed = (await run('linkedin-sent-invitations.js', 'const PUBLIC_IDENTIFIER = "jane-doe";', () => bad(500))).result;

out.leaked = JSON.stringify(out).includes(TOKEN) || JSON.stringify(out).includes('Secret');
out.odd = ODD;
console.log(JSON.stringify(out));
})();
"""

GOLDEN = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[1], 'utf8').split('\n');
const helpers = src.filter((l) => /^const (isObj|canonical|fnv1a32) = /.test(l)).join('\n');
const { canonical, fnv1a32 } = new Function(helpers + '\nreturn { canonical, fnv1a32 };')();
const payload = { status: 200, signedIn: true, text: 'hi​there é 😀', urn: 'urn:li:fsd_profile:ABC_def-123', n: [1, null, 2.5], z: { b: false, a: null } };
console.log(JSON.stringify({ text: canonical(payload), digest: fnv1a32(canonical(payload)), empty: fnv1a32(''), a: fnv1a32('a'), foobar: fnv1a32('foobar'),
  undef: canonical({ a: undefined, b: [undefined, 1] }),
  nullFree: canonical({ a: null, b: [null, { c: null, d: 1 }], e: { f: null }, g: 0 }),
  withNulls: fnv1a32(canonical({ x: 1, y: { z: null }, w: null, l: [null] })), withoutNulls: fnv1a32(canonical({ x: 1, y: {}, l: [null] })),
  changed: fnv1a32(canonical({ x: 2, y: {}, l: [null] })) }));
"""


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def fnv1a32(data: bytes) -> str:
    h = 0x811C9DC5
    for byte in data:
        h = ((h ^ byte) * 0x01000193) & 0xFFFFFFFF
    return f"{h:08x}"


def null_free(value: object) -> object:
    """Drops object keys whose value is null at every depth; array items (null ones included) stay."""
    if isinstance(value, dict):
        return {k: null_free(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [null_free(v) for v in value]
    return value


def canonical(value: object) -> str:
    return json.dumps(null_free(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest_of(record: dict) -> str:
    return fnv1a32(canonical({k: v for k, v in record.items() if k != "integrity"}).encode("utf-8"))


def check_sealed(name: str, record: dict) -> None:
    check(list(record)[-1] == "integrity", f"{name}: integrity is not the last field")
    check(set(record["integrity"]) == {"algorithm", "digest"} and record["integrity"]["algorithm"] == "fnv1a32", f"{name}: wrong integrity shape")
    check(re.fullmatch(r"[0-9a-f]{8}", record["integrity"]["digest"]) is not None, f"{name}: digest is not 8 lowercase hex characters")
    check(record["integrity"]["digest"] == digest_of(record), f"{name}: digest differs from the independent implementation")
    altered = json.loads(json.dumps(record))
    altered["status"] = altered["status"] + 1
    check(digest_of(altered) != record["integrity"]["digest"], f"{name}: changing a value did not change the digest")
    altered = json.loads(json.dumps(record))
    altered["extra"] = 1
    check(digest_of(altered) != record["integrity"]["digest"], f"{name}: adding a field did not change the digest")


def main() -> None:
    node = shutil.which("node")
    if node is None:
        print("SKIP: node is not installed, so the integrity digests were not checked against the scripts.")
        return

    # The golden vector, run through the helper text each script carries.
    expected_text = ('{"n":[1,null,2.5],"signedIn":true,"status":200,"text":"hi​there é \U0001f600",'
                     '"urn":"urn:li:fsd_profile:ABC_def-123","z":{"b":false}}')
    check(fnv1a32(b"") == "811c9dc5" and fnv1a32(b"a") == "e40c292c" and fnv1a32(b"foobar") == "bf9cf968", "the Python FNV-1a does not match the standard vectors")
    check(fnv1a32(expected_text.encode("utf-8")) == "aa3bbe69", "the golden vector's digest is not aa3bbe69")
    helper_texts = set()
    for name in SCRIPTS.values():
        done = subprocess.run([node, "-e", GOLDEN, str(BROWSER / name)], capture_output=True, text=True, encoding="utf-8", check=False)
        check(done.returncode == 0, f"{name}: golden snippet failed: {done.stderr[-300:]}")
        golden = json.loads(done.stdout)
        check(golden["text"] == expected_text and golden["digest"] == "aa3bbe69", f"{name}: golden vector differs ({golden['digest']})")
        check((golden["empty"], golden["a"], golden["foobar"]) == ("811c9dc5", "e40c292c", "bf9cf968"), f"{name}: FNV-1a standard vectors differ")
        check(golden["undef"] == '{"b":[null,1]}', f"{name}: undefined is not dropped from objects and nulled in arrays")
        check(golden["nullFree"] == '{"b":[null,{"d":1}],"e":{},"g":0}', f"{name}: null-valued keys are not omitted at every depth, or array items changed ({golden['nullFree']})")
        check(golden["withNulls"] == golden["withoutNulls"], f"{name}: a payload with and without its null keys gives different digests")
        check(golden["withNulls"] != golden["changed"], f"{name}: a changed value gives the same digest")
        check(golden["withNulls"] == fnv1a32(canonical({"x": 1, "y": {"z": None}, "w": None, "l": [None]}).encode("utf-8")), f"{name}: digest differs from the Python mirror")
        header = (BROWSER / name).read_text(encoding="utf-8")
        check("the canonical JSON (keys sorted, no spaces, with null-valued keys omitted) of everything else" in header, f"{name}: header integrity sentence not updated")
        lines = (BROWSER / name).read_text(encoding="utf-8").split("\n")
        helper_texts.add("\n".join(line for line in lines if line.startswith(("const canonical = ", "const fnv1a32 = "))))
    check(len(helper_texts) == 1 and next(iter(helper_texts)).count("\n") == 1, "the digest helpers are not identical text in all five scripts")

    done = subprocess.run([node, "-e", HARNESS, str(BROWSER)], capture_output=True, text=True, encoding="utf-8", check=False)
    check(done.returncode == 0, f"harness failed: {done.stderr[-500:]}")
    out = json.loads(done.stdout)
    check(out["leaked"] is False, "the token or a dropped name reached a result")

    sealed = [k for k in out if isinstance(out[k], dict)]
    check(sealed == ["whoami", "whoamiFailed", "whoamiSignedOut", "evidence", "evidenceFailed", "connections", "connectionsStopped", "connectionsFailed",
                     "thread", "threadFailed", "sent", "sentNotFound", "sentFailed"], f"unexpected results {sealed}")
    for name in sealed:
        check_sealed(name, out[name])

    check(list(out["whoami"]) == ["status", "signedIn", "capturedAt", "plainId", "entries", "integrity"], "whoami keys changed")
    check(out["whoami"]["plainId"] == 1234 and len(out["whoami"]["entries"]) == 1 and out["whoamiFailed"]["status"] == 403, "whoami content changed")
    check(out["whoamiSignedOut"]["signedIn"] is False, "signed-out whoami reported signed in")
    check(list(out["evidence"]) == ["status", "signedIn", "capturedAt", "state", "errorStep", "profileIdentifier", "requestedIdentifier", "resolvedIdentifier", "memberUrn",
                                    "entries", "integrity"] and len(out["evidence"]["entries"]) == 2, "evidence keys or entries changed")
    check(out["evidenceFailed"]["state"] == "error" and out["evidenceFailed"]["errorStep"] == "profile" and out["evidenceFailed"]["entries"] == [], "failed evidence not reported")
    check(list(out["sent"]) == ["status", "signedIn", "capturedAt", "state", "errorStep", "publicIdentifier", "requestedIdentifier", "resolvedIdentifier", "memberUrn",
                                "invitation", "pagesRead", "integrity"]
          and out["sent"]["state"] == "found" and out["sentNotFound"]["state"] == "not-found", "sent-invitations content changed")

    # Thread: the new coverage fields sit before the seal; odd characters survive and are digested as UTF-8.
    thread = out["thread"]
    check(list(thread) == ["status", "signedIn", "capturedAt", "state", "errorStep", "source", "publicIdentifier", "requestedIdentifier", "requestedName", "resolvedIdentifier", "memberUrn", "matchBasis", "displayName",
                           "conversationUrn", "participants", "messages", "coverage", "lookup", "pagesRead", "searchPagesRead", "integrity"], "thread keys changed")
    check(thread["state"] == "ok" and thread["coverage"] == "complete" and thread["pagesRead"] == 1, "thread coverage wrong")
    # 0.8.5: text is normalised before it is sealed (zero-width and control characters go), so the sealed text is the normalised one.
    check(thread["messages"][1]["text"] == "hithere \u00e9 \U0001f600 \"q\" \\ x", f"non-BMP text lost or text not normalised: {thread['messages'][1]['text']!r}")
    check(digest_of(thread) == thread["integrity"]["digest"], "the thread digest is not over the normalised text")
    check(out["threadFailed"]["coverage"] == "page-limit" and out["threadFailed"]["pagesRead"] == 0 and out["threadFailed"]["searchPagesRead"] == 0 and out["threadFailed"]["lookup"] == "none", "failed thread coverage wrong")

    # Connections: every page is sealed on its own, and the whole result's digest covers the pages' seals.
    connections = out["connections"]
    check(list(connections) == ["status", "signedIn", "capturedAt", "pages", "integrity"], "connections keys changed")
    check(len(connections["pages"]) == 2 and len(out["connectionsStopped"]["pages"]) == 1 and out["connectionsFailed"]["pages"] == [], "connections paging changed")
    for index, page in enumerate(connections["pages"] + out["connectionsStopped"]["pages"]):
        check(list(page) == ["elements", "entries", "integrity"], f"page {index} keys are {list(page)}")
        check(page["integrity"] == {"algorithm": "fnv1a32", "digest": digest_of(page)}, f"page {index} carries a wrong digest")
        check(all(set(entry) <= {"$type", "entityUrn", "createdAt", "*connectedMemberResolutionResult", "publicIdentifier"} for entry in page["entries"]), "a page carries a dropped field")
    altered = json.loads(json.dumps(connections))
    altered["pages"][0]["integrity"]["digest"] = "00000000"
    check(digest_of(altered) != connections["integrity"]["digest"], "the whole result's digest does not cover the pages' seals")
    altered = json.loads(json.dumps(connections))
    altered["pages"][1]["entries"][0]["createdAt"] += 1
    check(digest_of(altered) != connections["integrity"]["digest"], "altering an entry did not change the whole result's digest")
    check(digest_of(altered["pages"][1]) != connections["pages"][1]["integrity"]["digest"], "altering an entry did not change its page's digest")
    print("PASS: all five approved scripts seal their result with an FNV-1a digest an independent implementation reproduces; the connections pages are sealed too.")


if __name__ == "__main__":
    main()
