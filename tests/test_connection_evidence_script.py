#!/usr/bin/env python3
"""The approved connection-evidence script resolves a vanity, a redirected vanity or an opaque member id, and reports why it failed.

Since 0.9.16 it also retries the profile query once with the page's own slug when the first call failed (404, 410 or a 2xx with no
usable Profile) and the page the run opened has followed a redirect to a different /in/<slug>/. It never retries on a refusal, a rate
limit, a server error, a dropped call, when the slug is the one asked for, or when the page is not a profile page.

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
async function run(id, routes, cookie = 'JSESSIONID="' + TOKEN + '"', pathname = null) {
  const calls = [];
  const body = SRC.replace('const PUBLIC_IDENTIFIER = "PUBLIC_IDENTIFIER";', 'const PUBLIC_IDENTIFIER = ' + JSON.stringify(id) + ';');
  const wrapped = new AsyncFunction('document', 'fetch', 'location', 'return await (async () => {' + body.replace(/\n\(\{/, '\nreturn ({') + '})();');
  const result = await wrapped({ cookie }, async (url, init) => { calls.push({ url, init }); return routes(url, init); }, pathname === null ? undefined : { pathname });
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

  // 0.9.16: the redirect retry. The route answers by the vanityName the call asks for.
  const byName = (table) => (url) => { const name = decodeURIComponent(/vanityName:([^)]*)\)/.exec(url)[1]); const entry = table[name]; return entry === undefined ? bad(404) : entry; };
  const names = (calls) => calls.map((c) => decodeURIComponent(/vanityName:([^)]*)\)/.exec(c.url)[1]));
  const NEW = ok({ included: [relationship, profile('the-new-vanity', 'ACoAAZOE')] });
  r = await run('old-vanity', byName({ 'the-new-vanity': NEW }), undefined, '/in/the-new-vanity/');
  out.retry = r.result; out.retryCalls = names(r.calls); out.retryLeaked = JSON.stringify(r.result).includes(TOKEN);
  r = await run('old-vanity', byName({ 'old-vanity': ok({ included: [relationship] }), 'the-new-vanity': NEW }), undefined, '/in/the-new-vanity/');
  out.retryAfterEmpty = r.result; out.retryAfterEmptyCalls = names(r.calls);
  r = await run('old-vanity', byName({ 'old-vanity': bad(410), 'The-New-Vanity': NEW }), undefined, '/in/The-New-Vanity/details/contact-info/');
  out.retryAfter410 = r.result; out.retryAfter410Calls = names(r.calls);
  // No redirect (same slug, or only a different case), no profile page, an unsafe slug, no page location at all: one call, no retry.
  const only404 = byName({ 'the-new-vanity': NEW });
  for (const [name, pathname] of [['sameSlug', '/in/old-vanity/'], ['sameSlugCase', '/in/Old-Vanity'], ['notProfilePage', '/messaging/thread/2-abc/'], ['unsafeSlug', '/in/a)(b/'],
    ['emptySlug', '/in/'], ['noLocation', null]]) {
    r = await run('old-vanity', only404, undefined, pathname);
    out['noRetry_' + name] = r.result; out['noRetryCalls_' + name] = names(r.calls);
  }
  // A refusal, a rate limit, a server error, a dropped call or a signed-out page says nothing about the slug: no retry.
  for (const [name, route] of [['403', () => bad(403)], ['429', () => bad(429)], ['500', () => bad(500)], ['dropped', () => { throw new Error('net'); }]]) {
    r = await run('old-vanity', route, undefined, '/in/the-new-vanity/');
    out['noRetry_' + name] = r.result; out['noRetryCalls_' + name] = r.calls.length;
  }
  // A call that worked is never retried, whatever the page says.
  r = await run('jane-doe', answer(profile('jane-doe', 'LEADID01')), undefined, '/in/someone-else/');
  out.workedNoRetry = r.result; out.workedNoRetryCalls = r.calls.length;
  // The retry runs once and its failure is reported, with its own status; a dropped retry keeps the first status.
  r = await run('old-vanity', () => bad(404), undefined, '/in/the-new-vanity/');
  out.retryFails = r.result; out.retryFailsCalls = r.calls.length;
  r = await run('old-vanity', ((n) => () => { n += 1; return n === 1 ? bad(404) : ok({ included: [relationship] }); })(0), undefined, '/in/the-new-vanity/');
  out.retryEmpty = r.result; out.retryEmptyCalls = r.calls.length;
  r = await run('old-vanity', ((n) => () => { n += 1; if (n === 1) return bad(404); throw new Error('net'); })(0), undefined, '/in/the-new-vanity/');
  out.retryDropped = r.result; out.retryDroppedCalls = r.calls.length;
  // A retry whose Profile is not the requested vanity's person is still the page's person (the redirect); two Profiles with no exact name are not.
  r = await run('old-vanity', byName({ 'the-new-vanity': ok({ included: [relationship, profile('a', 'A1'), profile('b', 'B1')] }) }), undefined, '/in/the-new-vanity/');
  out.retryAmbiguous = r.result;
  // An opaque member id: the page's slug is accepted only when its Profile carries that very member id.
  r = await run('ACoAAB1x_y-Z', byName({ 'the-new-vanity': ok({ included: [relationship, profile('the-new-vanity', 'ACoAAB1x_y-Z')] }) }), undefined, '/in/the-new-vanity/');
  out.retryOpaque = r.result; out.retryOpaqueCalls = names(r.calls);
  r = await run('ACoAAB1x_y-Z', byName({ 'the-new-vanity': ok({ included: [relationship, profile('the-new-vanity', 'ACoAAOTHER')] }) }), undefined, '/in/the-new-vanity/');
  out.retryOpaqueOther = r.result; out.retryOpaqueOtherCalls = r.calls.length;
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

    # 0.9.16: the redirect retry.
    retry = out["retry"]
    check(out["retryCalls"] == ["old-vanity", "the-new-vanity"], f"the retry did not ask first for the requested identifier, then once for the page's slug: {out['retryCalls']}")
    check(retry["state"] == "ok" and retry["errorStep"] is None and retry["status"] == 200 and retry["requestedIdentifier"] == "old-vanity" and retry["profileIdentifier"] == "old-vanity"
          and retry["resolvedIdentifier"] == "the-new-vanity" and retry["memberUrn"] == "urn:li:fsd_profile:ACoAAZOE" and len(retry["entries"]) == 2
          and retry["entries"][1]["publicIdentifier"] == "the-new-vanity", f"a redirect retry did not report the requested and the resolved identifier: {retry}")
    check(out["retryLeaked"] is False, "the token reached a retry result")
    check(out["retryAfterEmptyCalls"] == ["old-vanity", "the-new-vanity"] and out["retryAfterEmpty"]["state"] == "ok" and out["retryAfterEmpty"]["resolvedIdentifier"] == "the-new-vanity"
          and out["retryAfterEmpty"]["requestedIdentifier"] == "old-vanity", "a 200 with no Profile was not retried with the page's slug")
    check(out["retryAfter410Calls"] == ["old-vanity", "The-New-Vanity"] and out["retryAfter410"]["state"] == "ok", f"a 410 was not retried with the page's own slug (as the page shows it): {out['retryAfter410Calls']}")
    for name in ("sameSlug", "sameSlugCase", "notProfilePage", "unsafeSlug", "emptySlug", "noLocation"):
        record = out["noRetry_" + name]
        check(out["noRetryCalls_" + name] == ["old-vanity"] and record["state"] == "error" and record["status"] == 404 and record["resolvedIdentifier"] is None and record["requestedIdentifier"] == "old-vanity",
              f"noRetry_{name}: retried or answered wrongly: {out['noRetryCalls_' + name]} {record}")
    for name, status in (("403", 403), ("429", 429), ("500", 500), ("dropped", 0)):
        check(out["noRetryCalls_" + name] == 1 and out["noRetry_" + name]["status"] == status and out["noRetry_" + name]["state"] == "error", f"a {name} answer was retried")
    check(out["workedNoRetryCalls"] == 1 and out["workedNoRetry"]["resolvedIdentifier"] == "jane-doe", "a call that worked was retried because the page shows another slug")
    check(out["retryFailsCalls"] == 2 and out["retryFails"]["state"] == "error" and out["retryFails"]["status"] == 404 and out["retryFails"]["requestedIdentifier"] == "old-vanity"
          and out["retryFails"]["resolvedIdentifier"] is None and out["retryFails"]["entries"] == [], "a failed retry was repeated or not reported as an error")
    check(out["retryEmptyCalls"] == 2 and out["retryEmpty"]["state"] == "error" and out["retryEmpty"]["status"] == 200 and out["retryEmpty"]["entries"] == [],
          "a retry that answered 200 with no Profile did not report its own status")
    check(out["retryDroppedCalls"] == 2 and out["retryDropped"]["state"] == "error" and out["retryDropped"]["status"] == 404, "a dropped retry did not keep the first call's status")
    check(out["retryAmbiguous"]["state"] == "error" and out["retryAmbiguous"]["status"] == 200, "a retry that answered several unrelated Profiles was accepted")
    check(out["retryOpaque"]["state"] == "ok" and out["retryOpaqueCalls"] == ["ACoAAB1x_y-Z", "the-new-vanity"] and out["retryOpaque"]["requestedIdentifier"] == "ACoAAB1x_y-Z"
          and out["retryOpaque"]["resolvedIdentifier"] == "the-new-vanity" and out["retryOpaque"]["memberUrn"] == "urn:li:fsd_profile:ACoAAB1x_y-Z", f"an opaque id was not resolved through the page's slug: {out['retryOpaque']}")
    check(out["retryOpaqueOtherCalls"] == 2 and out["retryOpaqueOther"]["state"] == "error" and out["retryOpaqueOther"]["memberUrn"] is None and out["retryOpaqueOther"]["entries"] == [],
          "another member's Profile was accepted through the page's slug for an opaque id")

    for name, status in (("forbidden", 403), ("network", 0), ("badJson", 0), ("signedOut", 401)):
        record = out[name]
        check(record["state"] == "error" and record["errorStep"] == "profile" and record["status"] == status and record["entries"] == [], f"{name}: error not reported with status {status}: {record}")
    check(out["signedOut"]["signedIn"] is False, "signed-out script reported signed in")
    for name, record in out.items():
        if isinstance(record, dict) and "integrity" in record:
            check(list(record)[-1] == "integrity" and record["integrity"] == {"algorithm": "fnv1a32", "digest": digest_of(record)}, f"{name}: not sealed correctly")
    check(digest_of({**out["redirect"], "memberUrn": "urn:li:fsd_profile:OTHER"}) != out["redirect"]["integrity"]["digest"], "the new fields are not inside the digest")
    print("PASS: the connection-evidence script resolves a vanity, a redirected vanity or an opaque member id, retries once with the page's own slug after a redirect, reports errorStep, and never throws.")


if __name__ == "__main__":
    main()
