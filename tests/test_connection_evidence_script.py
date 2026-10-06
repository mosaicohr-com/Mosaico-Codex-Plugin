#!/usr/bin/env python3
"""The approved connection-evidence script resolves a vanity, a redirected vanity or an opaque member id, and reports why it failed.

It is run under node against a fake page and a fake LinkedIn: no network, no real cookie. The check is skipped
(and says so) when node is not installed.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins" / "mosaico-claude" / "browser" / "linkedin-connection-evidence.js"

HARNESS = r"""
const fs = require('fs');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const SRC = fs.readFileSync(process.argv[1], 'utf8');
const TOKEN = 'ajax:SECRET-TOKEN';
async function run(id, routes, cookie = 'JSESSIONID="' + TOKEN + '"') {
  const calls = [];
  const body = SRC.replace('const PUBLIC_IDENTIFIER = "PUBLIC_IDENTIFIER";', 'const PUBLIC_IDENTIFIER = ' + JSON.stringify(id) + ';');
  const wrapped = new AsyncFunction('document', 'fetch', 'return await (async () => {' + body.replace(/\n\(\{/, '\nreturn ({') + '})();');
  const result = await wrapped({ cookie }, async (url, init) => { calls.push({ url, init }); return routes(url, init); });
  return { result, calls };
}
const ok = (j) => ({ ok: true, status: 200, json: async () => j });
const bad = (s) => ({ ok: false, status: s, json: async () => ({}) });
const P = 'com.linkedin.voyager.dash.identity.profile.Profile';
const REL = 'com.linkedin.voyager.dash.relationships.MemberRelationship';
const relationship = { $type: REL, entityUrn: 'urn:li:fsd_memberRelationship:X', memberRelationship: { noConnection: { memberDistance: 'DISTANCE_2', invitation: { noInvitation: {} } } }, extra: 'dropped' };
const profile = (identifier, id, extra = {}) => ({ $type: P, publicIdentifier: identifier, entityUrn: 'urn:li:fsd_profile:' + id, firstName: 'Secret', headline: 'Boss', ...extra });
const answer = (...profiles) => () => ok({ included: [relationship, ...profiles] });
(async () => {
  const out = {};
  let r = await run('jane-doe', answer(profile('jane-doe', 'LEADID01')));
  out.exact = r.result; out.exactUrls = r.calls.map((c) => c.url.replace('https://www.linkedin.com/voyager/api', ''));
  out.credentials = r.calls.map((c) => c.init.credentials);
  out.leaked = ['Secret', 'Boss', 'dropped', TOKEN].some((s) => JSON.stringify(r.result).includes(s));
  out.exactCase = (await run('jane-doe', answer(profile('Jane-Doe', 'LEADID01')))).result;
  out.exactAmongMany = (await run('jane-doe', answer(profile('other', 'OTHER01'), profile('Jane-Doe', 'LEADID01')))).result;
  // A redirected vanity: LinkedIn answers the old vanity with the one Profile of the new one.
  out.redirect = (await run('zoe-milligan-conscious-learning-architecture', answer(profile('zoemilliganignitespark', 'ACoAAZOE')))).result;
  out.twoProfiles = (await run('old-vanity', answer(profile('a', 'A1'), profile('b', 'B1')))).result;
  out.noProfile = (await run('old-vanity', answer())).result;
  out.noUrn = (await run('old-vanity', answer(profile('a', 'x', { entityUrn: 'urn:li:fsd_company:1' })))).result;
  // An opaque member id is sent as the vanityName and the Profile is accepted only when its member id is the requested one.
  r = await run('ACoAAB1x_y-Z', answer(profile('the-new-vanity', 'ACoAAB1x_y-Z')));
  out.opaque = r.result; out.opaqueUrls = r.calls.map((c) => c.url);
  out.opaqueNoVanity = (await run('ACoAAB1x_y-Z', answer({ $type: P, entityUrn: 'urn:li:fsd_profile:ACoAAB1x_y-Z' }))).result;
  out.opaqueWrongMember = (await run('ACoAAB1x_y-Z', answer(profile('someone-else', 'ACoAAOTHER')))).result;
  out.opaqueTwo = (await run('ACoAAB1x_y-Z', answer(profile('someone-else', 'ACoAAOTHER'), profile('the-new-vanity', 'ACoAAB1x_y-Z')))).result;
  // Errors never throw.
  out.forbidden = (await run('jane-doe', () => bad(403))).result;
  out.network = (await run('jane-doe', () => { throw new Error('net'); })).result;
  out.badJson = (await run('jane-doe', () => ({ ok: true, status: 200, json: async () => { throw new SyntaxError('x'); } }))).result;
  out.signedOut = (await run('jane-doe', () => bad(401), '')).result;
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


def null_free(value):
    """Canonical JSON with object keys whose value is None omitted at every depth (array items stay)."""
    if isinstance(value, dict):
        return {k: null_free(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [null_free(v) for v in value]
    return value


def digest_of(record: dict) -> str:
    body = {k: v for k, v in record.items() if k != "integrity"}
    return fnv1a32(json.dumps(null_free(body), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


KEYS = ["status", "signedIn", "capturedAt", "state", "errorStep", "profileIdentifier", "requestedIdentifier", "resolvedIdentifier", "memberUrn", "entries", "integrity"]


def main() -> None:
    node = shutil.which("node")
    if node is None:
        print("SKIP: node is not installed, so the connection-evidence script was not run against a fake LinkedIn.")
        return
    done = subprocess.run([node, "-e", HARNESS, str(SCRIPT)], capture_output=True, text=True, encoding="utf-8", check=False)
    check(done.returncode == 0, f"harness failed: {done.stderr[-400:]}")
    out = json.loads(done.stdout)

    exact = out["exact"]
    check(list(exact) == KEYS, f"unexpected keys {list(exact)}")
    check(exact["state"] == "ok" and exact["errorStep"] is None and exact["status"] == 200 and exact["signedIn"] is True, "exact vanity not ok")
    check(exact["profileIdentifier"] == "jane-doe" and exact["requestedIdentifier"] == "jane-doe" and exact["resolvedIdentifier"] == "jane-doe"
          and exact["memberUrn"] == "urn:li:fsd_profile:LEADID01", "identifier fields wrong for an exact vanity")
    check(len(exact["entries"]) == 2 and exact["entries"][1] == {"$type": "com.linkedin.voyager.dash.identity.profile.Profile", "publicIdentifier": "jane-doe", "entityUrn": "urn:li:fsd_profile:LEADID01"},
          f"entries are not the relationship and the reduced profile: {exact['entries']}")
    check(len(out["exactUrls"]) == 1 and "variables=(vanityName:jane-doe)&queryId=voyagerIdentityDashProfiles.34ead06db82a2cc9a778fac97f69ad6a" in out["exactUrls"][0], "profile call is not the documented query")
    check(all(c == "include" for c in out["credentials"]) and out["leaked"] is False, "token or a dropped field reached the result")
    check(out["exactCase"]["state"] == "ok" and out["exactCase"]["resolvedIdentifier"] == "Jane-Doe" and out["exactCase"]["requestedIdentifier"] == "jane-doe", "a vanity differing only in case was not matched")
    check(out["exactAmongMany"]["state"] == "ok" and out["exactAmongMany"]["memberUrn"] == "urn:li:fsd_profile:LEADID01", "the exact vanity among several Profiles was not used")

    redirect = out["redirect"]
    check(redirect["state"] == "ok" and redirect["requestedIdentifier"] == "zoe-milligan-conscious-learning-architecture" and redirect["profileIdentifier"] == redirect["requestedIdentifier"]
          and redirect["resolvedIdentifier"] == "zoemilliganignitespark" and redirect["memberUrn"] == "urn:li:fsd_profile:ACoAAZOE"
          and redirect["entries"][1]["publicIdentifier"] == "zoemilliganignitespark", f"a redirected vanity was not accepted: {redirect}")
    for name in ("twoProfiles", "noProfile", "noUrn"):
        record = out[name]
        check(record["state"] == "error" and record["errorStep"] == "profile" and record["status"] == 200 and record["entries"] == []
              and record["resolvedIdentifier"] is None and record["memberUrn"] is None and record["requestedIdentifier"] == "old-vanity", f"{name}: not an error at the profile step: {record}")

    opaque = out["opaque"]
    check(opaque["state"] == "ok" and opaque["requestedIdentifier"] == "ACoAAB1x_y-Z" and opaque["resolvedIdentifier"] == "ACoAAB1x_y-Z"
          and opaque["memberUrn"] == "urn:li:fsd_profile:ACoAAB1x_y-Z" and len(opaque["entries"]) == 2, f"opaque id not resolved: {opaque}")
    check("variables=(vanityName:ACoAAB1x_y-Z)" in out["opaqueUrls"][0], "an opaque id was not sent as the vanityName")
    check(out["opaqueNoVanity"]["state"] == "ok" and out["opaqueNoVanity"]["entries"][1] == {"$type": "com.linkedin.voyager.dash.identity.profile.Profile", "entityUrn": "urn:li:fsd_profile:ACoAAB1x_y-Z"},
          "an opaque id's Profile without a vanity was not accepted")
    check(out["opaqueTwo"]["state"] == "ok" and out["opaqueTwo"]["entries"][1]["publicIdentifier"] == "the-new-vanity", "the Profile of the requested member id was not chosen among several")
    wrong = out["opaqueWrongMember"]
    check(wrong["state"] == "error" and wrong["errorStep"] == "profile" and wrong["entries"] == [] and wrong["memberUrn"] is None, "another member's Profile was accepted for an opaque id")

    for name, status in (("forbidden", 403), ("network", 0), ("badJson", 0), ("signedOut", 401)):
        record = out[name]
        check(record["state"] == "error" and record["errorStep"] == "profile" and record["status"] == status and record["entries"] == [], f"{name}: error not reported with status {status}: {record}")
    check(out["signedOut"]["signedIn"] is False, "signed-out script reported signed in")
    for name, record in out.items():
        if isinstance(record, dict) and "integrity" in record:
            check(list(record)[-1] == "integrity" and record["integrity"] == {"algorithm": "fnv1a32", "digest": digest_of(record)}, f"{name}: not sealed correctly")
    check(digest_of({**out["redirect"], "memberUrn": "urn:li:fsd_profile:OTHER"}) != out["redirect"]["integrity"]["digest"], "the new fields are not inside the digest")
    print("PASS: the connection-evidence script resolves a vanity, a redirected vanity or an opaque member id, reports errorStep, and never throws.")


if __name__ == "__main__":
    main()
