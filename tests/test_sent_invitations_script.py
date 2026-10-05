#!/usr/bin/env python3
"""The approved sent-invitations script reduces LinkedIn's sent-invitations list to one small record and nothing else.

It is run under node against a fake page and a fake LinkedIn: no network, no real cookie. The check is skipped
(and says so) when node is not installed. The endpoint has not been run against a live account (validated:
pending), so the fake answers in the documented normalized shape; the gate checks below do not depend on that.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "mosaico-claude"
SCRIPT = PLUGIN / "browser" / "linkedin-sent-invitations.js"

spec = importlib.util.spec_from_file_location("gate", PLUGIN / "hooks" / "browser-script-gate.py")
gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gate)

SOURCE = SCRIPT.read_text(encoding="utf-8")
TOOL = "mcp__Claude_Browser__javascript_tool"
CHROME_TOOL = "mcp__claude-in-chrome__javascript_tool"

HARNESS = r"""
const fs = require('fs');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const SRC = fs.readFileSync(process.argv[1], 'utf8');
const TOKEN = 'ajax:SECRET-TOKEN';
async function run(id, routes, cookie = 'JSESSIONID="' + TOKEN + '"') {
  const calls = [];
  const body = SRC.replace('const PUBLIC_IDENTIFIER = "";', 'const PUBLIC_IDENTIFIER = ' + JSON.stringify(id) + ';');
  const wrapped = new AsyncFunction('document', 'fetch', 'return await (async () => {' + body.replace(/\n\(\{/, '\nreturn ({') + '})();');
  const result = await wrapped({ cookie }, async (url, init) => { calls.push({ url, init }); return routes(url, init); });
  return { result, calls };
}
const ok = (j) => ({ ok: true, status: 200, json: async () => j });
const bad = (s) => ({ ok: false, status: s, json: async () => ({}) });
const TYPE = 'com.linkedin.voyager.relationships.invitation.';
// One invitation as LinkedIn's normalized answer holds it: a view, the invitation it points at, the invitee's MiniProfile.
const entries = (n, identifier, sentTime) => [
  { $type: TYPE + 'SentInvitationView', entityUrn: 'urn:li:fs_relInvitationView:V' + n, '*invitation': 'urn:li:fs_relInvitation:INV' + n, '*toMember': 'urn:li:fs_miniProfile:MINI' + n },
  { $type: TYPE + 'Invitation', entityUrn: 'urn:li:fs_relInvitation:INV' + n, sentTime, message: 'a private note', '*toMember': 'urn:li:fs_miniProfile:MINI' + n, toMemberId: 'MEMBER' + n },
  { $type: 'com.linkedin.voyager.identity.shared.MiniProfile', entityUrn: 'urn:li:fs_miniProfile:MINI' + n, dashEntityUrn: 'urn:li:fsd_profile:MEMBER' + n, publicIdentifier: identifier, firstName: 'Secret', lastName: 'Name', occupation: 'Boss', picture: { rootUrl: 'x' } },
];
const pageOf = (items, total = items.length) => ok({
  data: { elements: Array.from({ length: total }, (_, i) => 'urn:li:fs_relInvitationView:V' + i), paging: { start: 0, count: 100 } },
  included: items.flat(),
});
const filler = (from, count) => Array.from({ length: count }, (_, i) => entries(from + i, 'someone-' + (from + i), 1759000000000 + i));
const route = (...pages) => (url) => {
  if (!url.includes('/voyager/api/relationships/sentInvitationViewsV2')) return bad(404);
  const start = Number(new URL(url).searchParams.get('start'));
  const page = pages[start / 100];
  return page === undefined ? pageOf([]) : page;
};
(async () => {
  const out = {};
  const SENT = 1759700000000;
  let r = await run('jane-doe', route(pageOf([...filler(1, 3), entries(50, 'Jane-Doe', SENT), entries(51, 'someone-else', 1759100000000)])));
  out.found = r.result;
  out.urls = r.calls.map((c) => c.url.replace('https://www.linkedin.com/voyager/api', ''));
  out.headers = r.calls.map((c) => c.init.headers);
  out.credentials = r.calls.map((c) => c.init.credentials);
  out.leaked = JSON.stringify(r.result).includes(TOKEN);
  out.secrets = ['Secret', 'Name', 'private note', 'Boss', 'rootUrl'].some((s) => JSON.stringify(r.result).includes(s));
  const paged = await run('jane-doe', route(pageOf(filler(1, 100)), pageOf(filler(101, 100)), pageOf([entries(250, 'jane-doe', SENT)])));
  out.paging = paged.result;
  out.pagedUrls = paged.calls.map((c) => c.url.replace('https://www.linkedin.com/voyager/api', ''));
  const five = await run('jane-doe', route(...Array.from({ length: 6 }, (_, p) => pageOf(filler(p * 100 + 1, 100)))));
  out.five = five.result; out.fiveCalls = five.calls.length;
  const short = await run('jane-doe', route(pageOf(filler(1, 7))));
  out.short = short.result; out.shortCalls = short.calls.length;
  out.inlineInvitee = (await run('jane-doe', route(ok({ included: [
    { $type: TYPE + 'Invitation', entityUrn: 'urn:li:fs_relInvitation:INLINE', sentTime: SENT, toMember: { $type: 'com.linkedin.voyager.identity.shared.MiniProfile', entityUrn: 'urn:li:fs_miniProfile:M', publicIdentifier: 'jane-doe' } },
  ] })))).result;
  out.newest = (await run('jane-doe', route(pageOf([entries(1, 'jane-doe', 1759000000000), entries(2, 'jane-doe', SENT)])))).result;
  out.noTime = (await run('jane-doe', route(pageOf([entries(1, 'jane-doe', null)])))).result;
  out.encoded = (await run('Jos%C3%A9-Garc%C3%ADa', route(pageOf([entries(1, 'josé-garcía', SENT)])))).result;
  out.forbidden = (await run('jane-doe', () => bad(403))).result;
  out.laterPageFails = (await run('jane-doe', (url) => (url.includes('start=0') ? pageOf(filler(1, 100)) : bad(500)))).result;
  r = await run('jane-doe', route(pageOf(filler(1, 1))), '');
  out.signedOut = r.result; out.signedOutCalls = r.calls.length;
  r = await run('', route(pageOf(filler(1, 1))));
  out.emptyId = r.result; out.emptyIdCalls = r.calls.length;
  out.network = (await run('jane-doe', () => { throw new Error('net'); })).result;
  out.badJson = (await run('jane-doe', () => ({ ok: true, status: 200, json: async () => { throw new SyntaxError('x'); } }))).result;
  console.log(JSON.stringify(out));
})();
"""


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def call(tool_name: str, tool_input: object) -> tuple[bool, str]:
    return gate.decide({"tool_name": tool_name, "tool_input": tool_input})


def substituted(script: str, value: str) -> str:
    first, rest = script.split("\n", 1)
    return f"const {first.split(' ')[1]} = {value};\n{rest}"


def check_gate() -> None:
    check(SOURCE.split("\n", 1)[0] == 'const PUBLIC_IDENTIFIER = "";', "sent-invitations script's first line changed")
    check("validated: pending" in SOURCE, "the header does not say the endpoint is not validated")
    check(SCRIPT.name in gate.approved_scripts(), "the gate does not know the sent-invitations script")
    # Word for word, with only the first line's value changed, on either browser, alone or in a batch.
    check(call(TOOL, {"text": substituted(SOURCE, '"jane-doe_42"')})[0], "sent-invitations script with identifier refused")
    check(call(CHROME_TOOL, {"text": substituted(SOURCE, '"Jane-Doe%C3%A9"') + "\n"})[0], "script with encoded identifier or trailing newline refused")
    check(call("mcp__Claude_Browser__browser_batch", {"actions": [{"name": "javascript_tool", "input": {"action": "javascript_exec", "text": substituted(SOURCE, '"x"')}}]})[0],
          "sent-invitations script in a batch refused")
    # The placeholder is the thread script's own: an empty identifier is the template, not something a run may send.
    check(not call(TOOL, {"text": SOURCE})[0], "script with an empty identifier passed")
    check(not call(TOOL, {"text": substituted(SOURCE, "1")})[0], "script with a number on its first line passed")
    check(not call(TOOL, {"text": substituted(SOURCE, '"a\\" + document.cookie + \\""')})[0], "script with unsafe identifier passed")
    check(not call(TOOL, {"text": "const STOP_AT = 0;\n" + SOURCE.split("\n", 1)[1]})[0], "script under another placeholder passed")
    check(not call(TOOL, {"text": "\n".join(SOURCE.split("\n")[1:])})[0], "script without its first line passed")
    check(not call(TOOL, {"text": SOURCE.replace("MAX_PAGES = 5", "MAX_PAGES = 500")})[0], "edited sent-invitations script body passed")
    check(not call(TOOL, {"text": SOURCE.replace("invitationType=CONNECTION", "invitationType=ALL")})[0], "script with another query passed")
    check(not call(TOOL, {"text": SOURCE + "\nconsole.log(document.cookie)"})[0], "script with an appended line passed")
    # It returns only the record: never the token, and the only address it names is LinkedIn's sent-invitations list.
    returned = SOURCE.rstrip("\n").split("\n")[-1]
    check(returned == '({ ...payload, integrity: { algorithm: "fnv1a32", digest: fnv1a32(canonical(payload)) } })'
          and 'const payload = { status, signedIn: csrf !== "", capturedAt, state, publicIdentifier: PUBLIC_IDENTIFIER, invitation, pagesRead };' in SOURCE,
          "script's last line returns something other than the record sealed with its digest")
    check("csrf:" not in returned and "csrf," not in returned, "script returns the token")
    check(SOURCE.count("https://") == 1 and 'const ENDPOINT = "https://www.linkedin.com/voyager/api/relationships/sentInvitationViewsV2";' in SOURCE,
          "script names another address")
    for fragment in ("count=", "invitationType=CONNECTION", "q=invitationType", "start=", "x-restli-protocol-version", "normalized+json+2.1"):
        check(fragment in SOURCE, f"script does not use {fragment}")


def main() -> None:
    check_gate()
    node = shutil.which("node")
    if node is None:
        print("SKIP: node is not installed, so the sent-invitations script was not run against a fake LinkedIn (gate checks passed).")
        return
    done = subprocess.run([node, "-e", HARNESS, str(SCRIPT)], capture_output=True, text=True, check=False)
    check(done.returncode == 0, f"harness failed: {done.stderr[-400:]}")
    out = json.loads(done.stdout)

    found = out["found"]
    check(list(found) == ["status", "signedIn", "capturedAt", "state", "publicIdentifier", "invitation", "pagesRead", "integrity"], f"unexpected keys {list(found)}")
    check(found["integrity"]["algorithm"] == "fnv1a32" and len(found["integrity"]["digest"]) == 8, "the record is not sealed with an fnv1a32 digest")
    check(found["status"] == 200 and found["signedIn"] is True and found["state"] == "found", "found invitation not reported")
    check(found["publicIdentifier"] == "jane-doe" and found["pagesRead"] == 1, "identifier or pages read wrong")
    check(list(found["invitation"]) == ["sentTime", "inviteeUrn", "invitationUrn"], "invitation carries fields other than the three")
    check(found["invitation"] == {
        "sentTime": "2025-10-05T21:33:20.000Z", "inviteeUrn": "urn:li:fsd_profile:MEMBER50", "invitationUrn": "urn:li:fs_relInvitation:INV50",
    }, f"wrong invitation chosen or reduced: {found['invitation']}")
    check(found["capturedAt"].endswith("Z") and "T" in found["capturedAt"], "capturedAt is not an ISO time")
    check(out["leaked"] is False, "the CSRF token reached the result")
    check(out["secrets"] is False, "a name, note, picture or occupation reached the result")
    check(all(c == "include" for c in out["credentials"]), "a call did not use the page's own session")
    check(len(out["urls"]) == 1 and out["urls"][0] == "/relationships/sentInvitationViewsV2?count=100&invitationType=CONNECTION&q=invitationType&start=0",
          f"unexpected first call {out['urls']}")
    check(out["headers"][0]["x-restli-protocol-version"] == "2.0.0" and out["headers"][0]["accept"] == "application/vnd.linkedin.normalized+json+2.1"
          and out["headers"][0]["csrf-token"] == "ajax:SECRET-TOKEN", "request headers are not the documented ones")

    # Paging: start moves by 100, and reading stops as soon as the Lead is found.
    check(out["paging"]["state"] == "found" and out["paging"]["pagesRead"] == 3, "third page not read")
    check([u.rsplit("start=", 1)[1] for u in out["pagedUrls"]] == ["0", "100", "200"], "start did not move by 100")
    five = out["five"]
    check(five["state"] == "not-found" and five["status"] == 200 and five["invitation"] is None and five["pagesRead"] == 5 and out["fiveCalls"] == 5,
          "reading did not stop at five pages with not-found")
    check(out["short"]["state"] == "not-found" and out["short"]["pagesRead"] == 1 and out["shortCalls"] == 1, "a short list was read past its end")

    check(out["inlineInvitee"]["state"] == "found" and out["inlineInvitee"]["invitation"]["invitationUrn"] == "urn:li:fs_relInvitation:INLINE",
          "an inline invitee was not read")
    check(out["newest"]["invitation"]["sentTime"] == "2025-10-05T21:33:20.000Z", "the newest invitation was not chosen")
    check(out["noTime"]["state"] == "not-found", "an invitation with no send time counted as found")
    check(out["encoded"]["state"] == "found" and out["encoded"]["publicIdentifier"] == "Jos%C3%A9-Garc%C3%ADa", "an encoded identifier was not matched")

    for name, status in (("forbidden", 403), ("laterPageFails", 500), ("network", 0), ("badJson", 0)):
        record = out[name]
        check(record["status"] == status and record["state"] == "error" and record["invitation"] is None, f"{name}: error not reduced to status and no invitation")
    check(out["laterPageFails"]["pagesRead"] == 1, "pages read before the failure not reported")
    check(out["signedOut"]["signedIn"] is False and out["signedOut"]["state"] == "error" and out["signedOut"]["status"] == 0 and out["signedOutCalls"] == 0,
          "signed-out script still called LinkedIn")
    check(out["emptyId"]["state"] == "error" and out["emptyId"]["publicIdentifier"] == "" and out["emptyIdCalls"] == 0, "empty identifier still called LinkedIn")
    print("PASS: the sent-invitations script is gated word for word, returns only the Lead's own invitation, never the token, and never throws.")


if __name__ == "__main__":
    main()
