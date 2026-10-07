# Mosaico assistant plugins

Public, read-only distribution repository for the official Mosaico plugins for Codex and Claude
Code. Both packages connect to the production Mosaico MCP service and require each user to sign in
with their own Mosaico account.

The repository intentionally contains only provider manifests, the public MCP endpoint and thin
interaction skills. Mosaico application code, workflow state, authorization rules, credentials,
customer data and deployment configuration are not distributed here.

## Codex

Add the Git marketplace and install the plugin:

```bash
codex plugin marketplace add mosaicohr-com/Mosaico-Codex-Plugin
codex plugin add mosaico@mosaico
```

Restart Codex and begin a new conversation after installation. Codex will request authorization
for `https://app.mosaico.one/api/mcp`; sign in with your own Mosaico account.

## Claude Code

From Claude Code:

```text
/plugin marketplace add mosaicohr-com/Mosaico-Codex-Plugin
/plugin install mosaico@mosaico
```

Complete Mosaico authorization using your own account when prompted.

## Outreach workflows

The provider packages include dedicated invitation, follow-up and schedule-installation skills.
Use `$mosaico:mosaico-outreach` in Codex or `/mosaico:mosaico-outreach` in Claude Code to choose an
action. The schedule option installs three per-user local-time schedules: Sync data (connections and
messaging, once a day, the only one that sends), Source leads (every two hours in business hours,
at least 60 minutes from Sync, never sends; each sourcing start carries a quota of who receives the Leads and how many) and Repair (once a week, Sunday 10:00 AM by default, also on
demand, never sends). Before installing, the Claude package checks that
`~/.claude/settings.json` allows the three browser tools scheduled sessions need
(`mcp__Claude_Browser__javascript_tool`, `mcp__Claude_Browser__computer` and
`mcp__Claude_Browser__browser_batch`; the pane batches a click with a wait and a screenshot through the
last one, so without it every Connect or Send click is blocked), and both packages
refuse while stale `mosaico-outreach-*` skill copies or the old Codex automations exist; Codex installs
only Source leads. Plugin installation never creates or enables a user's schedules silently.

## Set up a second person

A colleague sets up her own schedules on her own Mac:

1. Install the Claude desktop app on her Mac, with the Mosaico plugin from the marketplace, version 0.6.1
   or later.
2. Sign the Mosaico connector in as her own Mosaico account. She must be an active member of the
   organisation; an Owner or Admin can check in Outreach, Agent tab.
3. Sign in to her own LinkedIn inside Claude's built-in browser pane.
4. Put the three allow rules in her own `~/.claude/settings.json`:

   ```json
   {
     "permissions": {
       "allow": [
         "mcp__Claude_Browser__javascript_tool",
         "mcp__Claude_Browser__computer",
         "mcp__Claude_Browser__browser_batch"
       ]
     }
   }
   ```

5. Register her LinkedIn profile in Mosaico Outreach, Agent tab, "LinkedIn profile". The installer checks
   it with `outreach_start_run` (intent `inspect_day`); if Mosaico answers
   `linkedin_identity_not_registered`, register the profile there, or have an Owner do it, and check again.
6. Run the schedule installer. It installs her Sync data schedule, and Source leads only if she sources
   Leads herself Her Source leads schedule needs her own member id in its quota map (the installer asks who receives
   the Leads and how many each, and reads the ids with `get_team_profiles`).

Each person's Sync data schedule runs on that person's own Mac, in that person's own pane, and sends only
from that person's account. Nobody's run touches another owner's Leads.

## Connection-evidence capability (Claude Code)

The Claude Code package verifies LinkedIn connection status through a browser-side capability instead
of any cookie or session export:

- `plugins/mosaico-claude/browser/` holds the six approved capture scripts. Each runs inside the
  signed-in LinkedIn page in Claude's built-in browser pane, calls one fixed LinkedIn endpoint, uses the
  page's own session and CSRF material without ever returning it, and returns only the fields Mosaico's
  evidence parser reads (status, relationship state, profile identifier, capture time). Names, headlines
  and every other field are dropped before anything leaves the page.
- `plugins/mosaico-claude/browser/linkedin-whoami.js` is the identity script: one call to LinkedIn's "who am I" endpoint that returns only the account's numeric id, URNs and public identifier, which a run passes unchanged as `identityEvidence` to `outreach_start_run`.
- `plugins/mosaico-claude/browser/linkedin-thread-messages.js` is the thread script: it takes the Lead's public identifier on its first line and the Lead's name on its second (0.9.2), finds the one-to-one conversation with that Lead by LinkedIn's messaging search on the Lead's name (up to 3 pages) and, when that finds nothing, by paging LinkedIn's conversation list (up to 8 pages, about 160 conversations, stopping at the first page that holds it), and returns only the participants' member ids and the messages oldest first, each with its delivery time, sender and text, plus `coverage` (`complete` or `page-limit`), `lookup` (`search`, `list` or `none`), `pagesRead`, `searchPagesRead` and, since 0.9.2, `matchBasis` (`identifier` or `name`), `requestedName` and the matched person's `displayName`. A run passes the output unchanged as `threadEvidence` to `outreach_deposit_conversation`; Mosaico derives each message's direction and time from it. It runs only in Claude's built-in browser pane.
- Every approved script ends its result with an `integrity` field, `{ algorithm: "fnv1a32", digest }` (0.8.1): FNV-1a 32-bit over the UTF-8 bytes of the canonical JSON (keys sorted, no spaces, object keys whose value is null or undefined omitted at every depth; array items stay) of everything else it returns, computed in the page. The connections script also seals each page. A run passes each output to Mosaico exactly as returned; Mosaico recomputes the digest and refuses an altered copy with `evidence-altered`.
- `plugins/mosaico-claude/browser/linkedin-sent-invitations.js` is the sent-invitations script (0.8.0): it takes the Lead's public identifier on its first line, reads LinkedIn's Sent invitations list (100 a page, up to five pages) until the Lead is found, and returns only `{ status, signedIn, capturedAt, state, publicIdentifier, invitation, pagesRead }`, where `state` is `found`, `not-found` or `error` and `invitation` is `{ sentTime, inviteeUrn, invitationUrn }` or null. A run passes the output unchanged as `sentInvitationEvidence` to `outreach_mark_message_sent`. The endpoint is not validated against a live account yet (validated: pending). It runs only in Claude's built-in browser pane.
- `plugins/mosaico-claude/browser/linkedin-salesnav-colleague-connection.js` is the colleague-connection script (0.9.5): it takes the candidate's public identifier on its first line and the colleague's registered public identifier on its second (Mosaico supplies it; the run never chooses it), and asks Sales Navigator's "Connections of" filter whether the candidate is already one of the colleague's connections. It runs only in the signed-in Sales Navigator page (any `https://www.linkedin.com/sales/` page) in Claude's built-in browser pane, calls only LinkedIn's profile query, the filter's typeahead and the lead search, and returns only `{ status, signedIn, capturedAt, state, colleague, candidate, filter, found, resultsTotal, pagesRead }` (each person as `{ input, salesNavId, memberId }`), where `state` is `ok`, `colleague-not-resolved`, `candidate-not-resolved` or `error`. A run passes the output unchanged as `colleagueConnectionEvidence` to `outreach_save_lead`; Mosaico decides whether to skip the candidate. People are found by numeric member id (decoded from LinkedIn's ids), never by name. `found: false` is never proof that two people are not connected.
- `plugins/mosaico-claude/hooks/browser-script-gate.py` runs before every browser script call. It allows
  an approved script word for word (only the values on its leading placeholder lines may change: the first line, for the thread script the second, the Lead's name, and for the colleague-connection script the second, the colleague's identifier), expands a one-line run
  directive (0.8.4, below) into the approved script, and refuses any other script
  that names LinkedIn or reads a credential store. It logs nothing and never echoes a script, header,
  cookie or response.
- When the capability is unavailable, the skills leave the Lead unverified, report only what the LinkedIn
  page visibly shows, and stop the step. They never scrape browser storage, profile files, DevTools data
  or the keychain.

The Codex package ships no such capability, so its Outreach skills do not capture connection evidence.

## Changelog

### 0.9.5

- Fixes the colleague check: the script now looks up the colleague and the candidate with exactly the request and the reading
  the connection-evidence script uses. 0.9.4 asked LinkedIn for a plain JSON answer, got no profile back and stopped with
  `colleague-not-resolved` after one call, for every colleague.
- Source leads texts (Claude and Codex) now need plugin 0.9.5 or later: run the installer again to update a saved schedule.
  Tests run the script against a fake LinkedIn that answers a profile only to the evidence script's request, and compare the
  profile requests with the evidence script's, parameter for parameter.

### 0.9.4

- Source leads checks whether a candidate is already connected to the colleague before saving the candidate for
  her. New approved script `browser/linkedin-salesnav-colleague-connection.js`. For one candidate and one colleague
  it makes at most these calls to LinkedIn from the signed-in Sales Navigator page, one after the other with a short
  pause, and never retries: LinkedIn's profile query for each person (their member id and name); Sales Navigator's
  "Connections of" typeahead, which searches by text, so the colleague's name is the text and the colleague is the
  entry whose id decodes to her own member id; the lead search with that one filter and the candidate's name as the
  keyword (25 results a page, at most 2 pages), where the candidate is the result whose id decodes to the
  candidate's member id; and, when the filtered search does not list them, one unfiltered keyword page, only to read
  the candidate's own Sales Navigator id (Mosaico needs it). The API cannot restrict a search to one member, so the
  keyword narrows it and the member id decides. Nothing is chosen by name: a person with a similar name is never taken.
- It returns `{ status, signedIn, capturedAt, state, colleague, candidate, filter, found, resultsTotal, pagesRead,
  integrity }` and nothing else: no name, headline or result row leaves the page. `colleague` and `candidate` are each
  `{ input, salesNavId, memberId }` (`input` is the identifier it was given, echoed exactly). `found` is true only
  when `state` is `ok` and the candidate is listed in the colleague's connections. `state` `ok` always carries both
  Sales Navigator ids and status 200. It fails closed: a signed-out page, an error status, an answer not in the
  expected shape, results with no readable id, or a filtered answer that does not echo the colleague's id (the filter
  was not applied) end in `error` with `found` false. The result is sealed with the same `integrity` digest as the
  other scripts, computed last.
- It never sets a connection state and never proves that two people are not connected: `found: false` can mean the
  colleague hides her connections, the candidate hides his, or Sales Navigator does not list everyone. Mosaico saves
  such a candidate with the connection unknown and says so.
- The browser-script gate takes one more placeholder, `COLLEAGUE_IDENTIFIER`, on the script's second line, checked
  exactly like `PUBLIC_IDENTIFIER` (1 to 120 letters, marks and digits of any script, `-`, `.`, `_` and well-formed
  `%XX`; anything else is refused), word for word and as the directive
  `// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=<candidate> COLLEAGUE_IDENTIFIER=<colleague>`.
  The directive must carry both placeholders once each, in that order. Mosaico supplies the colleague's value in
  `workflowStatus.colleagueChecks` and a directive with `<candidate>` left to fill.
- The Claude invite-run skill has a new section, "Check a candidate against the colleague": before saving a
  candidate for a colleague whose check Mosaico lists as allowed, run the directive for the candidate and pass the
  output unchanged as `colleagueConnectionEvidence`. A `skipped` answer `already-connected-to-colleague` is not a
  failure and does not count toward the target: source the next candidate. A `blocked` answer
  `colleague-check-required` (reasons `evidence-missing`, `evidence-altered`, `colleague-evidence-malformed`,
  `colleague-evidence-inconsistent`, `observation-stale`, `observation-time-invalid`, `colleague-mismatch`,
  `candidate-mismatch`, `candidate-is-colleague`) means run the script again and send the new output; never retype it.
  The notes `colleague-check-negative-unproven` (saved, connection unknown, not a proof),
  `colleague-check-unavailable` (saved; no evidence needed for that colleague for the rest of the run) and
  `colleague-check-cap-reached` are explained. The sourcing report now says "skipped as already connected to
  <owner>: N" for each owner, from Mosaico's counts.
- The Source leads schedule text (Claude) lists the new script among the approved scripts and the check; both
  Source leads texts now need plugin 0.9.4 or later: run the installer again to update a saved schedule. The Codex
  package ships no browser scripts: its skills say Codex cannot run the check, and a Codex save for a colleague that
  Mosaico blocks with `colleague-check-required` is left for a Claude run.
- Needs the Mosaico application change that accepts `colleagueConnectionEvidence` (mosaico-app pull request 1811).
  What the 2026-10-07 captures could not show (the capture tool cut long bodies and hid the query and the
  `decorationId`): the keyword field's spelling inside the query, the `decorationId` the Sales Navigator page sends
  and the shape of a result row are the script's best reading, stated in its header. A wrong reading ends in
  `state` `error`, never in a wrong `found`. The first live check must confirm them.
- Tests: the new script runs under node against a fake Sales Navigator (found, not found, namesakes, similar-name
  typeahead entries, hidden list, paging, odd characters, every error path, no name or token in the result, digest
  recomputed independently); the gate tests cover accepted and refused values in both slots and both forms and the
  round trip; skill tests check the wording. Manifests are at 0.9.4.

### 0.9.3

- The browser-script gate accepts non-ASCII public identifiers and Lead names. Until now it refused a first-line
  identifier with any accented or non-Latin letter (for example `josé-garcía-1a2b3c`), so a Sync data run could not
  verify that Lead's connection or read its thread. The identifier and the Lead's name are now checked against what
  may appear, not what may not: letters and combining marks of any script and decimal digits, plus `-`, `.` and `_`
  for an identifier (opaque member ids need them) and spaces, hyphens, apostrophes (`'` or `’`), periods and commas
  for a name, each 1 to 120 characters. Quotes, backslashes, line breaks and other control characters, `$`, backticks,
  brackets, parentheses, `;`, `/`, `<`, `>`, zero-width, joiner and direction-changing characters, lone surrogates and
  private-use characters are refused, which also closes a gap: a zero-width character in a name used to pass.
  A well-formed `%XX` sequence in an identifier is still accepted but never decoded; the application hands the decoded
  identifier. The hook now reads its input as UTF-8 bytes whatever the machine's locale, so a UTF-8 value survives the
  round trip. A name with other punctuation (a pipe, parentheses, a slash, an emoji) is now refused; it used to pass.
  Tests cover accepted and refused values in both forms and the hook under a C and a Latin-1 locale.
- Source leads sends the sourcing quota the server now requires. Since 2026-10-04 Mosaico refuses
  `outreach_start_run` with `intent: source_invitation_leads` (code `sourcing_participant_required`, recommended
  action `name_sourcing_colleague`) unless the call carries `colleagueOwnerUserId` (an active member distinct from
  the run owner; both then get 5) or `quota` (a map from active owner member ids to whole-number targets from 1
  to 100 that includes the run owner's own id; naming anyone else needs an Owner or Admin). A wrong map is refused
  with `sourcing_quota_invalid`. The skills never sent either, so every scheduled Source leads run was refused.
- The invite-run skills (Claude and Codex) now say a sourcing start must carry `quota` or `colleagueOwnerUserId`,
  that the person's standing answer supplies who receives Leads and how many, that member ids come from
  `get_team_profiles` ("Person ID"), that a run which knows neither stops and asks instead of guessing, and what
  to do on `sourcing_participant_required` and `sourcing_quota_invalid`. "Source Leads only" no longer assumes a
  colleague: it covers the person alone, a colleague or a map of several members, and its target is the quota.
  The run report gives Leads saved and quota remaining per owner, and a run that saved nothing is reported as
  failed with Mosaico's code, never as successful.
- The Source leads schedule texts (Claude and Codex) send `<quota map>` on every sourcing start and say "using the
  quota sent at the start"; the installers ask once who receives the Leads and how many each, and how to read the
  member ids, and the second-person section says her schedule needs her own id in the map. A Source leads schedule
  saved before 0.9.3 has no quota map: run the installer again to update it in place. The Source leads text now
  needs plugin 0.9.3 or later. The Sync data and Repair texts are unchanged apart from the sentence in the last point.
- A run that has no quota ends with one plain "Fix:" sentence naming the installer skill. When a person answers who
  receives the Leads in an interactive run, the invite-run skill offers once to save that answer into the installed
  Source leads schedule (the installer's new "Update the Source leads quota in place" steps), or says no schedule is
  installed and offers to install one.
- The overview skills mention the quota on the sourcing start. Tests check the manifests at 0.9.3 and that the
  Source leads schedule and the invite-run skill carry the quota.
- The three Claude schedule texts (Sync data, Source leads, Repair) now say: read each approved script file with the
  file-reading tool, one file at a time, by its path under the installed plugin's browser folder, and do not print
  them with a shell command. A scheduled run had joined several `cat` and `echo =====` commands into one line, and
  zsh failed on `=====` (it reads a word starting with `=` as a command name), so the run saw an error although
  nothing was wrong. Run the installer again to update a saved schedule. The Codex package ships no browser scripts
  and is unchanged.

### 0.9.2

- The thread script finds a conversation when the Lead's stored address is out of date. Two Repair leads
  (a polite no and a yes with an email) answered no-conversation twice because the old vanity or member id
  no longer matched what LinkedIn returns. The script now takes the Lead's name on a second placeholder line
  (`const LEAD_NAME = "";`) and the directive becomes
  `// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=<id> LEAD_NAME=<name>` (the name is the rest of
  the line, so it may hold spaces; it holds only letters, marks, digits, spaces, hyphens, apostrophes, periods and commas (0.9.3), and the gate still
  refuses every other edit). The lookup order is unchanged (identifier, then the search by name, then the
  list). When the identifier resolves nothing, or no participant of any search result carries its member URN,
  the script matches the search results by name: case and accents folded, spaces collapsed, the Lead's name
  equal to the display name, a prefix of it followed by a space or comma, or equal once a trailing
  " - ...", " | ..." or ", ..." part is dropped. Two different people with that name are ambiguous and none is
  taken, and a member-URN match always wins. A name match skips the list and reads the matched person's public
  identifier with the existing profile query; no other endpoint is added.
- New evidence fields, sealed with the rest: `matchBasis` (`identifier`, `name`, or null when no
  conversation was found), `requestedName`, `displayName` of the matched person, and `memberUrn` and
  `resolvedIdentifier` of the person matched. Mosaico accepts `matchBasis` `name` only by comparing the Lead's
  own name with `displayName` under the same rule, then repairs the Lead's address and member id from the
  thread and keeps the old ones as aliases. Not yet validated against a live account: the participant's name
  fields (`participantType.member.firstName` and `lastName`) the script reads.
- The follow-up-run, repair-run and schedule-install skills, and the Sync data and Repair schedule texts, give
  the thread directive both values (`PUBLIC_IDENTIFIER=<scriptIdentifier>` and `LEAD_NAME=<the Lead's name>`),
  and the schedule texts need plugin 0.9.2 or later. When a profile capture cannot read the profile (an
  `errorStep` and no entries), the run still passes the output to `outreach_record_connection_evidence`, so
  Mosaico records the failure; a Lead whose thread was not found twice, or whose profile capture failed twice,
  leaves the Repair queue and waits in To sort for a person (`summary.needsPerson`, with a `cause`).
- Tests: the gate rejects every other edit and every unsafe name; the thread script is run under node against
  a fake LinkedIn for the name cases (including accents, suffixes, ambiguity and a failed profile lookup);
  the Codex package is unchanged (it has no scripts) and only its Repair text names the new causes.

### 0.9.1

- The integrity seal is computed over the null-free canonical form. The claude.ai connector drops null-valued
  keys from tool arguments in transit, so a capture sealed over a form that kept nulls could never verify. In
  all five approved scripts `canonical()` now omits object keys whose value is null or undefined at every
  depth; array items stay, and a null item stays as `null`. The returned payload itself is unchanged (nulls are
  still present in the output), the digest helpers are still identical text in all five scripts, and the
  header sentence says "over the canonical JSON with null-valued keys omitted". The script gate is unaffected
  (first lines unchanged). Mosaico verifies against the payload as received and against the null-free form.

### 0.9.0

- New Repair routine. Sync data stays daily work (threads, approved follow-ups, invitations, and a small
  verification cap); a separate routine, run on demand or weekly, works the backlog behind it. Mosaico owns the
  list: `outreach_get_repair_queue` (run intent `repair`) returns the items grouped (`duplicates`,
  `addresses`, `declinedPending`, `mismatches`, `repairSuggestions`, `unverified`) in the order Mosaico sets,
  each with `leadId`, `personName`, `scriptIdentifier`, a one-line `reason` and the exact `recommendedCall`
  (the tool and arguments to pass unchanged, and `supplyAlso` for what the run adds), plus `summary` counts,
  `progress`, the cap (25 items per Repair run, counted by Mosaico from the run's own calls), `nextCursor` and
  `completion` with its valid stop reasons.
- New skill `mosaico-outreach-repair-run` (Claude): starts a run with intent `repair`, reads the queue, works
  the items in the order given with the directive form for scripts and each item's exact call, reads the queue
  again after each group, stops where Mosaico says (`run-cap-reached`, `queue-empty`, `end-of-queue`) and
  reports counts per group and what remains. It never sends a message or an invitation. A decline found while
  reading a thread is recorded with `outcome` `declined`. The Codex copy is read-only: it lists the queue and
  what a person should do.
- New tool used by the skill: `outreach_link_duplicate_leads` links two Leads of one owner that are the same
  person; Mosaico keeps the one with the richer history and drops the other as an alias.
- The schedule installer adds a third routine, "Mosaico Outreach — Repair": weekly, Sunday 10:00 AM local time
  by default (cron `0 10 * * 0`), also on demand, kept 60 minutes from Sync data and Source leads on its day.
  The Sync data text gains one sentence: when Mosaico notes `repair-recommended`, do not work the backlog, and
  end the report with "Repair needed: n items, run the Repair routine". The follow-up-run skills say the same
  and that Mosaico caps the verification list at 20 Leads per run (`deferredToRepair` counts the rest).
- Needs the Mosaico application release that adds `outreach_get_repair_queue`, `outreach_link_duplicate_leads`
  and the `repair` run intent. The scripts are unchanged. Schedule installs keep working without it, but the
  Repair routine stops at its first read until the application is updated.

### 0.8.7

- The thread script now searches by name for an opaque member id. For a first-line value that matches
  `^ACoAA[A-Za-z0-9_-]+$` it builds the member URN as before, then looks the profile up by id the way the
  connection-evidence script does (the profile query with the id as `vanityName`, accepted only when the returned
  Profile's `entityUrn` carries the same id). That Profile's first and last name are used inside the page as the search
  keywords and are never returned, so the search path runs before the list path exactly as for a vanity. Coverage rules
  are unchanged. If the by-id lookup fails, no name is known: the script uses the list path only (`searchPagesRead` 0,
  `lookup` `list` or `none`) and a miss reads `page-limit`, as in 0.8.6. The lookup alone never turns the result into
  an error. Every other script is unchanged.
- The follow-up-run, invite-run, mosaico-outreach and schedule-install skills say the first-line value for every
  per-Lead script is the Lead's `scriptIdentifier` from the Mosaico read when it is present (a member id or a public
  identifier, whatever Mosaico supplies), otherwise the part of the profile address after `/in/`. This lets the
  application hand the scripts a member id for an old vanity LinkedIn no longer resolves. The directive form is
  unchanged.
- No run depends on 0.8.7: the directive and the fields are additive, so the Sync data and Source leads schedule
  texts still say 0.8.1 or later. Update the plugin to get the name search for member ids.

### 0.8.6

- The thread, connection-evidence and sent-invitations scripts accept an opaque member id as well as a vanity.
  The first line's value (the part of the Lead's profile address after `/in/`) may be a name such as `jane-doe` or an
  id that matches `^ACoAA[A-Za-z0-9_-]+$` (the id part of `urn:li:fsd_profile:<id>`). In production 43 of 97 active
  Leads store the id form. Thread and sent-invitations build the member URN directly from an id and skip the
  profile lookup (so the thread script has no name to search by and uses the list path only). Connection-evidence
  sends the id as the profile query's `vanityName` and accepts the Profile only when its `entityUrn` carries the same id.
- A redirected vanity is accepted. When the profile lookup finds no Profile with the requested vanity but returns
  exactly one Profile entity, that one is the redirect target (an old vanity LinkedIn now sends to a new one, such as
  `zoe-milligan-conscious-learning-architecture` to `zoemilliganignitespark`). Any other answer is an error at the
  `profile` step. Sent-invitations, which had no lookup, now resolves a vanity first and matches the invitee by member
  id, or by the requested or the resolved identifier.
- Every output carries `requestedIdentifier` (as given), `resolvedIdentifier` (the response's `publicIdentifier`, or the
  opaque id) and `memberUrn`; they are null when the Profile was not resolved. The existing identifier field
  (`publicIdentifier` or `profileIdentifier`) is unchanged. The new fields are inside the integrity digest.
- A failed lookup never throws and says why: `state` is `error` with `status` (the HTTP status, or 0) and `errorStep`,
  one of `me`, `profile`, `conversations`, `messages` or `sent-invitations`. Connection-evidence gains `state`
  (`ok` or `error`) and `errorStep`, and returns no entries on an error.
- The follow-up-run and invite-run skills say the first-line value is whatever follows `/in/` (a name or an
  `ACoAA...` id) and that `requestedIdentifier`, `resolvedIdentifier` and `memberUrn` are passed on unchanged.
- The application must accept the new fields on `threadEvidence`, `sendEvidence` and `sentInvitationEvidence`.

### 0.8.5

- Thread lookup searches by name first. The thread script now finds the one-to-one conversation by LinkedIn's own
  messaging search (the call LinkedIn's search box sends, observed 6 Oct 2026: query
  `messengerConversations.737b27144cf922499202658a5345016f`, categories INBOX, SPAM and ARCHIVE, 20 a page, up to 3
  pages, each next page adding the response's `nextCursor`) using the Lead's first and last name from the profile
  response. The names are used only inside the page as the search keywords and are never returned. When the
  search finds nothing, the script falls back to the primary-inbox list paging of 0.8.3, unchanged. The search
  found a conversation the list paging missed. The result gains `lookup` (`search`, `list` or `none`) and
  `searchPagesRead` beside `pagesRead`. `coverage` is `complete` when the conversation was found by either path, or
  when the search returned at least one page without error and the list was exhausted; otherwise `page-limit`
  (including when the search failed or could not run and the list hit its cap or stalled).
- Text is normalised before it is hashed. Every approved script now carries one `normalizeText` rule, stated in
  its header so the application can mirror it, and applies it to every free-text field that leaves the page (today
  the message text of the thread script). In order: Unicode NFC; every space separator (U+00A0, U+1680,
  U+2000-U+200A, U+202F, U+205F, U+3000) becomes a plain space; zero-width characters (U+200B-U+200D, U+2060,
  U+FEFF) are removed; CRLF and CR become LF; every other C0 or C1 control character (U+0000-U+001F,
  U+007F-U+009F) except LF and TAB is removed; each run of spaces becomes one space; spaces and tabs at the end of
  each line are removed. URNs, URLs, identifiers and timestamps are never touched. The `integrity` digest is
  computed after normalisation. The browser-script gate is unchanged: the scripts' first lines and placeholders
  are as before and the run directive keeps working. The Codex skills are unchanged.

### 0.8.4

- Run directive. A run no longer retypes a long approved script into the browser javascript tool (in
  production the model retyped the 125-line thread script, changed one line, and the gate rightly refused
  it). It now sends one line as the whole script, alone or as a javascript item inside a `browser_batch`:
  `// mosaico run <script>.js [<PLACEHOLDER>=<value>]`, for example
  `// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=jane-doe`,
  `// mosaico run linkedin-recent-connections.js STOP_AT=1759400000000` or
  `// mosaico run linkedin-whoami.js`. `<script>.js` is a file in the plugin's `browser/` folder; the optional
  assignment names that script's first-line constant (`PUBLIC_IDENTIFIER` for the evidence, thread and
  sent-invitations scripts, `STOP_AT` for the connections script, none for whoami) with a value that satisfies
  the existing placeholder pattern (an identifier may be bare or in quotes). The thread and sent-invitations
  scripts need the identifier. The gate replaces the call's `text` with the approved script, its first line set,
  and allows it, using Claude Code's PreToolUse output (`hookSpecificOutput` with `hookEventName`
  `PreToolUse`, `permissionDecision` `allow` and `updatedInput`, the full replacement input; every other input
  field is kept). An invalid directive (unknown script, wrong placeholder, bad value, extra lines) is refused
  with the list of valid directives and never echoes what was sent. Word-for-word scripts are still allowed
  exactly as before and everything else that touches LinkedIn or a credential store is still refused. The Claude
  skills now tell a run to send the directive and keep word for word as the fallback. The browser scripts
  themselves are unchanged. The Sync data and Source leads schedule texts now describe the directive but still
  say 0.8.1 or later: on an older plugin the gate refuses the directive and the fallback runs the script word
  for word, so no run depends on 0.8.4. The Codex skills are unchanged.

### 0.8.3

- The thread script now reports `complete` coverage when the conversation list ends. In 0.8.2 a profile with no
  conversation read 3 pages and answered `page-limit`, because the smallest `lastActivityAt` stopped decreasing;
  but that is the end of the list (LinkedIn returns the tail again, or an empty tail, for a cursor older than every
  conversation), not a limit, and the application then wrongly blocked first follow-ups for people with no
  conversation. After each page the script keeps only the new elements (`lastActivityAt` strictly older than the
  cursor) and searches the Lead among them. The list is exhausted, coverage `complete`, when a page has no
  elements, no new elements, or fewer than 20 elements. Only reaching 8 pages with new elements still arriving
  gives `page-limit`. Query ids, paged variables, the `integrity` seal and the safety rules are unchanged. The
  Sync data schedule text is unchanged (0.8.1 or later still works); update the plugin to get the fix. Needs no
  application change.

### 0.8.2

- The thread script now reads older conversations. 0.8.1 sent the `lastUpdatedBefore` cursor to the first-page
  query, which ignores it, so a second page repeated the first and a thread that had slid off the first page was
  reported as not found. Page 1 is unchanged; pages 2 to 8 use LinkedIn's own paged conversation query
  (`messengerConversations.9501074288a12f3ae9e3c7ea243bccbf`, the call the inbox makes when it scrolls) with
  `count:20` and `lastUpdatedBefore` set to the smallest `lastActivityAt` seen so far. It stops when the Lead's
  conversation is found, when a page has no conversations (coverage `complete`), or when the cursor does not move
  or 8 pages are read (coverage `page-limit`). Only the primary inbox is searched: message requests and the Other
  tab are not. The paging call was observed on live LinkedIn on 6 Oct 2026. Output shape, coverage, `pagesRead`
  and the `integrity` seal are unchanged. The Sync data schedule text is unchanged (0.8.1 or later still works);
  update the plugin to get the fix. Needs no application change.

### 0.8.1

- The thread script pages LinkedIn's conversation list instead of reading one page. It reads up to 8 pages
  (about 160 conversations) with the `lastUpdatedBefore` cursor, stops at the first page that holds the Lead's
  one-to-one conversation, and returns `coverage` (`complete` when the conversation was found or the list was
  exhausted, `page-limit` when it stopped at 8 pages, made no progress, or failed) and `pagesRead`. A run passes
  the output unchanged; Mosaico answers `no-conversation` only when coverage is complete and
  `thread-not-found-in-window` otherwise. A Lead whose thread was not found in the window is reported as such,
  never as having no conversation, and is not read by eye unless the person asks. The cursor form follows the
  documented query pattern and is not yet validated against live LinkedIn; a response that ignores it is
  handled as `page-limit`.
- Outcome judgment and the no-pressure rule. Every thread deposit that holds a message from the Lead carries
  `outcome` (`declined`, `interested` or `neutral`), the run's judgment of the Lead's latest message under a
  written checklist; without it Mosaico answers `outcome-required` and stores nothing. A no ends the Lead:
  Mosaico moves it to Drop, discards its unsent drafts and refuses new ones (`follow-up-declined`); an
  interested Lead is marked Warm.
- Awaiting reply. Mosaico refuses a follow-up draft when the latest sent message is ours and is not the
  invitation note (`follow-up-awaiting-reply`); our own unanswered message blocks a new one.
  `connection-accepted-no-reply` now means only that the invitation note is the last message or nothing has been sent.
- Repair of unsent drafts. After it stores a thread or an outcome, Mosaico re-checks every unsent draft on the
  Lead and lists the ones it discarded as `draftsDiscarded`. When `outreach_get_follow_ups` recommends
  `repair_drafts`, a run visits each Lead in `repairSuggestions` (capture the thread, deposit with `outcome`)
  before drafting or sending anything, and the report lists the discarded drafts with their Leads and reasons.
- Integrity digests. All five approved scripts return an `integrity` field; the connections script also seals
  each page. Output goes to Mosaico exactly as returned, and Mosaico refuses an altered copy with
  `evidence-altered` (nothing stored; recommended action `recapture`: run the script again).
  `outreach_record_connection_evidence` now takes the script's whole output plus `profileUrl`, `leadId`,
  `runId` and the identity evidence.
- The Claude schedule installer's Sync data text requires plugin 0.8.1 or later, adds the outcome and
  no-pressure sentence and the unchanged-output rule, and its Step 4 report lists `draftsDiscarded` and the
  Leads whose thread was not found in the window. Reinstall or repair the Sync data schedule to pick it up.
  Codex follows the outcome, awaiting-reply and repair rules in its by-eye deposits. Needs the matching
  application release.

### 0.8.0

- A send is confirmed from LinkedIn's data, not from the screen. After the Connect click (invitations) or the
  send (follow-ups), the Claude invite-run and follow-up-run skills run an approved script for that Lead and
  pass its output unchanged to `outreach_mark_message_sent`, together with fresh `identityEvidence`.
  - Invitations: LinkedIn's profile data cannot show a pending invitation (a Lead invited on 5 October
    answered `noInvitation: null`), so pending is proven only by LinkedIn's Sent invitations list. The run
    runs the approved sent-invitations script with the Lead's public identifier after the send and passes its
    output unchanged as `sentInvitationEvidence`. Mosaico marks the invitation sent only when the Lead is on
    the list with a send time after the check before the send. A `sendEvidence` capture from the
    connection-evidence script is accepted only when it shows the person connected; any other is answered
    `send-evidence-cannot-prove`.
  - Follow-ups stay as built: the thread script output as `threadEvidence`; Mosaico marks the message sent
    only when the newest message in the thread is the approved one.
  - New approved script `browser/linkedin-sent-invitations.js`; the gate picks it up from the browser folder
    with no rule change. It calls `GET /voyager/api/relationships/sentInvitationViewsV2` and has not been
    validated against a live account yet (validated: pending).
- If Mosaico answers `send-not-confirmed`, the run does not retype the note or message: it retries the send
  once, runs the script again, and if it is still not confirmed calls `outreach_record_delivery_block` with
  `reason: cannot-message`. A run never marks a send from the screen alone unless the script cannot run, and
  then the report says so; Mosaico records that as a reading and answers `send-proof-missing` (a declared
  fallback until the next release removes it).
- Codex cannot run page scripts, so its sends stay by screen and declared as such in its report. Sync data
  is installed from Claude.
- The Claude schedule installer's Sync data text requires plugin 0.8.0 or later, names the sent-invitations
  script among the approved scripts, uses the post-send check in Steps 2 and 3 (the sent-invitations script
  for invitations, the thread script for follow-ups), and its Step 4 report counts sends confirmed from data
  versus by screen. Reinstall or repair
  the Sync data schedule to pick it up. Needs the application changes "Outreach: a send is marked only when
  LinkedIn data confirms it (w8pg)" and "Outreach: invitation send proof from LinkedIn's sent invitations list
  (w8pg, part 2)".

### 0.7.1

- The Claude schedule installer's Sync data text now reads each Lead's thread through the approved script
  `browser/linkedin-thread-messages.js`, as the follow-up-run skill has done since 0.7.0. It passes the output
  unchanged as `threadEvidence` to `outreach_deposit_conversation`; Mosaico derives direction and times. The
  by-eye deposit stays only as the fallback when the script cannot run, and the report says so. The text
  requires plugin 0.7.1 or later and its report now counts threads read from data versus by eye.
  Reinstall or repair the Sync data schedule to pick it up.

### 0.7.0

- New approved script `browser/linkedin-thread-messages.js` reads a Lead's thread from LinkedIn's own
  messaging data (query 2.4). Its first line holds the Lead's public identifier; the browser-script gate
  accepts a changed value there and nothing else. It returns `{ status, signedIn, capturedAt, state, source,
  publicIdentifier, conversationUrn, participants, messages }` with messages oldest first and only each
  message's id, delivery time, sender and text. With no conversation it says `state: "no-conversation"`; on any
  error it returns the status and empty lists and never throws. It never returns the session or CSRF token.
- The Claude follow-up-run skill runs it for each Lead and passes the output unchanged as `threadEvidence` to
  `outreach_deposit_conversation`, together with fresh `identityEvidence`. Mosaico reads the thread from that
  data: it refuses a capture it cannot trust with a named code and derives direction and time itself. The
  by-eye deposit stays only as the fallback for a run that cannot run the script, and the report says so.
  Mosaico accepts `threadEvidence` as of the application change "Outreach: conversation deposited from
  LinkedIn thread evidence"; until that is released, older runs keep depositing by eye.
- The Codex follow-up-run skill says that Codex's page-script scope cannot run the script and keeps the by-eye
  deposit, reported as such.
- The other three approved scripts are unchanged.

### 0.6.1

- The Claude follow-up-run skill submits the recent-connections snapshot page by page to
  `outreach_record_connections_snapshot`: one call per page with `runId`, `identityEvidence` (the whoami
  script is run again when its output is older than 8 minutes), `capturedAt`, `snapshotId`, `pageIndex`,
  `pageCount` and the one page unchanged. Mosaico answers `page_recorded` with any missing indexes until
  the last page, then `connections_recorded`. A run that stops half-way is finished from
  `connectionsCapture.pending`. The one-call form stays allowed for short lists. The Codex skill still
  does not capture and now says so. This contract is live in Mosaico production as of 4 October 2026.
- The schedule installer requires, and the Sync data schedule text relies on, the user-level allow rules
  `mcp__Claude_Browser__javascript_tool`, `mcp__Claude_Browser__computer` and
  `mcp__Claude_Browser__browser_batch`, because scheduled sessions ignore project-level rules. The
  "Set up a second person" steps cover the same rules.
- The approved browser scripts are unchanged.

## Public exposure boundary

Assume every file in this repository and every installed plugin file is public and inspectable.
The MCP tool names, descriptions and schemas are public contracts. All enforcement and proprietary
implementation remain on the Mosaico server.

## Outreach contract regression

Before publishing either provider plugin, verify that both Outreach skill sets reference the same
tools and that every referenced tool exists in the application registry:

```bash
python3 tests/test_outreach_tool_contract.py --app-repo ../mosaico-app
python3 tests/test_browser_script_gate.py
python3 tests/test_thread_script.py
python3 tests/test_schedule_install_skill.py
python3 tests/test_follow_up_thread_skill.py
```

## License

Copyright Mosaico Limited. See [LICENSE](LICENSE).
