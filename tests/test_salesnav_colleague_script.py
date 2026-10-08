#!/usr/bin/env python3
"""The approved Sales Navigator colleague-connection script answers one question and leaks nothing else.

Static checks on the script text (placeholders, endpoints, the seal, the state and found rules) always run. The behaviour is run under node
against a fake page and a fake LinkedIn: no network, no real cookie, no real person. The check is skipped (and says so) when node is not
installed. The fake answers in the shapes the 2026-10-07 capture notes record; the parts the captures could not show (the keywords field,
the decorationId, the result row) are stated in the script header and are only as true as that.

Profile lookups (0.9.5): the live test of 0.9.4 ended at the first call with "colleague-not-resolved" because the script asked LinkedIn's profile
query with a plain JSON accept header, and LinkedIn then answers without the `included` list the profile is read from. The fake LinkedIn here
answers a profile query with `included` only when the request carries the normalized-JSON accept header the proven connection-evidence script
sends (and with an answer that has no `included` list otherwise), and the profile requests made for a vanity and for an opaque id are compared,
parameter for parameter, with the ones linkedin-connection-evidence.js makes for the same identifier. The answer shapes are the ones that script's
own tests use; no real LinkedIn answer is recorded in this repository.

Member ids: LinkedIn's opaque ids are 29 bytes, 4 prefix bytes (00 2A 00 00 for ACoAA..., 00 2C 00 00 for Sales Navigator's ACw...), the
numeric member id as 4 big-endian bytes, then 21 more. The fake builds them the same way, so the script decodes them as it would real ones.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "mosaico-claude"
SCRIPT = PLUGIN / "browser" / "linkedin-salesnav-colleague-connection.js"
EVIDENCE = PLUGIN / "browser" / "linkedin-connection-evidence.js"

spec = importlib.util.spec_from_file_location("gate", PLUGIN / "hooks" / "browser-script-gate.py")
gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gate)

SOURCE = SCRIPT.read_text(encoding="utf-8")
TOOL = "mcp__Claude_Browser__javascript_tool"
NORMALIZED_ACCEPT = "application/vnd.linkedin.normalized+json+2.1"

HARNESS = r"""
const fs = require('fs');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const SRC = fs.readFileSync(process.argv[1], 'utf8');
const EVIDENCE_SRC = fs.readFileSync(process.argv[2], 'utf8');
const NORMALIZED_ACCEPT = 'application/vnd.linkedin.normalized+json+2.1';
const TOKEN = 'ajax:SECRET-TOKEN';

// Opaque ids as LinkedIn builds them: 00 <kind> 00 00, the member id as 4 big-endian bytes, 21 more bytes.
const opaque = (kind, member, seed = 1) => {
  const b = Buffer.alloc(29);
  b[1] = kind === 'sales' ? 0x2c : 0x2a;
  b.writeUInt32BE(member, 4);
  for (let i = 8; i < 29; i++) b[i] = (seed * 31 + i * 7) & 255;
  return b.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
};
const fsd = (m) => opaque('fsd', m);
const sales = (m) => opaque('sales', m);

const PEOPLE = {
  colleague: { vanity: 'ewa-colleague', first: 'Ewa', last: 'Colleague', member: 300001 },
  candidate: { vanity: 'jane-doe', first: 'Jane', last: 'Doe', member: 553472255 },
  namesake: { vanity: 'jane-doe-2', first: 'Jane', last: 'Doe', member: 400002 },
  strange: { vanity: 'zoe-obrien', first: "Zoë (Z.)", last: "O'Brien*", member: 500005 },
};
const byVanity = (v) => Object.values(PEOPLE).find((p) => p.vanity.toLowerCase() === v.toLowerCase());
// The Profile entity as the evidence script's tests fixture it (the shape linkedin-connection-evidence.js reads), with the names the thread script reads from the same query.
const profileAnswer = (p, vanity = p.vanity) => ({ included: [{ $type: 'com.linkedin.voyager.dash.identity.profile.Profile', publicIdentifier: vanity, entityUrn: 'urn:li:fsd_profile:' + fsd(p.member), firstName: p.first, lastName: p.last, headline: 'Secret headline' }] });

const ok = (j) => ({ ok: true, status: 200, json: async () => j });
const bad = (s) => ({ ok: false, status: s, json: async () => ({}) });

// A row as Sales Navigator's lead search returns it (the shape the profile call shows): entityUrn with the ACw id, objectUrn with the member id.
const row = (p, extra = {}) => ({ entityUrn: 'urn:li:fs_salesProfile:(' + sales(p.member) + ',NAME_SEARCH,abcd)', objectUrn: 'urn:li:member:' + p.member, fullName: p.first + ' ' + p.last, headline: 'Secret headline', currentPositions: [{ companyName: 'Secret Co' }], ...extra });
const fullName = (p) => p.first + ' ' + p.last;

// The fake LinkedIn. `world.connected`: member ids connected to the colleague. `world.hidden`: the colleague's connections are not listed.
const route = (world = {}) => (url, init) => {
  const calls = world.calls;
  if (url.includes('voyagerIdentityDashProfiles')) {
    const v = decodeURIComponent(/vanityName:([^)]*)\)/.exec(url)[1]);
    if (world.profileStatus) return bad(world.profileStatus);
    // Without the normalized-JSON accept header LinkedIn answers with a document that has no `included` list (what 0.9.4 got).
    if (!init || !init.headers || init.headers.accept !== NORMALIZED_ACCEPT) return ok({ data: { data: { identityDashProfilesByMemberIdentity: { '*elements': [] } } } });
    if (world.redirects && world.redirects[v]) return ok(profileAnswer(world.redirects[v].person, world.redirects[v].vanity));
    const p = byVanity(v) || (v.startsWith('ACoAA') ? Object.values(PEOPLE).find((q) => fsd(q.member) === v) : undefined);
    if (world.noProfile && world.noProfile.includes(v)) return ok({ included: [] });
    return ok(p ? profileAnswer(p) : { included: [] });
  }
  if (url.includes('/sales-api/salesApiFacetTypeahead')) {
    if (world.typeaheadStatus) return bad(world.typeaheadStatus);
    const q = decodeURIComponent(/query=([^&]*)/.exec(url)[1]);
    const near = [{ displayValue: 'Eva Colleague', id: sales(300002) }, { displayValue: 'Eve Colleague', id: sales(300003) }];
    const her = world.noColleagueEntry ? [] : [{ displayValue: 'Ewa Colleague', id: sales(300001), headline: 'Secret headline', displayImage: { rootUrl: 'x' } }];
    return ok({ elements: world.herFirst ? [...her, ...near] : [...near, ...her], paging: { count: 10, start: 0, links: [] }, q });
  }
  if (url.includes('/sales-api/salesApiLeadSearch')) {
    if (world.searchStatus) return bad(world.searchStatus);
    const raw = /query=(.*)&start=/.exec(url)[1];
    const start = Number(/start=(\d+)/.exec(url)[1]);
    const keywordMatch = /keywords:([^)]*?)\)$/.exec(raw);
    const keywords = keywordMatch === null ? null : decodeURIComponent(keywordMatch[1].replace(/%2[89]/g, (m) => m)); // restli-encoded text
    const filtered = raw.includes('type:CONNECTION_OF');
    const filterId = filtered ? /id:([A-Za-z0-9_-]+),text:/.exec(raw)[1] : null;
    const size = Number(/count=(\d+)/.exec(url)[1]);
    if (keywords === null) {
      // The control search (0.9.11): the filter alone, count 1. The answer carries paging.total: how many of her connections the account can see.
      if (world.controlStatus) return bad(world.controlStatus);
      if (world.controlNetwork) return new Error('net');
      if (world.controlBadBody) return ok([1, 2]);
      const total = world.hidden ? 0 : (world.controlTotal === undefined ? 1432 : world.controlTotal);
      const shown = Array.from({ length: Math.min(size, total) }, (_, i) => row({ member: 800000 + i }));
      const cmeta = { totalDisplayCount: total >= 1000 ? '1K+' : String(total), ...(world.controlNoEcho ? {} : { filters: [{ type: 'CONNECTION_OF', values: [{ id: filterId, selectionType: 'INCLUDED' }] }] }) };
      return ok({ metadata: cmeta, elements: shown, paging: world.controlNoPaging ? { count: size, start: 0, links: [] } : { total, count: size, start, links: [] } });
    }
    let people = Object.values(PEOPLE).filter((p) => fullName(p) === keywords);
    if (world.extraNamesakes) people = [...Array.from({ length: world.extraNamesakes }, (_, i) => ({ vanity: 'x' + i, first: 'Jane', last: 'Doe', member: 700000 + i })), ...people];
    if (world.candidateFirst) people = [...people.filter((p) => p.member === PEOPLE.candidate.member), ...people.filter((p) => p.member !== PEOPLE.candidate.member)];
    if (filtered) people = world.hidden ? [] : people.filter((p) => (world.connected || []).includes(p.member) || (world.connectedFiller && p.member >= 700000 && p.member < 700000 + world.connectedFiller));
    if (world.noCandidateUnfiltered && !filtered) people = people.filter((p) => p.member !== PEOPLE.candidate.member);
    const page = people.slice(start, start + 25);
    const nothing = () => ({ entityUrn: 'urn:li:fs_salesProfile:(nothing)' });
    const elements = world.unreadable ? page.map(nothing) : page.map((p, i) => (filtered && i < (world.unreadableCount || 0) ? nothing() : row(p, world.mismatchObject ? { objectUrn: 'urn:li:member:1' } : {})));
    const meta = { totalDisplayCount: people.length >= 2000 ? '2K+' : String(people.length), keywords, ...(filtered && !world.noEcho ? { filters: [{ type: 'CONNECTION_OF', values: [{ id: filterId, selectionType: 'INCLUDED' }] }] } : {}) };
    if (world.badSearchBody) return ok([1, 2]);
    return ok({ metadata: meta, elements, paging: world.noPagingTotal ? { count: 25, start, links: [] } : { total: people.length, count: 25, start, links: [] } });
  }
  return bad(404);
};

async function run(candidate, colleague, world = {}, cookie = 'JSESSIONID="' + TOKEN + '"') {
  const calls = [];
  const delays = [];
  world.calls = calls;
  const body = SRC.replace('const PUBLIC_IDENTIFIER = "";', 'const PUBLIC_IDENTIFIER = ' + JSON.stringify(candidate) + ';').replace('const COLLEAGUE_IDENTIFIER = "";', 'const COLLEAGUE_IDENTIFIER = ' + JSON.stringify(colleague) + ';');
  const wrapped = new AsyncFunction('document', 'fetch', 'setTimeout', 'return await (async () => {' + body.replace(/\n\(\{/, '\nreturn ({') + '})();');
  const router = world.router || route(world);
  const result = await wrapped({ cookie }, async (url, init) => { calls.push({ url, init }); const r = router(url, init); if (r instanceof Error) throw r; return r; }, (fn, ms) => { delays.push(ms); fn(); });
  return { result, calls, delays };
}
// The proven connection-evidence script, run for one identifier against the same fake LinkedIn: the request it makes is the reference.
async function evidence(id, world = {}) {
  const calls = [];
  world.calls = calls;
  const router = route(world);
  const body = EVIDENCE_SRC.replace('const PUBLIC_IDENTIFIER = "PUBLIC_IDENTIFIER";', 'const PUBLIC_IDENTIFIER = ' + JSON.stringify(id) + ';');
  const wrapped = new AsyncFunction('document', 'fetch', 'return await (async () => {' + body.replace(/\n\(\{/, '\nreturn ({') + '})();');
  const result = await wrapped({ cookie: 'JSESSIONID="' + TOKEN + '"' }, async (url, init) => { calls.push({ url, init }); return router(url, init); });
  return { result, calls };
}
const urls = (r) => r.calls.map((c) => c.url.replace('https://www.linkedin.com', ''));
const shortUrls = (r) => urls(r).map((u) => u.replace(/\?.*/, ''));

(async () => {
  const out = { ids: { colleagueSales: sales(300001), candidateSales: sales(553472255), namesakeSales: sales(400002), candidateFsd: fsd(553472255) } };
  const C = PEOPLE.colleague, J = PEOPLE.candidate, N = PEOPLE.namesake;

  // Found: the candidate is among the colleague's connections.
  let r = await run('jane-doe', 'ewa-colleague', { connected: [J.member] });
  out.found = r.result; out.foundUrls = urls(r); out.foundShort = shortUrls(r); out.foundHeaders = r.calls.map((c) => c.init.headers); out.foundCreds = r.calls.map((c) => c.init.credentials); out.foundDelays = r.delays;
  out.leaked = JSON.stringify(r.result).includes(TOKEN);
  out.secrets = ['Secret', 'Jane', 'Doe', 'Ewa', 'Colleague', 'headline', 'rootUrl'].some((s) => JSON.stringify(r.result).includes(s));
  // Not found: the candidate exists and the colleague's list does not hold them. Their own id is read from the unfiltered results.
  r = await run('jane-doe', 'ewa-colleague', { connected: [] });
  out.notFound = r.result; out.notFoundShort = shortUrls(r); out.notFoundUrls = urls(r);
  // A namesake is never taken for the candidate: only the namesake is connected, and the candidate is chosen by member id in the unfiltered list.
  r = await run('jane-doe', 'ewa-colleague', { connected: [N.member] });
  out.namesakeConnected = r.result;
  // The namesake comes first in the unfiltered list too (both people have the same name): the candidate's id is still the one returned.
  out.namesakeId = (await run('jane-doe', 'ewa-colleague', { connected: [] })).result.candidate.salesNavId;
  out.namesakeOnly = (await run('jane-doe-2', 'ewa-colleague', { connected: [N.member] })).result;
  // The colleague's typeahead entry is chosen by member id, not by order or by name; her entry first or last both work.
  out.herFirst = (await run('jane-doe', 'ewa-colleague', { connected: [J.member], herFirst: true })).result;
  out.noColleagueEntry = (await run('jane-doe', 'ewa-colleague', { noColleagueEntry: true })); out.noColleagueEntryCalls = out.noColleagueEntry.calls.length; out.noColleagueEntry = out.noColleagueEntry.result;
  // Colleague profile unknown to LinkedIn.
  r = await run('jane-doe', 'nobody-here', {}); out.colleagueUnknown = r.result; out.colleagueUnknownCalls = r.calls.length;
  // Candidate profile unknown: nothing is searched.
  r = await run('nobody-here', 'ewa-colleague', {}); out.candidateUnknown = r.result; out.candidateUnknownShort = shortUrls(r);
  // The candidate is the colleague herself: nothing is searched.
  r = await run('ewa-colleague', 'ewa-colleague', {}); out.sameAsColleague = r.result; out.sameShort = shortUrls(r);
  // The candidate cannot be found in the unfiltered results either.
  r = await run('jane-doe', 'ewa-colleague', { connected: [], noCandidateUnfiltered: true }); out.notInPlain = r.result; out.notInPlainShort = shortUrls(r);
  // A colleague who hides her connections: the filtered search lists nobody, and that is not found.
  out.hidden = (await run('jane-doe', 'ewa-colleague', { hidden: true })).result;
  // Paging: at most 2 filtered pages (25 a page), then the candidate's own id from the unfiltered list.
  const filler = { extraNamesakes: 60, connectedFiller: 60, connected: [] };
  r = await run('jane-doe', 'ewa-colleague', { ...filler, candidateFirst: true }); out.twoPages = r.result; out.twoPagesUrls = urls(r);
  // Only the first unfiltered page is read: a candidate lost among more than 25 namesakes is not resolved (and is never guessed).
  out.lostInNamesakes = (await run('jane-doe', 'ewa-colleague', { ...filler })).result;
  r = await run('jane-doe', 'ewa-colleague', { extraNamesakes: 20, connectedFiller: 20, connected: [J.member] }); out.onePageFound = r.result; out.onePageFoundCalls = r.calls.length;
  r = await run('jane-doe', 'ewa-colleague', { extraNamesakes: 30, connectedFiller: 30, connected: [J.member] }); out.secondPageFound = r.result; out.secondPageUrls = urls(r);
  // Identifiers: opaque member id for the candidate; a vanity given in other letter case is echoed as given.
  r = await run(fsd(J.member), 'ewa-colleague', { connected: [J.member] }); out.opaque = r.result; out.opaqueUrls = urls(r);
  // Profile lookups equal the proven script's, parameter for parameter, for a vanity and for an opaque id (the colleague's and the candidate's are looked up alike).
  const profileCall = (c) => ({ url: c.url, credentials: c.init.credentials, headers: c.init.headers, method: c.init.method || null });
  const profileCallsOf = (rr) => rr.calls.filter((c) => c.url.includes('voyager/api/graphql')).map(profileCall);
  r = await run('jane-doe', 'ewa-colleague', { connected: [J.member] });
  out.vanityRun = profileCallsOf(r); out.vanityEvidence = [profileCall((await evidence('ewa-colleague')).calls[0]), profileCall((await evidence('jane-doe')).calls[0])];
  r = await run(fsd(J.member), fsd(C.member), { connected: [J.member] });
  out.opaqueRun = profileCallsOf(r); out.opaqueEvidence = [profileCall((await evidence(fsd(C.member))).calls[0]), profileCall((await evidence(fsd(J.member))).calls[0])];
  out.opaqueBoth = r.result; out.opaqueBothShort = shortUrls(r);
  // The vanity the live test used was a real one: the colleague's, in a plain vanity form like the live one, and the candidate an opaque id (the form Mosaico hands over).
  r = await run(fsd(J.member), 'ewa-colleague', { connected: [J.member] }); out.vanityColleagueOpaqueCandidate = r.result; out.vanityColleagueOpaqueCandidateShort = shortUrls(r);
  // A redirected vanity: LinkedIn answers the old vanity with the one Profile of the new one (the evidence script accepts it, so does this one).
  r = await run('jane-doe', 'ewa-old-vanity', { connected: [J.member], redirects: { 'ewa-old-vanity': { person: C, vanity: 'ewa-colleague' } } }); out.redirected = r.result; out.redirectedShort = shortUrls(r);
  // The 0.9.4 failure: a profile answer without `included` (what a plain accept header gets) is the colleague not resolved after one call, and nothing is searched.
  r = await run('jane-doe', 'ewa-colleague', { router: (url, init) => (url.includes('voyagerIdentityDashProfiles') ? ok({ data: { data: {} } }) : bad(500)) }); out.noIncluded = r.result; out.noIncludedCalls = r.calls.length;
  out.upper = (await run('Jane-Doe', 'EWA-Colleague', { connected: [J.member] })).result;
  // Odd characters in a name go to LinkedIn encoded and never as raw brackets, quotes or stars.
  r = await run('zoe-obrien', 'ewa-colleague', { connected: [] }); out.strange = r.result; out.strangeUrls = urls(r);

  // Proof fields (0.9.11).
  r = await run('jane-doe', 'ewa-colleague', { connected: [] }); out.notFoundFull = r.result; out.notFoundFullUrls = urls(r); out.notFoundFullDelays = r.delays; out.notFoundFullSecrets = ['Secret', 'Jane', 'Doe', 'Ewa', 'Colleague', 'headline'].some((x) => JSON.stringify(r.result).includes(x));
  r = await run('jane-doe', 'ewa-colleague', { connected: [], controlTotal: 7 }); out.smallControl = r.result;
  r = await run('jane-doe', 'ewa-colleague', { connected: [], controlTotal: 0 }); out.zeroControl = r.result;
  out.hiddenFull = (await run('jane-doe', 'ewa-colleague', { hidden: true })).result;
  // The page cap: three filtered pages exist, two are read, so the search is not complete.
  out.capped = (await run('jane-doe', 'ewa-colleague', { ...filler, candidateFirst: true })).result;
  // Exactly one full page whose start + count reaches paging.total: complete although the page is full, and no second page is read.
  r = await run('jane-doe', 'ewa-colleague', { extraNamesakes: 25, connectedFiller: 25, connected: [], candidateFirst: true }); out.exactPage = r.result; out.exactPageUrls = urls(r);
  // A full first page and a second short page: complete after two pages.
  r = await run('jane-doe', 'ewa-colleague', { extraNamesakes: 30, connectedFiller: 30, connected: [], candidateFirst: true }); out.shortSecondPage = r.result; out.shortSecondPageUrls = urls(r);
  // No paging.total at all: only a short page can end the search. A full page after a full page at the cap is not the end; a short one is.
  out.noPagingTotal = (await run('jane-doe', 'ewa-colleague', { extraNamesakes: 60, connectedFiller: 60, connected: [], candidateFirst: true, noPagingTotal: true })).result;
  out.noPagingTotalShort = (await run('jane-doe', 'ewa-colleague', { extraNamesakes: 25, connectedFiller: 25, connected: [], candidateFirst: true, noPagingTotal: true })).result;
  // Unreadable rows among the narrowed results are counted (2 of 5), on every narrowed page.
  out.unreadableSome = (await run('jane-doe', 'ewa-colleague', { extraNamesakes: 5, connectedFiller: 5, connected: [], unreadableCount: 2 })).result;
  // The control search fails: the proof field is empty, nothing else moves.
  out.controlForbidden = (await run('jane-doe', 'ewa-colleague', { connected: [], controlStatus: 403 })).result;
  out.control500 = (await run('jane-doe', 'ewa-colleague', { connected: [], controlStatus: 500 })).result;
  out.controlNetwork = (await run('jane-doe', 'ewa-colleague', { connected: [], controlNetwork: true })).result;
  out.controlBadBody = (await run('jane-doe', 'ewa-colleague', { connected: [], controlBadBody: true })).result;
  out.controlNoEcho = (await run('jane-doe', 'ewa-colleague', { connected: [], controlNoEcho: true })).result;
  out.controlNoPaging = (await run('jane-doe', 'ewa-colleague', { connected: [], controlNoPaging: true })).result;
  // A found candidate needs no control search, and one who could not be looked up is not searched at all.
  r = await run('jane-doe', 'ewa-colleague', { connected: [J.member] }); out.foundNoControlCalls = r.calls.length;

  // Fail closed.
  out.signedOut = await run('jane-doe', 'ewa-colleague', { connected: [J.member] }, ''); out.signedOutCalls = out.signedOut.calls.length; out.signedOut = out.signedOut.result;
  out.emptyCandidate = await run('', 'ewa-colleague', {}); out.emptyCandidateCalls = out.emptyCandidate.calls.length; out.emptyCandidate = out.emptyCandidate.result;
  out.emptyColleague = await run('jane-doe', '', {}); out.emptyColleagueCalls = out.emptyColleague.calls.length; out.emptyColleague = out.emptyColleague.result;
  out.profileForbidden = (await run('jane-doe', 'ewa-colleague', { profileStatus: 403 })).result;
  out.typeaheadForbidden = (await run('jane-doe', 'ewa-colleague', { typeaheadStatus: 429 })).result;
  out.searchForbidden = (await run('jane-doe', 'ewa-colleague', { searchStatus: 403, connected: [J.member] })).result;
  out.search500 = (await run('jane-doe', 'ewa-colleague', { searchStatus: 500 })).result;
  out.noEcho = (await run('jane-doe', 'ewa-colleague', { connected: [J.member], noEcho: true })).result;
  out.unreadable = (await run('jane-doe', 'ewa-colleague', { connected: [J.member], unreadable: true })).result;
  out.mismatchObject = (await run('jane-doe', 'ewa-colleague', { connected: [J.member], mismatchObject: true })).result;
  out.badSearchBody = (await run('jane-doe', 'ewa-colleague', { badSearchBody: true })).result;
  out.network = (await run('jane-doe', 'ewa-colleague', { router: () => new Error('net') })).result;
  out.badJson = (await run('jane-doe', 'ewa-colleague', { router: () => ({ ok: true, status: 200, json: async () => { throw new SyntaxError('x'); } }) })).result;
  out.laterNetwork = (await run('jane-doe', 'ewa-colleague', { connected: [J.member], router: (url, init) => (url.includes('salesApiLeadSearch') ? new Error('net') : route({ calls: [], connected: [J.member] })(url, init)) })).result;
  console.log(JSON.stringify(out));
})();
"""


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


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def call(tool_name: str, tool_input: object) -> tuple[bool, str]:
    return gate.decide({"tool_name": tool_name, "tool_input": tool_input})


def with_values(candidate: str, colleague: str) -> str:
    lines = SOURCE.split("\n")
    lines[0], lines[1] = f'const PUBLIC_IDENTIFIER = "{candidate}";', f'const COLLEAGUE_IDENTIFIER = "{colleague}";'
    return "\n".join(lines)


def check_static() -> None:
    lines = SOURCE.split("\n")
    check(lines[0] == 'const PUBLIC_IDENTIFIER = "";' and lines[1] == 'const COLLEAGUE_IDENTIFIER = "";', "the two placeholders are not lines 1 and 2")
    check(SOURCE.count("PUBLIC_IDENTIFIER") >= 2 and SOURCE.count("const PUBLIC_IDENTIFIER") == 1 and SOURCE.count("const COLLEAGUE_IDENTIFIER") == 1, "a placeholder is declared twice")
    check(SCRIPT.name in gate.approved_scripts(), "the gate does not know the colleague-connection script")
    # Word for word (values only) and as a run directive: the approved file with only the two value lines changed.
    check(call(TOOL, {"text": with_values("jane-doe", "ewa-betkier")})[0], "script with both identifiers refused")
    allowed, _, updated = gate.evaluate({"tool_name": TOOL, "tool_input": {"text": "// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=jane-doe COLLEAGUE_IDENTIFIER=ewa-betkier"}})
    check(allowed and updated == {"text": with_values("jane-doe", "ewa-betkier")}, "the directive did not expand to the approved script")
    check(not call(TOOL, {"text": SOURCE})[0], "the template with empty identifiers passed")
    # The last line returns the sealed payload and nothing else; the seal is computed from the payload as the very last step.
    last = SOURCE.rstrip("\n").split("\n")[-1]
    check(last == '({ ...payload, integrity: { algorithm: "fnv1a32", digest: fnv1a32(canonical(payload)) } })', "the last line is not the sealed payload")
    body_lines = SOURCE.rstrip("\n").split("\n")
    payload_line = next(line for line in body_lines if line.startswith("const payload = "))
    check(body_lines.index(payload_line) == len(body_lines) - 2, "something is computed between the payload and its seal")
    check("integrity" not in payload_line, "the payload holds the integrity field before it is computed")
    check(payload_line == 'const payload = { status, signedIn: csrf !== "", capturedAt, state, colleague, candidate, filter: { type: "CONNECTION_OF" }, found: state === "ok" && found, resultsTotal, pagesRead, complete, controlTotal, visibility, unreadableRows };',
          "the payload is not exactly the contract's fields, with found false unless state is ok")
    check("csrf:" not in last and "csrf," not in last and "csrf }" not in payload_line, "the token is returned")
    # Only LinkedIn's own endpoints: the profile query, the typeahead and the lead search.
    addresses = sorted(re.findall(r"https://[^\"' ]+", "\n".join(line for line in body_lines if not line.startswith("//"))))
    check(addresses == ["https://www.linkedin.com/sales-api/salesApiFacetTypeahead", "https://www.linkedin.com/sales-api/salesApiLeadSearch", "https://www.linkedin.com/voyager/api/graphql"],
          f"the script names an address other than the three LinkedIn endpoints: {addresses}")
    code = "\n".join(line for line in body_lines if not line.startswith("//"))
    check(code.count("fetch(") == 1, "the script calls fetch from more than one place")
    for banned in ("localStorage", "sessionStorage", "indexedDB", "document.cookie.split", "console.", "XMLHttpRequest", "sendBeacon", "window.open", "location", "import("):
        check(banned not in code, f"the script uses {banned}")
    check(code.count("document.cookie") == 1 and "JSESSIONID" in code, "the cookie is read for more than the CSRF token")
    # The rules in the header and the code: states, found, bounds, the filter and what is never taken by name.
    for state in ("ok", "colleague-not-resolved", "candidate-not-resolved", "error"):
        check(f'"{state}"' in code, f"the script never produces state {state}")
    check("MAX_FILTERED_PAGES = 2;" in code and "PAGE_SIZE = 25;" in code and "type=CONNECTION_OF" in code and "type:CONNECTION_OF" in code, "the page or filter bounds changed")
    check("selectionType:INCLUDED" in code and "decorationId=" in code, "the search query lost its filter value or decoration")
    check("found = false" in code and code.count("found = true") == 1, "found is set to true in more than one place")
    # 0.9.11: one control search (same filter, no keyword, count 1), never "hidden" (no hidden-list marker is known), fail closed.
    check(code.count("search(null,") == 1 and "search(null, colleague.salesNavId, filterText, 0, 1)" in code, "the control search is not one call of the same filter with no keyword and count 1")
    check('"hidden"' not in code, "the script says hidden although no hidden-list marker is known")
    check("controlTotal = null; visibility = \"unknown\"; }" in code, "a failed control search does not empty controlTotal")
    for field in ("complete", "controlTotal", "visibility", "unreadableRows"):
        check(f"{field}" in payload_line, f"the payload lacks {field}")
    check("normalizeText" in SOURCE and "const normalizeText = " in SOURCE, "the script lost the shared normalisation rule")
    # The header says what the proof fields are, that the control search is the sixth call, and that no hidden-list marker is known.
    header = "\n".join(line for line in body_lines if line.startswith("//"))
    for needle in ("Proof fields (0.9.11", "complete:", "controlTotal:", "visibility:", "unreadableRows:", "the control search", "No such marker is known", "never says \"hidden\"", "its last page held fewer results than a page"):
        check(needle in header, f"the script header lacks: {needle}")
    check("never retries" in SOURCE and "Never a wrong" in SOURCE.replace("never in a wrong", "Never a wrong") or "never in a wrong" in SOURCE, "the header lost its fail-closed statement")
    # Nothing from a result row is copied into the output except ids: the output is built from these fields only.
    for forbidden in ("fullName", "headline", "displayValue }", "firstName }", "lastName }"):
        check(forbidden not in payload_line, f"the payload carries {forbidden}")


def check_behaviour(out: dict) -> None:
    ids = out["ids"]
    keys = ["status", "signedIn", "capturedAt", "state", "colleague", "candidate", "filter", "found", "resultsTotal", "pagesRead", "complete", "controlTotal", "visibility", "unreadableRows", "integrity"]
    found = out["found"]
    check(sorted(found) == sorted(keys), f"unexpected keys {sorted(found)}")
    check(found["integrity"]["algorithm"] == "fnv1a32" and re.fullmatch(r"[0-9a-f]{8}", found["integrity"]["digest"]) is not None, "the record is not sealed with an fnv1a32 digest")
    check(found["status"] == 200 and found["signedIn"] is True and found["state"] == "ok" and found["found"] is True, f"found not reported: {found}")
    check(found["filter"] == {"type": "CONNECTION_OF"}, "the filter is not CONNECTION_OF")
    check(found["colleague"] == {"input": "ewa-colleague", "salesNavId": ids["colleagueSales"], "memberId": 300001}, f"colleague wrong: {found['colleague']}")
    check(found["candidate"] == {"input": "jane-doe", "salesNavId": ids["candidateSales"], "memberId": 553472255}, f"candidate wrong: {found['candidate']}")
    check(found["resultsTotal"] == "1" and found["pagesRead"] == 1, "resultsTotal or pagesRead wrong")
    check(re.fullmatch(r"\d{4}-\d\d-\d\dT[\d:.]+Z", found["capturedAt"]) is not None, "capturedAt is not an ISO time")
    check(out["leaked"] is False, "the CSRF token reached the result")
    check(out["secrets"] is False, "a name, headline, picture or company reached the result")
    check(all(c == "include" for c in out["foundCreds"]), "a call did not use the page's own session")
    check(all(h["csrf-token"] == "ajax:SECRET-TOKEN" and h["x-restli-protocol-version"] == "2.0.0" for h in out["foundHeaders"]), "request headers are not the documented ones")
    check([h["accept"] for h in out["foundHeaders"]] == [NORMALIZED_ACCEPT, "application/json", NORMALIZED_ACCEPT, "application/json"], f"accept headers wrong (the profile query needs the normalized one): {out['foundHeaders']}")
    # The calls, in order: the colleague's profile, her typeahead entry, the candidate's profile, the filtered search. Nothing else.
    check(out["foundShort"] == ["/voyager/api/graphql", "/sales-api/salesApiFacetTypeahead", "/voyager/api/graphql", "/sales-api/salesApiLeadSearch"], f"unexpected calls {out['foundShort']}")
    check("vanityName:ewa-colleague" in out["foundUrls"][0] and "vanityName:jane-doe" in out["foundUrls"][2], "profiles were not looked up by the two identifiers")
    check(out["foundUrls"][1] == "/sales-api/salesApiFacetTypeahead?q=query&start=0&count=10&type=CONNECTION_OF&query=Ewa%20Colleague", f"typeahead call wrong: {out['foundUrls'][1]}")
    search = out["foundUrls"][3]
    check(search.startswith("/sales-api/salesApiLeadSearch?q=searchQuery&query=(filters:List((type:CONNECTION_OF,values:List((id:" + ids["colleagueSales"] + ",text:Ewa%20Colleague,selectionType:INCLUDED)))),keywords:Jane%20Doe)&start=0&count=25&decorationId="),
          f"filtered search call wrong: {search}")
    check(out["foundDelays"] == [500, 500], f"calls to Sales Navigator were not spaced: {out['foundDelays']}")

    # Profile lookups: the same request, parameter for parameter, as the proven connection-evidence script makes for the same identifier.
    check(len(out["vanityRun"]) == 2 and out["vanityRun"] == out["vanityEvidence"], f"vanity profile requests differ from the evidence script's: {out['vanityRun']} vs {out['vanityEvidence']}")
    check(len(out["opaqueRun"]) == 2 and out["opaqueRun"] == out["opaqueEvidence"], f"opaque-id profile requests differ from the evidence script's: {out['opaqueRun']} vs {out['opaqueEvidence']}")
    check(out["vanityRun"][0]["headers"]["accept"] == NORMALIZED_ACCEPT and out["vanityRun"][0]["credentials"] == "include" and "queryId=voyagerIdentityDashProfiles.34ead06db82a2cc9a778fac97f69ad6a" in out["vanityRun"][0]["url"],
          "the profile request is not the documented one")
    both = out["opaqueBoth"]
    check(both["state"] == "ok" and both["found"] is True and both["colleague"]["memberId"] == 300001 and both["candidate"]["memberId"] == 553472255
          and out["opaqueBothShort"] == ["/voyager/api/graphql", "/sales-api/salesApiFacetTypeahead", "/voyager/api/graphql", "/sales-api/salesApiLeadSearch"], f"two opaque ids were not resolved through to the search: {both}")
    mixed = out["vanityColleagueOpaqueCandidate"]
    check(mixed["state"] == "ok" and mixed["found"] is True and mixed["candidate"]["memberId"] == 553472255 and out["vanityColleagueOpaqueCandidateShort"][-1] == "/sales-api/salesApiLeadSearch", f"a vanity colleague with an opaque candidate was not resolved: {mixed}")
    redirected = out["redirected"]
    check(redirected["state"] == "ok" and redirected["colleague"]["input"] == "ewa-old-vanity" and redirected["colleague"]["memberId"] == 300001
          and out["redirectedShort"] == ["/voyager/api/graphql", "/sales-api/salesApiFacetTypeahead", "/voyager/api/graphql", "/sales-api/salesApiLeadSearch"], f"a redirected vanity was not resolved: {redirected}")
    check(out["noIncluded"]["state"] == "colleague-not-resolved" and out["noIncluded"]["found"] is False and out["noIncludedCalls"] == 1, "a profile answer without included was not a clean colleague-not-resolved")

    # Not found: the search ran, the candidate is real and their own id is read from the unfiltered results. Never "found".
    nf = out["notFound"]
    check(nf["state"] == "ok" and nf["found"] is False and nf["resultsTotal"] == "0" and nf["pagesRead"] == 3 and nf["status"] == 200, f"not-found record wrong: {nf}")
    check(nf["candidate"]["salesNavId"] == ids["candidateSales"] and nf["candidate"]["memberId"] == 553472255, "a not-found candidate's own ids were not read")
    check(out["notFoundShort"][-3:] == ["/sales-api/salesApiLeadSearch"] * 3 and "filters:List" in out["notFoundUrls"][3] and "filters:List" not in out["notFoundUrls"][4]
          and out["notFoundUrls"][4].startswith("/sales-api/salesApiLeadSearch?q=searchQuery&query=(keywords:Jane%20Doe)&start=0&count=25"), f"the unfiltered resolution search is wrong: {out['notFoundUrls']}")
    # Names are never matched: a connected namesake is not the candidate.
    check(out["namesakeConnected"]["state"] == "ok" and out["namesakeConnected"]["found"] is False, "a connected namesake was taken for the candidate")
    check(out["namesakeConnected"]["candidate"]["memberId"] == 553472255 and out["namesakeId"] == ids["candidateSales"], "the candidate's id was not chosen by member id among namesakes")
    check(out["namesakeOnly"]["found"] is True and out["namesakeOnly"]["candidate"]["salesNavId"] == ids["namesakeSales"], "the namesake, searched as themselves, was not found by their own id")
    # The colleague's entry is the one whose id decodes to her member id; similar names before or after her are not taken.
    check(out["herFirst"]["found"] is True and out["herFirst"]["colleague"]["salesNavId"] == ids["colleagueSales"], "the colleague's typeahead entry was not chosen by member id")
    check(out["noColleagueEntry"]["state"] == "colleague-not-resolved" and out["noColleagueEntry"]["found"] is False and out["noColleagueEntry"]["colleague"]["salesNavId"] is None
          and out["noColleagueEntry"]["colleague"]["memberId"] == 300001 and out["noColleagueEntryCalls"] == 2, f"similar-name entries were taken for the colleague: {out['noColleagueEntry']}")
    check(out["noColleagueEntry"]["candidate"] == {"input": "jane-doe", "salesNavId": None, "memberId": None}, "the candidate was looked up although the colleague was not resolved")
    check(out["colleagueUnknown"]["state"] == "colleague-not-resolved" and out["colleagueUnknown"]["found"] is False and out["colleagueUnknownCalls"] == 1, "an unknown colleague profile was not reported")
    check(out["candidateUnknown"]["state"] == "candidate-not-resolved" and out["candidateUnknown"]["found"] is False and out["candidateUnknown"]["colleague"]["salesNavId"] == ids["colleagueSales"]
          and out["candidateUnknown"]["candidate"] == {"input": "nobody-here", "salesNavId": None, "memberId": None}
          and "/sales-api/salesApiLeadSearch" not in out["candidateUnknownShort"], f"an unknown candidate was searched or misreported: {out['candidateUnknown']}")
    check(out["sameAsColleague"]["state"] == "candidate-not-resolved" and out["sameAsColleague"]["found"] is False and out["sameAsColleague"]["candidate"]["memberId"] == out["sameAsColleague"]["colleague"]["memberId"]
          and "/sales-api/salesApiLeadSearch" not in out["sameShort"], "a candidate who is the colleague was searched")
    check(out["notInPlain"]["state"] == "candidate-not-resolved" and out["notInPlain"]["found"] is False and out["notInPlain"]["candidate"]["salesNavId"] is None
          and out["notInPlain"]["candidate"]["memberId"] == 553472255 and out["notInPlain"]["status"] == 200, f"a candidate absent from the unfiltered results was not reported: {out['notInPlain']}")
    check(out["hidden"]["state"] == "ok" and out["hidden"]["found"] is False and out["hidden"]["resultsTotal"] == "0", "a hidden list was reported as anything but not found")

    # Paging: at most two filtered pages, and the candidate on page 2 is found.
    two = out["twoPages"]
    check(two["state"] == "ok" and two["found"] is False and two["pagesRead"] == 4, f"two filtered pages, one unfiltered page and the control search were not read: {two}")
    check(sum("filters:List" in u for u in out["twoPagesUrls"]) == 3 and [u.rsplit("&start=", 1)[1].split("&")[0] for u in out["twoPagesUrls"] if "salesApiLeadSearch" in u] == ["0", "25", "0", "0"], f"start did not move by 25 or a third narrowed page was read: {out['twoPagesUrls']}")
    lost = out["lostInNamesakes"]
    check(lost["state"] == "candidate-not-resolved" and lost["found"] is False and lost["candidate"]["salesNavId"] is None and lost["pagesRead"] == 3, f"a candidate lost among namesakes was guessed: {lost}")
    check(out["onePageFound"]["found"] is True and out["onePageFound"]["pagesRead"] == 1 and out["onePageFoundCalls"] == 4, "a short first page was read past its end")
    check(out["secondPageFound"]["found"] is True and out["secondPageFound"]["pagesRead"] == 2 and out["secondPageFound"]["resultsTotal"] == "31"
          and sum("salesApiLeadSearch" in u for u in out["secondPageUrls"]) == 2, "the candidate on page 2 was not found")

    # Identifiers are echoed exactly as given; an opaque member id works for the candidate.
    check(out["opaque"]["found"] is True and out["opaque"]["candidate"]["input"].startswith("ACoAA") and out["opaque"]["candidate"]["memberId"] == 553472255, f"an opaque candidate id was not resolved: {out['opaque']}")
    check(out["upper"]["colleague"]["input"] == "EWA-Colleague" and out["upper"]["candidate"]["input"] == "Jane-Doe" and out["upper"]["found"] is True, "an identifier was not echoed exactly as given")
    # A name with brackets, quotes and stars goes to LinkedIn encoded: no raw bracket, quote or star in the keyword.
    keyword = [u for u in out["strangeUrls"] if "salesApiLeadSearch" in u][0].split("keywords:", 1)[1].split(")&start=")[0]
    check(keyword == "Zo%C3%AB%20%28Z.%29%20O%27Brien%2A" and out["strange"]["state"] == "ok", f"a name with odd characters was not encoded: {keyword}")


    # Proof fields (0.9.11): inside the sealed record, each computed from LinkedIn's own paging.
    check(found["complete"] is True and found["controlTotal"] is None and found["visibility"] == "unknown" and found["unreadableRows"] == 0 and out["foundNoControlCalls"] == 4,
          f"a listed candidate should read its one page to the end and need no control search: {found}")
    full = out["notFoundFull"]
    control = out["notFoundFullUrls"][5]
    check(full["complete"] is True and full["controlTotal"] == "1432" and full["visibility"] == "visible" and full["unreadableRows"] == 0 and full["pagesRead"] == 3 and full["resultsTotal"] == "0",
          f"a completed not-found did not carry its proof fields: {full}")
    check(len(out["notFoundFullUrls"]) == 6 and out["notFoundFullDelays"] == [500, 500, 500, 500], f"the control search is not the sixth call, or Sales Navigator calls were not spaced: {out['notFoundFullDelays']}")
    check(control == "/sales-api/salesApiLeadSearch?q=searchQuery&query=(filters:List((type:CONNECTION_OF,values:List((id:" + ids["colleagueSales"] + ",text:Ewa%20Colleague,selectionType:INCLUDED)))))&start=0&count=1&decorationId=com.linkedin.sales.deco.desktop.searchv2.LeadSearchResult-14",
          f"the control search is not the same filter with no keyword and count 1: {control}")
    check(out["notFoundFullSecrets"] is False, "a name or headline reached a not-found record")
    check(out["smallControl"]["controlTotal"] == "7" and out["smallControl"]["visibility"] == "visible", "a small control total is not reported as it is")
    check(out["zeroControl"]["controlTotal"] == "0" and out["zeroControl"]["visibility"] == "unknown" and out["zeroControl"]["state"] == "ok" and out["zeroControl"]["found"] is False,
          f"a control total of 0 should be reported as 0 and not called visible: {out['zeroControl']}")
    hid = out["hiddenFull"]
    check(hid["complete"] is True and hid["controlTotal"] == "0" and hid["visibility"] == "unknown" and hid["found"] is False, f"an empty list is not reported as total 0, visibility unknown: {hid}")
    # complete: the page cap, an exact full page, a short second page, a missing paging.total.
    check(out["capped"]["complete"] is False and out["capped"]["state"] == "ok" and out["capped"]["controlTotal"] == "1432", f"stopping at the page cap was reported as complete: {out['capped']}")
    ex = out["exactPage"]
    check(ex["complete"] is True and sum("filters:List" in u and "keywords" in u for u in out["exactPageUrls"]) == 1, f"a full page that reaches paging.total was not complete after one page: {ex}")
    sp = out["shortSecondPage"]
    check(sp["complete"] is True and sum("filters:List" in u and "keywords" in u for u in out["shortSecondPageUrls"]) == 2, f"a short second page did not end the search as complete: {sp}")
    check(out["noPagingTotal"]["complete"] is False and out["noPagingTotal"]["state"] == "ok", "a capped read with no paging.total was reported as complete")
    check(out["noPagingTotalShort"]["complete"] is True and out["noPagingTotalShort"]["state"] == "ok", "a short page after a full one, with no paging.total, did not end the search")
    # unreadableRows counts rows without a readable id among the narrowed pages.
    check(out["unreadableSome"]["unreadableRows"] == 2 and out["unreadableSome"]["state"] == "ok" and out["unreadableSome"]["complete"] is True, f"unreadable rows were not counted: {out['unreadableSome']}")
    # The control search failing leaves everything else as it was.
    for name in ("controlForbidden", "control500", "controlNetwork", "controlBadBody", "controlNoEcho", "controlNoPaging"):
        record = out[name]
        check(record["controlTotal"] is None and record["visibility"] == "unknown" and record["state"] == "ok" and record["found"] is False and record["status"] == 200 and record["complete"] is True
              and record["candidate"]["salesNavId"] == ids["candidateSales"], f"{name}: a failed control search changed more than controlTotal: {record}")
    # The seal covers the new fields: change any of them and the digest no longer matches.
    for field, value in (("complete", False), ("controlTotal", "1"), ("visibility", "unknown"), ("unreadableRows", 1)):
        tampered = {**full, field: value}
        check(digest_of(tampered) != full["integrity"]["digest"], f"the digest does not cover {field}")
    check(digest_of(full) == full["integrity"]["digest"], "the not-found digest is not the canonical one")

    # Fail closed: state error, found false, never a throw.
    for name, status in (("profileForbidden", 403), ("typeaheadForbidden", 429), ("searchForbidden", 403), ("search500", 500)):
        record = out[name]
        check(record["state"] == "error" and record["found"] is False and record["status"] == status and record["resultsTotal"] is None, f"{name}: not reduced to an error with status {status}: {record}")
    for name in ("noEcho", "unreadable", "mismatchObject", "badSearchBody"):
        record = out[name]
        check(record["state"] == "error" and record["found"] is False and record["status"] == 200, f"{name}: an answer not in the expected shape was not an error: {record}")
    for name in ("network", "badJson"):
        check(out[name]["state"] == "error" and out[name]["status"] == 0 and out[name]["found"] is False, f"{name}: not an error with status 0")
    check(out["laterNetwork"]["state"] == "error" and out["laterNetwork"]["status"] == 0 and out["laterNetwork"]["found"] is False, "a failed search was not an error with status 0")
    for name, calls in (("signedOut", out["signedOutCalls"]), ("emptyCandidate", out["emptyCandidateCalls"]), ("emptyColleague", out["emptyColleagueCalls"])):
        record = out[name]
        check(record["state"] == "error" and record["found"] is False and record["status"] == 0 and calls == 0, f"{name}: still called LinkedIn or was not an error")
    check(out["signedOut"]["signedIn"] is False and out["signedOut"]["colleague"]["input"] == "ewa-colleague" and out["signedOut"]["candidate"]["input"] == "jane-doe", "a signed-out record lost the identifiers it echoes")
    check(out["emptyColleague"]["signedIn"] is True and out["emptyCandidate"]["signedIn"] is True, "signedIn is not the CSRF cookie's presence")

    # The state/found rules, whatever happened: found only with state ok, ok only with both ids and status 200.
    every = [v for k, v in out.items() if isinstance(v, dict) and "integrity" in v]
    check(len(every) >= 25, f"too few records checked: {len(every)}")
    for record in every:
        if record["found"]:
            check(record["state"] == "ok", "found is true although the state is not ok")
        if record["state"] == "ok":
            check(record["colleague"]["salesNavId"] is not None and record["candidate"]["salesNavId"] is not None and record["signedIn"] is True and record["status"] == 200
                  and record["colleague"]["memberId"] is not None and record["candidate"]["memberId"] is not None, f"state ok without both ids, a session or status 200: {record}")
        check(record["state"] in ("ok", "colleague-not-resolved", "candidate-not-resolved", "error"), "unknown state")
        check(isinstance(record["complete"], bool) and isinstance(record["unreadableRows"], int) and record["unreadableRows"] >= 0 and record["visibility"] in ("visible", "unknown"),
              f"a proof field is missing or has a value the script cannot give: {record}")
        check(record["controlTotal"] is None or re.fullmatch(r"\d+", record["controlTotal"]) is not None, "controlTotal is not digits")
        check((record["visibility"] == "visible") == (record["controlTotal"] is not None and int(record["controlTotal"]) > 0), "visibility visible does not match a control total above 0")
        if record["found"] or record["state"] != "ok":
            check(record["controlTotal"] is None, "a control total came from a record that was not an ok not-found")
        if record["state"] == "error":
            check(record["complete"] is False, "an error record claims a complete search")
        check(isinstance(record["pagesRead"], int) and 0 <= record["pagesRead"] <= 50, "pagesRead out of range")
        check(record["integrity"]["digest"] == digest_of(record), "the digest is not the canonical-JSON FNV-1a of the rest of the record")
        check(set(record["colleague"]) == {"input", "salesNavId", "memberId"} and set(record["candidate"]) == {"input", "salesNavId", "memberId"}, "a person carries more than input, salesNavId and memberId")
    check(all(record["integrity"]["digest"] != "00000000" for record in every), "a digest is a placeholder")


def main() -> None:
    check_static()
    node = shutil.which("node")
    if node is None:
        print("SKIP: node is not installed, so the colleague-connection script was not run against a fake LinkedIn (static and gate checks passed).")
        return
    done = subprocess.run([node, "-e", HARNESS, str(SCRIPT), str(EVIDENCE)], capture_output=True, text=True, check=False)
    check(done.returncode == 0, f"harness failed: {done.stderr[-600:]}")
    check_behaviour(json.loads(done.stdout))
    print("PASS: the colleague-connection script is gated word for word, resolves both people by member id (never by name), returns only ids, seals its record last, and fails closed.")


if __name__ == "__main__":
    main()
