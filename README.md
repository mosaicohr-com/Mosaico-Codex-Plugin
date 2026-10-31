# Mosaico assistant plugins

Public, read-only distribution repository for the official Mosaico plugins for Codex and Claude
Code.

Architecture (0.9.7). The plugins ship no Mosaico server. They contain only skills and, for Claude
Code, hooks and approved browser scripts. Every Mosaico call goes through the person's own Mosaico
connector, the one that points at production (`https://app.mosaico.one/api/mcp`) and is signed in with
their own Mosaico account. Before 0.9.7 the Claude Code plugin also bundled a second Mosaico server that
reached the same production service through its own, separate sign-in; runs could stall at that sign-in.
It is gone, so there is one door and one sign-in.

The repository intentionally contains only provider manifests and thin interaction skills. Mosaico application code, workflow state, authorization rules, credentials,
customer data and deployment configuration are not distributed here.

## Codex

Add the Git marketplace and install the plugin:

```bash
codex plugin marketplace add mosaicohr-com/Mosaico-Codex-Plugin
codex plugin add mosaico@mosaico
```

Restart Codex and begin a new conversation after installation. The Codex plugin brings no Mosaico
server, so add your own Mosaico connector in Codex, pointing at `https://app.mosaico.one/api/mcp`
(for example `codex mcp add mosaico --url https://app.mosaico.one/api/mcp`), and sign in with your own
Mosaico account when Codex asks.

## Claude Code

From Claude Code:

```text
/plugin marketplace add mosaicohr-com/Mosaico-Codex-Plugin
/plugin install mosaico@mosaico
```

Then connect the Mosaico connector in Claude's connectors (not `/mcp`): add the connector for
`https://app.mosaico.one`, sign in with your own Mosaico account, and start a new conversation. If a
Mosaico connector is already connected and signed in, there is nothing more to do. A run with no Mosaico
connector connected stops and tells you to connect it.

Always use the production connector. A connector whose address contains `amplifyapp.com`, `stage`,
`staging`, `test` or `localhost` is never used by a run.

### After a Mosaico deploy

Claude keeps a copy of the connector's tool list. After Mosaico deploys a change to a tool, that copy can
go stale: a tool argument may be refused as unknown, or a new tool may be missing. When that happens,
disconnect and reconnect the Mosaico connector in Claude's connectors, or restart Claude, then run again.
Nothing in the plugin needs updating for this. A new tool, such as `get_acting_status`, appears in Claude only
after the person disconnects and reconnects the Mosaico connector in Claude's connector settings; the
`mosaico` skill and the Follow-up skill say so when a tool they name is missing.

## Current state (0.12.3)

Plugin 0.12.3 is the thin plugin (0.10.0), plus the Mosaico page for Claude. Mosaico's Outreach know-how (the order of the work, when a run stops, how to search,
how to write, the routine texts, times and steps, and the report wording) lives on the Mosaico server and is served to
the signed-in person's run. The Outreach skills only start the run, do exactly what the step Mosaico returns says, record
the result, end the run and give Mosaico's report unchanged. What stays in the plugin is what can happen only on the
person's machine: which connector is used, the acting-session stop, the approved browser scripts and their gate, the
rule that LinkedIn cookies and sessions are never read or exported, LinkedIn warnings and captchas, the Routines Board
write and the schedule installer's machine checks. The one Outreach limit is 20 invitation sends per owner per day,
which Mosaico enforces.

## The Mosaico page (Claude only)

The Claude package carries the Mosaico page (`plugins/mosaico-claude/assets/mosaico-page.html`), a claude.ai artifact that only shows screens.
Every rule and every piece of know-how stays on the Mosaico server. Run `/mosaico:mosaico-page-install` once: it publishes one copy for the
person with the Artifact tool, titled "Mosaico", keeps the link in `~/.claude/mosaico-page-url`, and on a later run (after a plugin update)
republishes to the same link, never a new one. The page calls the connector named `mosaico`, so the person's Mosaico connector must have that
name. The Codex package cannot publish pages and does not get the page or the skill.

The page's background video is not shipped: its address points at a file in Mosaico's own artifact, so a copy keeps the static background.

## Outreach workflows

Use `$mosaico:mosaico-outreach` in Codex or `/mosaico:mosaico-outreach` in Claude Code to choose an action.

- **Send invitations** sends the approved invitations, checks connections and writes or rewrites invitation drafts as Mosaico
  orders. **Follow-up** reads threads, writes follow-up drafts only, sends approved follow-ups and makes the repairs Mosaico
  lists. **Withdraw stale invitations** withdraws what Mosaico lists. **Load leads** loads the Leads a member was given;
  it finds none on LinkedIn. Agents and Leads have their own management skills.
- The schedule installer (Claude) reads `outreach_get_routine_setup`, saves each routine's text, name and default schedule
  exactly as Mosaico returns them, records each with `outreach_record_routine_schedule` and the `catalogueVersion`, and offers
  to remove a routine Mosaico retired. It publishes the person's Routines Board once. Before installing it checks that a
  production Mosaico connector is connected, that no non-production Mosaico server is configured, that
  `~/.claude/settings.json` allows the three browser tools scheduled sessions need (`mcp__Claude_Browser__javascript_tool`,
  `mcp__Claude_Browser__computer` and `mcp__Claude_Browser__browser_batch`) and that no stale `mosaico-outreach-*` skill copies
  or old Codex automations exist. Codex installs no routine: every routine needs the approved captures, which only
  Claude's built-in browser pane can run.
- A saved schedule holds only the text Mosaico returned, which names the skill and its routine section, so the procedure is
  always the one Mosaico serves. A run on a plugin or server that does not match stops and says both must be updated.
- The colleague check and the other approved scripts under `browser/` are unchanged; the gate still refuses any other script
  that touches LinkedIn or a credential store.

## Set up a second person

A colleague sets up her own schedules on her own Mac:

1. Install the Claude desktop app on her Mac, with the Mosaico plugin from the marketplace, version 0.6.1
   or later.
2. In her own Claude, connect the Mosaico connector for `https://app.mosaico.one` in Claude's connectors
   (not `/mcp`) and sign it in as her own Mosaico account. The plugin brings no Mosaico server, so nothing
   works until she does. She must be an active member of the organisation; an Owner or Admin can check in
   Outreach, Agent tab.
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
6. Run the schedule installer. It installs her Send invitations, Follow-up, Withdraw stale invitations and Routines report schedules and her own Routines Board (and retires an older Sync data task), and Load leads (which loads the Leads she
   is given into her Agents), and deletes the old Source leads tasks.

Each person's Send invitations, Follow-up and Withdraw stale invitations schedules run on that person's own Mac, in that person's own pane, and sends only
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
- `plugins/mosaico-claude/browser/linkedin-salesnav-colleague-connection.js` is the colleague-connection script (0.9.5): it takes the candidate's public identifier on its first line and the colleague's registered public identifier on its second (Mosaico supplies it; the run never chooses it), and asks Sales Navigator's "Connections of" filter whether the candidate is already one of the colleague's connections. It runs only in the signed-in Sales Navigator page (any `https://www.linkedin.com/sales/` page) in Claude's built-in browser pane, calls only LinkedIn's profile query, the filter's typeahead and the lead search, and returns only `{ status, signedIn, capturedAt, state, colleague, candidate, filter, found, resultsTotal, pagesRead, complete, controlTotal, visibility, unreadableRows }` (0.9.11 added the last four; each person as `{ input, salesNavId, memberId }`), where `state` is `ok`, `colleague-not-resolved`, `candidate-not-resolved` or `error`. A run passes the output unchanged as `colleagueConnectionEvidence` to `outreach_save_lead`; Mosaico decides whether to skip the candidate. People are found by numeric member id (decoded from LinkedIn's ids), never by name. `found: false` alone is never proof that two people are not connected: from 0.9.11 the four proof fields let Mosaico decide whether a not-found is a proven negative.
- Redirect retry (0.9.16): the connection-evidence script asks the profile query once more, with the page's own `/in/<slug>/`, when the
  first call failed (404, 410, or a 2xx with no usable profile) and the page followed a redirect to a different slug. It never retries a
  refusal, a rate limit, a server error or a dropped call, never more than once, and never swaps identifiers silently:
  `requestedIdentifier` stays what the run asked for and `resolvedIdentifier` is what LinkedIn named, so Mosaico can keep the old
  identifier as an alias.
- Gone profiles (0.9.17): the connection-evidence script's `status` is the HTTP status of LinkedIn's profile data call, which can answer
  200 with no profile for an address whose page shows LinkedIn's not-found page, so the application counted a first failure instead of
  giving up. When no profile was resolved, the data call answered 2xx and the page the run opened is LinkedIn's not-found page (its
  document title says the page or profile was not found, or its address is `/404`), the script reports `status` 404; a 410 stays 410. A
  first call's 404 or 410 is also never replaced by a redirect retry that finds no profile either. Only `document.title` and
  `location.pathname` are read for this. A refusal, a rate limit, a server error or a dropped call is reported as it is. The not-found
  marker has been tested against a fake page only, not yet against a live LinkedIn page.
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

### 0.12.3

Pairs with the Mosaico server release 20261101a (main-v2 `5d7b9420f`). Page asset refresh only.

- Methodology Overview shows real counts (`get_methodology_view` with `organisation_overview`).
- Flows can attach, read and remove step files (`add_step_file`, `get_step_file`, `remove_step_file`).
- The page now carries 64 tools (was 22).

### 0.12.2

Pairs with the Mosaico server release 20261030f (main-v2 `2f1e3abdd`). Page asset refresh only.

- The Brief page opens in two steps, top bar first.

### 0.12.1

Pairs with the Mosaico server release 20261030e (main-v2 `ffb1cc9c2`). Page asset refresh and one installer change.

- The page saves charts through Claude's download route.
- The schedule installer reinstalls routine times that have drifted.

### 0.12.0

Pairs with the Mosaico server release 20261030c (PR 2233, catalogue `2026-10-30.1`). Not additive: a routine is renamed and an argument is removed. Run the installer again after updating.

- Load leads replaces Source leads. It reads the Leads the person gave, loads them in pages with `outreach_load_leads`, and reports placed, skipped and rejected rows. It starts no run and opens no LinkedIn page. One routine, daily 05:00, installed for everyone.
- Held Leads are skipped with their reason, never re-sent. `acknowledgeProfileOnOtherOwner` and `sourcingScope` are gone from the skills.
- The installer deletes the old "Mosaico Outreach — Source leads (own)" and "(colleagues)" scheduled tasks that the setup read lists as `retiredRoutines`.
- The Routines Board has one `load-leads` entry in place of the two source entries.

### 0.11.3

Pairs with the Mosaico server release 20261030b (main-v2 `451142180`, live 2026-10-30). Page asset refresh only; no skill changes.

- Settings → Integrations on the page: see connected apps and revoke one. Connecting Claude links to the web.
- The page now declares 22 tools (adds `get_integrations_view` and `revoke_integration_grant`).
- `assets/mosaico-page.html`, `mosaico-page.capabilities.json` and `mosaico-page.source.json` (commit, release, date, checksums) are updated.

### 0.11.2

Pairs with the Mosaico server release 20261030a (main-v2 `acd69af6d`, live 2026-10-30). Page asset refresh only; no skill changes.

- Installed components show no Install button on the page.
- The reseller Overview shows totals.
- Managers can send tasks back.
- Claude never completes a task.
- `assets/mosaico-page.html`, `mosaico-page.capabilities.json` and `mosaico-page.source.json` (commit, release, date, checksums) are updated.

### 0.11.1

Pairs with the Mosaico server release 20261029c (main-v2 `3ce5886e0`, live 2026-10-29). Page asset refresh only; no skill changes.

- The Mosaico page shows clear reasons when a reseller screen is refused.
- The reseller Owner and Admin roles follow the organisation.
- The page now declares 20 tools (adds `create_organization_users`, live on the server since 20261029a).
- `assets/mosaico-page.html`, `mosaico-page.capabilities.json` and `mosaico-page.source.json` (commit, release, date, checksums) are updated.

### 0.11.0

Pairs with the Mosaico server release 20261029a (main-v2 `cd87c125a`, live 2026-10-29): the page calls 19 tools that are live since then, so
this plugin can ship any time after. Skills and one more page asset only: the plugin bundles no Mosaico server, address or token.

- **New skill `mosaico-page-install` (Claude only).** Publishes `assets/mosaico-page.html` unchanged, once per person, with the capabilities of
  `assets/mosaico-page.capabilities.json`; republishes to the same link on later runs. It says plainly when Claude has no Artifact tool or the
  connector is not named `mosaico`, and tells the person to reconnect Mosaico when the page says a tool is missing.
- **Assets.** `mosaico-page.html`, `mosaico-page.capabilities.json` and `mosaico-page.source.json` (commit, release, date and checksums).
- The Codex package does not get the skill or the page.
- Tests: `tests/test_mosaico_page_asset.py`. Version stamps in the other skills moved to 0.11.0; the server still asks for 0.10.0 or later.

### 0.10.0

Needs the Mosaico server release that ships stage-v2 pull requests #2168 to #2182 and #2184 (the step block, server-only run guidance, the rule
audit, the server-only routine catalogue and `outreach_get_routine_setup`, trimmed tool descriptions with run-scoped step guidance, one
limit only, held-back items, the retired Repair routine, and the review window that works out the routine times). Do not tag, publish or install this plugin before that release is live on
main-v2. Plugin and server release together. Skills only: the plugin bundles no Mosaico server, address or token.

- **Thin Outreach skills (both packages).** Mosaico-outreach, invite-run, follow-up-run, schedule-install, agent-management and
  lead-management now say what the skill is for, how to start a run, to follow the step Mosaico returns (`step.call`,
  `step.agentInstructions`, `step.guidance`), to end the run and to give `report.lines` and `report.sections` unchanged, how to stop
  on a blocker or refusal (`recommendedAction`), and only the rules the server cannot enforce. The Claude package's Outreach skills
  fell from about 38,700 words (41,500 with the Repair skill) to about 3,500.
- **Schedule installer.** Routines, texts, times and steps come only from `outreach_get_routine_setup`. Each saved routine is recorded
  with `outreach_record_routine_schedule` and the setup's `catalogueVersion`. A retired routine's scheduled task is offered for removal
  (`remove_retired_routines`). If the server has no `outreach_get_routine_setup`, no step block or an older catalogue than this plugin
  expects (`2026-10-30.1`), the skills stop and say the plugin and server must be updated together.
- **Review window (restored).** The owner's design that the routine times follow the person's evening review was dropped from the thin
  installer by mistake. Mosaico (server pull request #2184) now works out the times: the installer asks the person once when they review
  and approve drafts, passes the answer to `outreach_get_routine_setup` as `reviewWindow`, saves exactly the times returned, reads back
  the server's `readback` lines and records the window with each routine. It never asks when Mosaico already knows the window. No time
  or rule is written in the skill. The catalogue it expects is `2026-10-30.1`.
- **Removed.** The Repair skill (`mosaico-outreach-repair-run`) in both packages and every mention of the Repair routine and
  `outreach_get_repair_queue`; the verify, draft, check, withdraw, colleague-check and sourcing caps; the weekly invitation ceiling;
  the 24-hour rules (the Routines report look-back, the capture age); the routine texts, default times and step lists that were
  hard-coded in the installer and the run skills; the sequencing recipes, judgement guidance, drafting style and report wording that the
  server now serves; the rule that a skill works only on the signed-in person's own records. Outreach records are company-owned: an
  Owner or Admin reads and writes any member's records. The only limit is 20 invitation sends per owner per day.
- **Kept, unchanged.** The approved browser scripts, the browser-script gate hook and the Routines Board page. The client-only rules
  stay in the skills or the gate: the production connector only, no connector means stop, never end an acting session, run approved scripts
  only through the one-line directive, pass script output unchanged, never read or export a LinkedIn cookie, session or token, captures in
  Claude's built-in browser pane only, the email prompt is recorded as `email-required`, a withdrawal is recorded only after LinkedIn
  shows the invitation gone, a LinkedIn warning or captcha stops the run, the Routines Board write never blocks the report, contradictory
  state goes to the incident tool, Agent and Lead changes are confirmed with the person, the installer's machine checks, no overlapping
  browser schedules and thin schedule texts.
- **Tests.** `tests/test_thin_outreach_skills.py` pins the thin contract in both packages, the routine section names the server's routine texts
  point at, the absence of the moved know-how and Repair, and this release note. `tests/test_thin_skill_budget.py` keeps the Claude Outreach skills
  under the word budget and free of any limit but 20 invitation sends per owner per day, any 24-hour rule and Repair.
  `tests/test_client_only_rules.py` checks that every client-only rule of the server's rule audit
  (`tests/fixtures/outreach-client-only-rules.json`, copied from mosaico `feature/outreach-review-window` fe788273d9cd, PR 2184, which removes R107) is still stated in a thin skill or enforced
  by the gate hook. `tests/test_thin_schedule_install_skill.py` pins that the installer hard-codes no cron, time, title or routine text.
  `tests/test_routines_board_asset.py` pins the board page's document shape, now also written in its header comment.
  `tests/test_outreach_tool_contract.py --app-repo <stage-v2 export>` checks every tool, step field, version and routine section against the
  server. The script, gate and integrity tests are unchanged.

### 0.9.26

Needs the Mosaico release that adds `outreach_record_routine_schedule` and the Routines section of the Agent tab (the server release named in
mosaicohr-com/mosaico pull request 2158). Do not tag, publish or install this plugin before that release is live in production. Skills only:
the plugin bundles no Mosaico server, address or token.

- **The installer reports the schedules it sets.** The schedule-install skill (Claude) calls `outreach_record_routine_schedule` once per
  routine after it creates, updates, pauses or resumes a scheduled task and has read it back, with the time zone, the days of the week, the
  times of day and the paused state the task actually saved, and the plugin version. It says in its report which routines were recorded and
  which were not. Mosaico shows them in Outreach, Agent tab, Routines, with each routine's last run from its own run records. A refused or
  unavailable tool never undoes a schedule.
- **Codex.** The Codex schedule-install skill does the same for the one schedule it installs, Source leads.
- Nothing else changed: no routine text, stamp, cron, board or default time moved.

### 0.9.25

Needs the Mosaico release 20261026a and b (both live in production). Skills only: the plugin bundles no Mosaico server, address or token.

- **Load already-sourced Leads.** The Lead-management skill (both packages) loads a CSV, sheet or list of Leads the person already sourced
  with `outreach_load_leads`, once the person names the Agent. It maps columns to `name`, `linkedInProfileUrl`, `company`, `jobTitle` and
  `notes`, sends pages of at most 200 rows with no run, and after each page reports the placed rows (with their days), the skipped rows
  (`duplicate-own`, `duplicate-in-batch`, `held-by-other-owner`) and the rejected rows (`invalid-row`, `invalid-url`, `agent-days-full`,
  `agent-not-sourceable`, `write-failed`) as Mosaico returned them. It follows `nextAction` (`load_more`, `review_skipped`, `none`) and never
  sends a rejected row again with changed data without asking. Mosaico chooses the days and checks every row; the skill adds no rules.
- **Ask for a new draft.** The same skill calls `outreach_request_redraft` with `leadId` (and `messageId` for one Message) when the person
  asks for a draft to be rewritten. The Message returns to Draft with the reason `person-requested`; the next Send invitations run
  (invitations) or Follow-up run (follow-ups) rewrites it. Nothing is rewritten in place.
- **Rewrite reasons.** The invite-run and follow-up-run skills list `person-requested` beside `checklist-changed` and `instructions-changed`.
  Nothing else changed in them; no schedule, board or installer changes.

### 0.9.24

Needs the Mosaico release that ships PRs 2053, 2057 and 2058; not yet promoted. Do not tag, publish or install this plugin before that
release is live on main-v2. Skills and one page asset only: the plugin bundles no Mosaico server, address or token.

- **Rewrite work.** A draft returned to Draft by an Agent change (reasons `checklist-changed` or `instructions-changed`, or a draft
  never approved whose stored review no longer holds) is rewrite work, ordered by the application. The Send invitations work list has a
  new phase and step `rewrite`, after send and before check, with the action `rewrite_returned_invitation_draft`; `sendRun.rewrites`
  (up to 50 items: `leadId`, `name`, `messageId`, `kind`, `day`, `agentId`, `agentName`, `body`, `reason`, `basis`, `returnedAt`,
  `recommendedCall`), `sendRun.next.rewrite`, `sendRun.remaining.rewrite`, `sendRun.rewriteCount` and `sendRun.rewritesThisRun`. Rewrites
  share the 100-draft limit with new drafts and go first; what is left waits with the reason `rewrite-limit-reached`. The step covers every
  scheduled day. The routine rewrites the body to the Agent's current instructions and checklist and records it with the existing
  `messageId`; it never approves. The Follow-up queue has a new stage `rewrite-draft` (`nextStep` `rewrite_follow_up_draft`) between
  `send-approved` and `draft`, with `rewriteDraft`, a `recommendedCall` that names the `messageId`, a `readConversationCall` and
  `counts.rewrite`: the routine reads that thread first (the invitation actually sent is in it), then writes the first message without
  repeating the invitation's words, per the Agent's rules, and records it with the existing `messageId`. `outreach_record_message` with an
  existing `messageId` replaces the body, keeps the kind, the day and `sendNotBefore`, clears the returned flag and leaves the status
  Draft; the checklist review still applies and a second unsent draft is impossible. Reports name the rewritten drafts (count, names,
  days) and any `rewrite-limit-reached` wait. Both packages carry the invitation side; the follow-up side is in the Claude routine and
  the Codex queue notes.
- **Routines Board.** Every routine section (Source leads, Send invitations, Follow-up, Withdraw stale invitations) ends with the step
  "Record the run on the Routines Board". If the schedule text carries the line `routines board: https://claude.ai/artifact/<id>`, the run
  loads `ArtifactData` (ToolSearch `select:ArtifactData`) and writes one batch with that url: a `runs` document (id = the run's `runId`;
  `routine`, `startedAt`, `endedAt`, `outcome`, `headline`, `counts`, `notes`, `reportText`), `actions` documents for what the person
  must do (`act-<slug>-<yyyymmdd>`), `issues` documents for defects and blockers (`iss-<slug>`, `firstSeenAt` kept) and `meta/board`
  (`lastUpdatedAt`, `lastUpdatedBy`, any `states` kept). Existing documents are read first and written with their version. With no board
  line the step is skipped silently; a failed write is one line in the report and never blocks it.
- **Routines report.** A new thin task "Mosaico Outreach — Routines report" (`45 6,23 * * *`) with a new section "Routines report
  routine" in the follow-up-run skill reads each routine's latest scheduled run and writes the board the same way. It is the fallback
  when a routine could not write. It uses no browser and no Mosaico connector.
- **Installer.** It publishes the page `plugins/mosaico-claude/assets/routines-board.html` (Claude package only; the Codex package does
  not get it) once per person with the Artifact tool (title "Outreach Routines Board", icon `dashboard`, the `db` capability with
  everyone reading and only Editors and the Owner writing, and `user`), reuses the address found on an existing task otherwise, appends
  the line `routines board: <url>` to every routine's thin text (its own paragraph) and reads it back. The thin texts move to the
  0.9.24 stamp. The installer asks once for the person's review window (default 7:00 to 10:30 PM) and shifts the two Follow-up times when
  it differs.
- **New default times, every day.** Follow-up `45 18,22 * * *` (6:45 PM and 10:45 PM), Withdraw stale invitations `30 23 * * *`
  (11:30 PM, installed paused until the person has tested it), Source leads (own) `0 0,3 * * *`, Source leads (colleagues)
  `30 1,4 * * *`, Send invitations `0 6 * * *`, Routines report `45 6,23 * * *`, Repair unchanged. Why: the person reviews and approves
  drafts between 7:00 and 10:30 PM; the 6:45 PM Follow-up drafts for that review; the 10:45 PM one sends what was approved; Send
  invitations sends in the morning and drafts the coming days. The spacing rule is now: no two LinkedIn starts closer than 30 minutes, and
  90 minutes between the two sourcing lanes.
- Tests: `tests/test_schedule_install_skill.py` and `tests/test_rewrite_board_skill.py` (new) cover the texts, sections, times, board line,
  installer behaviour and version stamp; `tests/test_outreach_tool_contract.py` reads the rewrite fields from the application source.

### 0.9.23

Needs the Mosaico server release 20261019d (production build 349, live since 2026-10-19). The release carries
mosaicohr-com/mosaico#2011 and #2013 ("Install only"): the connector's catalogue, approval and example tools are gone and one
tool replaces them. Do not publish or install this plugin before that release is live on main-v2. Skills only: the plugin bundles
no Mosaico server, address or token. This entry supersedes the 0.9.21 bullets on approving a conversion and on the reseller
catalogue and a customer's examples.

- **Added tool: `install_methodology_component`** (the `mosaico` skill and the convert skill, both packages). It installs a copy of
  one published Flow or Domain of a conversion into one organisation, as the Install button does. Arguments: `projectId`,
  `componentKind` (`flow` or `domain`), `componentKey` and `targetOrganizationId` (the person's own organisation, or a customer of
  their reseller). It previews first, then installs when called again with `mode: "execute"` and the `confirmationToken`; the host asks
  the person once. A second install into the same organisation replaces the earlier copy in place when nobody has progress on it,
  and otherwise makes a new copy and keeps the old one; the preview says which. Only an Owner or Admin can install, and it needs a
  subscription. Mosaico refuses with a code and one sentence (`component_not_published` with its warning count,
  `analysis_not_complete`, `not_compilable`, `tenant_access_denied`, `subscription_required`). While Claude works as a member of a
  customer, only that member's organisation may be the target.
- **Project status carries the components.** `get_methodology_project_status` now lists, for every component, its `state`
  (`draft` or `published`), its `warnings` count, its `installs` (`organizationId`, `organizationName`, `installedAt`, `by`,
  `changedSinceInstall`), `allowedActions` and one `recommendedAction` (`fix_warnings`, `install_component`, `none`,
  `finish_analysis` or `resolve_in_app`). The status action `install_component` replaces `approve_conversion` and
  `publish_component_example`.
- **The flow is now convert, fix warnings, install.** The convert skill (both packages) no longer approves or publishes anything:
  a component with no warnings is published, and Claude installs it only when the person asks. The conversion-run skill still never
  installs, and now tells the person to review the draft in the Mosaico app.
- **No more catalogue.** There is no Approve, no Publish, no Private or Public setting, no hide or show for one customer, no
  per-customer availability, no customer Examples tab and no seeded library. Customers see what the reseller installed; a customer
  installs its own published components from the Methodology components tab.
- **Removed tools (13):** `approve_methodology_conversion`, `publish_approved_component_example`, `publish_private_reseller_example`,
  `get_private_reseller_catalogue`, `get_private_reseller_example_delivery`, `advance_private_reseller_example_delivery`,
  `get_approved_components_for_customer`, `set_approved_component_availability`, `install_approved_domain_example`,
  `list_example_catalogue`, `install_flow_example`, `install_domain_example` and `install_capability_example`. The status actions
  `approve_conversion` and `publish_component_example` are gone too. No skill names any of them.
- A missing tool: Claude keeps its old tool list until the Mosaico connector is disconnected and reconnected in Claude's connector
  settings, so `install_methodology_component` appears only after that.
- `tests/test_connector_acting_skill.py` pins the new wording in both packages, that no packaged file names a removed tool and,
  with `--app-repo`, that the application registers the new tool with these arguments and none of the removed ones. The version pins
  in the other tests move to 0.9.23.

### 0.9.22

Needs the Mosaico server release 20261017a (promotion mosaicohr-com/mosaico#1971, stage-v2 to main-v2; main-v2 merge commit
4285416fd; production build 340, green on 2026-10-17), which is live. The release carries mosaicohr-com/mosaico#1965 (no timer, no start limit, no
reason), #1966 (ending a session stops the task), #1967 (a plain sentence in the audit log), #1968 (an exact replica of the member)
and #1969 (a live sessions list in the reseller console). The version was bumped to 0.9.22 after the
production build was green. Skills only: the plugin bundles no Mosaico server, address or token. This entry supersedes the
"Connector acting" and "After acting ends" bullets of 0.9.21 below.

- **Connector acting has no timer** (the `mosaico` skill, both packages). A session as a member ends only when the person ends it
  (End in the web console) or signs out; there is no "30 minutes", and `get_acting_status` no longer returns `endsAt` or
  `secondsRemaining` (it returns `startedAt`). Every result ends with "Working as <member> (<role>) in <customer> since <time> UTC;
  signed in as <operator>."
- **An exact replica of the member.** Working as a member copies that member's permissions exactly and adds nothing. Billing is
  reachable only when working as the Owner. Progress in the member's name is allowed as the member could do it, and Mosaico logs it
  under both names. Mosaico refuses the reseller tools while working as a member: "Reseller tools are not available while your
  connector is working as a member of a customer, because the member is not a reseller. End the session first."
- **When the session ended, the task stops** (the `mosaico` skill and the six Outreach skills, both packages). This replaces "repeat
  the call once". Mosaico refuses the next call once with a sentence that begins "Your session as" and ends "so the task stopped and
  this call did not run: tell the person, and do not carry on as yourself." Claude stops, tells the person exactly that, does not
  repeat the call and does not continue as the operator until the person gives a new instruction. `ping`, `get_acting_status` and
  `stop_acting` still run and clear the refusal; for an ended session the one recommended action is
  `tell_the_person_the_task_stopped`.
- **Kept:** Outreach and incident tools are still refused while acting; the connector refresh note; approving a conversion needs a
  subscription.
- `tests/test_connector_acting_skill.py` pins the new wording in both packages and, with `--app-repo`, that the sentences are the
  ones the application has at main-v2 4285416fd.

### 0.9.21

Requires the Mosaico server release 20261015a (promotion mosaicohr-com/mosaico#1947, stage-v2 to main-v2; main-v2 merge commit
bebbbbe06; production build 334 green on 2026-10-15), which is live. The release carries mosaicohr-com/mosaico#1937 (every action
taken while acting is recorded with both identities), #1940 and #1941 (a reseller operator's own Claude connector can act as a
member of a customer organisation, started in the web console, with the tools `get_acting_status` and `stop_acting`) and #1942
(the console tells Claude connections apart, `ping` clears the ended notice, and approving a Methodology conversion through Claude
needs a subscription and allowance). The catalogue, install and people tools named below were already live on main-v2 before this
release; this version teaches the skills to use them. Skills only: the plugin bundles no Mosaico server, address or token.

- **Connector acting** (the `mosaico` skill, both packages). A reseller operator can make their own Claude connector act as a
  member of a customer organisation for 30 minutes (no timer since server release 20261017a; see 0.9.22). Only the operator's click in the Mosaico web console starts it; no tool does, so
  the skill never tries. `get_acting_status` (no arguments, always callable) returns `phase` (`not-acting`, `acting` or `ended`), the
  `operator`, `connector.reference` (the short reference the web console lists beside each connected Claude), the `member`, the
  `customer`, `endsAt` and `secondsRemaining`, `blockers`, `allowedActions` and one `recommendedAction`; the skill does what
  `recommendedAction` says. `stop_acting` (no arguments, no confirmation, always works) ends the session so the next call runs as the
  person in their own organisation. While acting, every call runs as the member and every result ends with a line that says who; the
  skill tells the person who they are acting as before it changes anything and in its final report.
- **An Outreach run stops while the connector is acting** (invite-run, follow-up-run, repair-run, the Outreach overview, Agent
  management and Lead management, both packages). Mosaico refuses every Outreach and incident call while acting with the sentence
  "Outreach and incident tools are not available while your connector is acting as a member of another organisation. End the session
  first." The routine stops, reports that sentence word for word with the step it reached, and does not try again, work round it or end
  the session itself. The model sees only the sentence: Mosaico records the codes `CONNECTOR_ACTING_OPERATOR_ONLY`,
  `CONNECTOR_ACTING_UNCLASSIFIED`, `CONNECTOR_ACTING_ENDED` and `CONNECTOR_ACTING_UNAVAILABLE` on its audit trail, so the skills match
  the sentence and never a code.
- **After acting ends, repeat the call once** (the same sections; superseded by the 0.9.22 entry above: the task now stops). When the session ends by itself or in the web console, Mosaico
  refuses the next call once with "Your session acting as <member> in <customer> ended at <time> UTC. This call did not run. Repeat it;
  it will run as you in <organisation>." Repeat that same call once, with the same arguments; it then runs as the person in their own
  organisation and the run goes on. If Mosaico says it could not confirm whether the connector is still acting, the skill reads
  `get_acting_status` (or ends the session with `stop_acting` if the person asks).
- **Changes need a subscription** (the `mosaico` skill and the convert skill; the approval part is superseded by 0.9.23: `install_methodology_component` replaces approving). A change made through the connector needs an active
  subscription with AI allowance left (a few tools that only stop or carry on a run Mosaico already started, and the two acting tools,
  are exempt); without a subscription Claude cannot change anything. The skills quote Mosaico's three
  sentences (no subscription, no remaining allowance, another call settling the allowance) and tell the person plainly that nothing was
  changed. `approve_methodology_conversion` is no longer allowance-exempt (mosaicohr-com/mosaico#1942): the convert skill (both
  packages) says that approving is still the person's decision, that Claude calls it only after the person has reviewed the draft and
  asks for the install (preview, then execute), and that without a subscription Mosaico refuses it, nothing is approved, and the person
  can approve the conversion with the Install button in the Mosaico web app. The conversion-run skill still never approves.
- **A refusal code the conversion-run skill was missing.** Mosaico has refused an incomplete domain answer with `response_incomplete`
  since 2026-10-12. The conversion-run skill (both packages) now lists it with Mosaico's sentence, "Your answer leaves out capabilities
  this part names. Add each one listed, using only what the document states, and send the whole object again." The lint test caught the
  gap against the live server commit; its word cap for that skill moves from 1400 to 1430 for the 26 added words.
- **The reseller catalogue and a customer's examples** (the `mosaico` skill; superseded by 0.9.23: these tools were removed). `publish_approved_component_example` publishes one
  approved component by reference (`projectId`, `componentKind`, `componentKey`, `visibility`, private by default).
  `get_approved_components_for_customer` and `set_approved_component_availability` read and switch a private domain for one customer; a
  flow cannot be switched this way (`flow_not_switchable`: publish it, then enable the published example with
  `advance_private_reseller_example_delivery`) and neither can a capability (`capability_not_switchable`). For the person's own
  organisation, `list_example_catalogue` reads what the Examples tabs show, and `install_flow_example`, `install_domain_example`,
  `install_capability_example` and `install_approved_domain_example` install only the example the person names; the skill says what a
  second install does.
- **People setup** (the `mosaico` skill). `list_teams`, `create_team`, `batch_assign_positions`, `assign_person_to_flow` and
  `set_person_task_due_date`, with the warning that removing a person from a flow deletes the work they recorded there.
- **A missing tool.** The `mosaico` skill (Claude) and the Follow-up skill (Claude) tell the person that Claude keeps its old tool list
  until the Mosaico connector is disconnected and reconnected in Claude's connector settings. The Codex skills keep their shorter
  wording.
- **No schedule text changes.** The saved schedule texts name the installed skills and their routine sections, so updating the plugin
  is what changes a run. Their minimum versions are unchanged.
- `tests/test_connector_acting_skill.py` pins the wording in both packages and, with `--app-repo`, that the sentences, tools, arguments
  and the allowance rule are the ones the application has at the release commit. The version pins in the other tests move to 0.9.21.

### 0.9.20

Requires the Mosaico server release 20261014b (carrying mosaicohr-com/mosaico#1938, "a stuck send never stops the run"; the release
also carries mosaicohr-com/mosaico#1935 and #1936, already on stage), on top of release 20261014a (0.9.19, mosaicohr-com/mosaico#1933).
Do not publish or install this plugin before that release is live on main-v2: the plugin is published only after 20261014b is on
production main-v2. The Send invitations run of this release relies on what #1938 added: `sendRun` on the answers to
`outreach_mark_message_sent` and `outreach_record_delivery_block` in a send run, `sendRun.movedThisRun` and `sendRun.movedCount`
(on `outreach_get_day`, and on the accepted `outreach_end_run`), the waiting reasons `send-refused-twice-this-run` and `no-open-day`,
the note `lead-skipped-this-run`, the state `invite-already-pending` (with `invitationSentAt`) on `outreach_mark_message_sent`, and
the delivery block reason `email-required` on `outreach_record_delivery_block`.

- **A send Mosaico refuses twice is skipped by Mosaico** (invite-run skill, both packages, "Send approved invitations" and the Claude
  "Send invitations routine"). The answer to `outreach_mark_message_sent` now carries `sendRun`. After a refused send the skill follows
  the answer's recommendation; once Mosaico has refused a send twice for the same Lead in the run it skips the Lead itself: the answer
  carries the note `lead-skipped-this-run`, lists the Lead under `sendRun.skippedThisRun` (step `send`) and `sendRun.waiting` (reason
  `send-refused-twice-this-run`), and its recommendation is the work list's. The skill does not try that Lead again and goes on with
  `sendRun.next`. The skill no longer records `cannot-message` after a second `send-not-confirmed`: Mosaico skips the Lead instead of the
  run dropping it.
- **An earlier invitation still pending is not an error.** When LinkedIn's Sent invitations list shows an older invitation to the same
  person still pending, `outreach_mark_message_sent` answers the state `invite-already-pending`; Mosaico itself recorded the invitation as
  the delivery block `invite-pending` with LinkedIn's time for the earlier one (`invitationSentAt`). The skill reports it and goes on with
  `sendRun.next`; it never records `invite-pending` itself.
- **LinkedIn asks for the person's email: `email-required`.** The skill records `outreach_record_delivery_block` with the new reason
  `email-required`, sends nothing and goes on with `sendRun.next`. Mosaico keeps the Lead (it stays active) and puts it in Outreach
  To sort for the person. `cannot-message` still drops the Lead and is never used for an email request.
- **Mosaico moves the Leads of a missed day.** When a Send invitations run is issued, Mosaico itself moves the Leads left on a past day
  to open days; the run lists them in `sendRun.movedThisRun` (`leadId`, `name`, `fromDay`, `toDay`; `sendRun.movedCount` is the full
  figure). A Lead with no open day waits with the reason `no-open-day`. The skill does nothing for either.
- **The answer to a send and to a recorded delivery block carries `sendRun`.** In 0.9.19 the run reread the day after them; from this
  release it follows `sendRun.next` and rereads only when an answer says `sendRun` is unavailable.
- **The report** gives, from Mosaico's answers and not from memory, the Leads Mosaico moved (`sendRun.movedThisRun`, each with the day it
  moved from and the day it moved to), the sends Mosaico skipped (`sendRun.skippedThisRun`) and the Leads that waited
  (`sendRun.waiting`) with their reasons, the Leads recorded as `email-required`, and the invitations answered `invite-already-pending`.
- **Codex.** The Codex invite-run skill carries the same wording for the cases it can reach. It still cannot confirm a send from
  LinkedIn's data, so `invite-already-pending` is named there for completeness only.
- **Unchanged from 0.9.19:** the ordered work list (send, check, draft), the limits Mosaico sets and counts (`checkLimit`, `draftLimit`),
  the refused end (`send-run-open`) and the waiting reasons of that release (`in-to-sort`, `no-agent`, `agent-missing`,
  `no-profile-address`, `profile-capture-failed`, `check-limit-reached`, `draft-limit-reached` and `refused-twice-this-run`).
- **No schedule text changes.** The Send invitations text stays at 0.9.15: it names the "Send invitations routine" section of the
  installed plugin, so the plugin update is what changes the run. Update the plugin on every machine that runs the Send invitations
  schedule. The Follow-up (0.9.18), Withdraw stale invitations (0.9.15), Source leads (0.9.13) and Repair (0.9.6) texts are unchanged.
- `tests/test_outreach_tool_contract.py` now also checks that every waiting reason, state, delivery block reason, note and `sendRun`
  field this release names (`send-refused-twice-this-run`, `no-open-day`, `invite-already-pending`, `email-required`,
  `lead-skipped-this-run`, `movedThisRun`, `movedCount`) exists in the application, and that the skills and this entry name them.

Also shipped in 0.9.20 (mosaicohr-com/Mosaico-Codex-Plugin#49, merged to main as "Unreleased" before this version; skill-only, needs
the Mosaico server release 20261013c or later, which is already live: it carries `changes.nextTouchOn` on `outreach_update_lead` and
its date refusals `date-invalid`, `date-not-future` and `date-too-far`):

- **The interactive Lead-management skill lists the next contact date.** In both packages, "Update existing Leads" now names
  `nextTouchOn` among the Lead fields a person can set, and a new paragraph "Next contact date" says what to do when the person asks
  to contact a Lead again later ("contact Zoe again in January"): the model proposes one day (YYYY-MM-DD) from the person's words, the
  person confirms it, and only then `outreach_update_lead` is called with `changes.nextTouchOn`; `null` clears the booking. Mosaico
  judges the day (today in the owner's time zone, the allowed range) and refuses it with `date-invalid`, `date-not-future` or
  `date-too-far`; the skill then shows Mosaico's `earliestAllowed` and `latestAllowed`, asks the person for a day and calls again only
  with a day the person confirms. It works out no date or range itself. A follow-up that is already written is dated with
  `sendNotBefore` on a Message, which this skill never changes: it points the person to the Follow Up tab or the Follow-up routine.
  This closes the "Not done" note of 0.9.18.
- `tests/test_lead_management_skill.py` pins the wording in both packages and, with `--app-repo`, that a `manage_leads` run may call
  `outreach_update_lead` with `nextTouchOn` in the application.

### 0.9.19

Requires the Mosaico server release 20261014a (carrying mosaicohr-com/mosaico#1933, the send run follows the owner's limits: 100
checks, 100 drafts, future days), on top of release 20261013d (promotion mosaicohr-com/mosaico#1932, stage-v2 to main-v2, carrying
mosaicohr-com/mosaico#1931, "the send run owns one ordered work list"), which is already live. Do not publish or install this plugin
before that release is live on main-v2: the plugin is published only after 20261014a is on production main-v2. The Send invitations
routine of this release relies on what those releases added: `workflowStatus.sendRun` on `outreach_get_day` (`phase`, `complete`,
`recommendedAction`, `allowedActions`, `next`, `remaining`, `checksThisRun`, `checkLimit`, `checksLeft`, `draftsThisRun`, `draftLimit`,
`draftsLeft`, `waiting`, `waitingCount`, `skippedThisRun`, `skippedCount` and `message`), `sendRun` on the answers to
`outreach_record_message` (an invitation draft) and `outreach_record_connection_evidence` in a send run, `sendRun` and the blocked code
`send-run-open` on `outreach_end_run`, and `end_run` as the recommended action of a finished list.

- **One run does send, then check, then draft, in the order Mosaico gives** (invite-run skill, "Send invitations routine" and the
  sections it uses). Mosaico keeps one list for the run in `workflowStatus.sendRun`: (1) send the approved invitations, each Lead
  that holds one checked first (that check never counts toward a limit); (2) check the connection of every Lead placed on a later day
  (after today) whose connection is not checked yet, soonest day first, at most 100 checks in the run (`checkLimit`), counted by
  Mosaico from the run's own record and never by the model; (3) write the invitation draft of every Lead placed on a later day whose
  connection was checked and is not connected, at most 100 drafts in the run (`draftLimit`), counted the same way. `next` names the
  one Lead and `recommendedAction` the one thing to do; the answer to a connection check or a draft carries the updated `sendRun`
  (with `checksThisRun`, `checksLeft`, `draftsThisRun` and `draftsLeft`), so the run needs no reread, and the answer to a send or a
  recorded delivery block does not, so the run rereads the day. The skill no longer counts, orders or remembers what is left, and no
  longer rebuilds the list from `draftsToWrite`. The skills point at the fields (Mosaico hands out at most `checkLimit` checks and
  `draftLimit` drafts a run) and carry no limit of their own.
- **The opening question.** The interactive question in the invite-run skill (both packages) no longer offers "write missing
  invitation drafts" and "send approved invitations" as separate choices. It offers Source leads or Send invitations and tells the
  person that Mosaico runs send, then check, then draft, in one run.
- **A refused end.** The run ends `complete` only when Mosaico says the list is empty (`phase` `done`, recommended action `end_run`).
  Asked earlier, `outreach_end_run` is refused with `send-run-open`: nothing is recorded, the run stays open and the answer names the
  count left and the next action. The skill does what the answer names, never argues and never asks again. `blocked` still needs a
  `blockerCode` Mosaico gave in the run, three Mosaico errors in a row, or a `linkedInIssue` with a note.
- **The model's own "never retry" rule is gone for the send run.** The draft section no longer says that a refused Lead stays on a
  list that is not tried again: Mosaico skips a Lead whose check or draft it refused twice in the run and lists it under
  `sendRun.skippedThisRun`. The draft-writing rules are unchanged (the Agent's `messageInstructions` and `messagingChecklist`, a
  `checklistReview`, `sentAt` null, never approved or sent).
- **Order.** The "Both" section no longer says drafts first: sends, then checks, then drafts, because Mosaico orders it so, and Mosaico
  recommends no draft while a send or a check is left.
- **Leads that need a person never hold the end, and neither do Leads left over at a limit.** Mosaico lists them under
  `sendRun.waiting` with a reason (`in-to-sort`, `no-agent`, `agent-missing`, `no-profile-address`, `profile-capture-failed`,
  `check-limit-reached`, `draft-limit-reached` or `refused-twice-this-run`) and a plain message. `check-limit-reached` is the reason
  that release 20261013d called `check-cap-reached`; `draft-limit-reached` is new. A Lead left over after the 100 checks or the 100
  drafts waits for a later run.
- **The report** states Mosaico's figures from its answers, not memory: drafts written (`draftsThisRun`), connection checks made
  (`checksThisRun`), the Leads that waited with their reasons (a person is needed, `check-limit-reached` or `draft-limit-reached`)
  and the Leads Mosaico skipped.
- **Codex.** The Codex invite-run skill carries the matching wording. It cannot capture connection evidence, so when the next action
  is `verify_connection` it stops there, does not ask to end the run as complete and reports that the checks, and the drafts behind
  them, are left for a Claude Send invitations run. The Codex schedule-install skill no longer says that Source leads writes drafts:
  the Lead owner's Send invitations run does.
- **No schedule text changes.** The Send invitations text stays at 0.9.15: it names the "Send invitations routine" section of the
  installed plugin, so the plugin update is what changes the run. Update the plugin on every machine that runs the Send invitations
  schedule; an older plugin does not know the list, and Mosaico refuses to end its run while the list is not empty. The Follow-up
  (0.9.18), Withdraw stale invitations (0.9.15), Source leads (0.9.13) and Repair (0.9.6) texts are unchanged.
- `tests/test_outreach_tool_contract.py` now also checks the application's work-list module and registry for the fields, codes and
  reasons this release relies on (including `checkLimit`, `draftLimit` and the two limit reasons), that every `sendRun` field and
  waiting reason the skills and this entry name exists in the application, and that the skills name them.

### 0.9.18

Requires the Mosaico server release 20261013c (promotion mosaicohr-com/mosaico#1930, stage-v2 to main-v2, carrying
mosaicohr-com/mosaico#1928, "the Usage audit tab follows the routines", and #1929, "dated follow-ups"; the plugin relies on #1929
only). The Follow-up routine of this release relies on fields of that release: `sendNotBefore` on `outreach_record_message`,
`changes.nextTouchOn` on `outreach_update_lead`, `nextTouchOn` on `outreach_get_leads`, `nextTouchOn`, `notBefore` and
`scheduledReason` on the rows of `outreach_get_follow_ups` (with `summary.scheduled`, the held reason `follow-up-scheduled` on a dated
approval and the `followUpReason` `next-touch-due`), `notBefore` and `scheduledReason` on the items of `outreach_get_follow_up_queue`
(with `counts.scheduled`, the `nextStep` `wait_for_scheduled_day` and the held reasons `follow-up-scheduled` and
`next-touch-scheduled`), the note `next-touch-scheduled` and the `delivery` reasons on `outreach_deposit_conversation`, and the date
refusals `date-invalid`, `date-not-future`, `date-too-far` and `date-not-applicable` (with `field`, `today`, `earliestAllowed`,
`latestAllowed` and the recommended action `retry_with_valid_date`). Install or move the Follow-up schedule to the 0.9.18 text only
after that release is live. Send invitations and Withdraw stale invitations are unchanged and stay at 0.9.15.

- **The Follow-up routine books a later touch** (follow-up-run skill, new section "Book a later touch"). When the Lead's latest
  message in a deposited conversation (outcome `interested` or `neutral`) asks to be contacted later ("talk in January", "after the
  holidays", "next month", a named day), the run books that day instead of drafting now. The model proposes the day from the Lead's
  words (YYYY-MM-DD, counted from the day the Lead wrote them); the application owns the rules. Mosaico's answer to the deposit
  decides the call: when it lists `draft_follow_up`, the run writes the draft with `sendNotBefore` set to the day; when it offers no
  draft, refuses nothing but `follow-up-awaiting-reply`, holds no approval and returned nothing to Draft, the run calls
  `outreach_update_lead` with `nextTouchOn` and writes no draft. Anything else is not booked and is reported with the Lead's words.
  An approved follow-up that Mosaico offers is still sent as approved: booking never holds back or changes what a person approved.
- **The outcome checklist** (identical in both packages) now says that a message which asks to be contacted at a time it names is not
  a refusal, even when it begins with "not now": it is judged `interested` or `neutral` and then booked. Without this, "not now, talk
  in January" would be judged `declined` and the Lead dropped before it could be booked. A "not now" with no time, or a "maybe
  someday", stays `declined`.
- **Never today from a clock.** The skill forbids reading today from the machine, the page or `date`; Mosaico judges every day against
  its own today in the owner's time zone and returns it as `today` when it refuses a date. The day is only ever counted from the day
  the Lead wrote.
- **Date refusals follow `recommendedAction`.** On `date-invalid`, `date-not-future`, `date-too-far` or `date-not-applicable` nothing
  is written. The run retries once with a day the Lead's words still name between `earliestAllowed` and `latestAllowed`, worked out
  from the returned `today`; otherwise it takes `continue_with_next_lead`, writes nothing more for that Lead and reports the
  refusal. It never picks a day only to get past a refusal and never writes the draft undated.
- **Booked work waits.** A queue item with `nextStep` `wait_for_scheduled_day` (reasons `follow-up-scheduled` or
  `next-touch-scheduled`, last in stage `held`) is not due: the run never opens, reads, drafts or sends for it and reports it from
  `counts.scheduled`. A queue left with only those stops with `queue-empty`, and they no longer count as needing a person. A draft
  skipped with `next-touch-scheduled`, or `draft-already-exists` for a dated approval, means the Lead is already booked: recorded,
  nothing written. On its day (`scheduledReason` `scheduled-due` or `next-touch-due`) the item is first in its stage and is worked
  like any other, without a date, and is not booked again from the same message.
- **A new reply on a booked Lead.** A reply before the day does not clear the booking. When a deposit carries the note
  `next-touch-scheduled`, the run judges the Lead's latest message against the booked day: another time moves `nextTouchOn`, a request
  for contact now or a withdrawn request clears it (`null`), anything else leaves it. A booking also ends when a follow-up is recorded as
  sent on or after the day (Mosaico clears it in the same write). The day of a follow-up that is already written is a person's to move
  on the Follow Up card; the run does not record a written message again to change its day.
- **The report** gains the bookings made (Lead, day and the Lead's words), the bookings changed or cleared, the booked items waiting
  (`counts.scheduled`) and the date refusals.
- The Follow-up schedule text is stamped 0.9.18 or later. The installer moves a saved 0.9.15, 0.9.16 or 0.9.17 Follow-up text to the
  0.9.18 text in place ("Update the standing answers in place"), keeping its cron, name and enabled state. The Send invitations and
  Withdraw stale invitations texts stay at 0.9.15; the Source leads (0.9.13) and Repair (0.9.6) texts are unchanged.
- The Codex package states the dated fields in its queue section and carries the same "Book a later touch" section for its check and
  one-pass scopes, and still does not run the scheduled routine.
- `tests/test_outreach_tool_contract.py` now also checks the application's registry, queue and date module for the fields and codes
  this release relies on.
- Not done: the interactive Lead-management skill does not list the next touch among the Lead fields a person can edit.

### 0.9.17

Requires the Mosaico server release 20261013a (promotion of stage-v2 to main-v2 carrying mosaicohr-com/mosaico#1921, "the Follow-up run
owns the repairs of its own Leads"). The Follow-up routine of this release relies on fields of that release: the new queue stages
`fix-address` and `drop-declined`, `repairGroup` on every queue item, `skippedThisRun` and `counts.skippedThisRun`, `linkedDuplicate`
(with the note `duplicate-linked`) and `heldBy` on `outreach_deposit_conversation`, and `excludedAsFollowUpWork` on
`outreach_get_repair_queue`. Install or move the Follow-up schedule to the 0.9.17 text only after that release is live. Send invitations
and Withdraw stale invitations are unchanged and stay at 0.9.15.

- **Connection-evidence script: a gone profile is reported as 404 or 410.** The script's `status` was the HTTP status of LinkedIn's
  profile data call, not of the page. A page that shows "not found" can still answer 200 with no profile, so the server counted a first
  failure instead of giving up (a 404 or 410 gives up at once), and the 0.9.16 redirect retry made it worse: it replaced a first call's
  404 with the retry's own status when the retry also found no profile. Now the script reports 404 when no profile was resolved, the
  data call answered 2xx and the page itself is LinkedIn's not-found page (read from `document.title` and `location.pathname` only), a
  410 stays 410, and a retry never replaces a first 404 or 410. A true 200 with a profile, a refusal, a rate limit, a server error and
  a dropped call are unchanged, and `requestedIdentifier` and `resolvedIdentifier` behave as in 0.9.16. The title marker is checked
  against a fake page; it has not been checked against a live LinkedIn not-found page yet.
- **Follow-up routine works the repairs the queue now carries** (follow-up-run skill). `fix-address` (`nextStep` `fix_address`) and
  `drop-declined` (`nextStep` `drop_lead`) are worked before every other stage, each by its `recommendedCall` (`outreach_update_lead`)
  with nothing done on LinkedIn; a profile check of a listed Lead is in `verify-connection` and a history mismatch is in `read-thread`.
  Every item carries `repairGroup` (`addresses`, `declinedPending`, `mismatches`, `repairSuggestions`, `unverified` or null).
- **`skippedThisRun` is information for the report.** A Lead whose call in this run came back with an answer nothing in the run can
  change (`profile-capture-failed`, `thread-person-held-by-other-lead` and the others Mosaico lists) is left out of `items` and `next`;
  `completion.stopReason` is `queue-empty` when only those remain. The routine never tries a skipped Lead again in the same run; a later
  run offers it again when it is still work.
- **`linkedDuplicate` on a deposit.** When the thread proves by member id that two Leads are one person, Mosaico links them inside
  `outreach_deposit_conversation` and stores the messages and outcome on the kept Lead. The routine reports the link and continues with
  the kept Lead. A match by identifier only still refuses with `thread-person-held-by-other-lead` (now with `heldBy` and `leadId`): the
  routine records it and continues as before. A follow-up pass still may not call `outreach_link_duplicate_leads`.
- **The report** lists the Leads skipped this run with their codes, the links made, the addresses fixed and the Leads dropped as
  declined. The standing answers and the stop-and-report structure are unchanged.
- **Repair now works only the backlog outside the follow-up queue.** `outreach_get_repair_queue` leaves out every Lead the follow-up
  queue lists except duplicates and counts them in `excludedAsFollowUpWork`; the repair-run skills (Claude and Codex) say so and report
  the count.
- The Follow-up schedule text is stamped 0.9.17 or later. The installer moves a saved 0.9.15 or 0.9.16 Follow-up text to the 0.9.17 text
  in place ("Update the standing answers in place"), keeping its cron, name and enabled state. The Send invitations and Withdraw stale
  invitations texts stay at 0.9.15; the Source leads (0.9.13) and Repair (0.9.6) texts are unchanged.
- The Codex package states the new queue stages and `skippedThisRun` in its queue section and still does not run the scheduled routine.

### 0.9.16

Requires the Mosaico server release 20261012d (promotion mosaicohr-com/mosaico#1916, stage-v2 to main-v2, carrying
mosaicohr-com/mosaico#1908, #1909, #1910, #1911, #1912 and #1915). The Follow-up routine of this release relies on two tools of that
release: the new `outreach_get_follow_up_queue` and the extended `outreach_deposit_conversation` (its `delivery` answer). It also needs
the run intent `follow_up_pass` on `outreach_start_run`. Install or move the Follow-up schedule to the 0.9.16 text only after that
release is live. Send invitations and Withdraw stale invitations are unchanged and stay at 0.9.15.

- **Follow-up routine** (follow-up-run skill). It starts its run with intent `follow_up_pass` (it may deposit conversations, record
  messages, mark sent, record delivery blocks, record connection evidence and connections snapshots, update Leads and end the run; it
  may not save Leads, link duplicates or withdraw) and reads `outreach_get_follow_up_queue` instead of `outreach_get_follow_ups`, which is
  about 750 KB and is no longer the working read. The queue is lean, paged and ordered by the application: the connections capture first
  (`next.kind` `connections-capture`, with its call and script parameters), then one item per Lead in its earliest stage
  (`verify-connection`, `read-thread`, `send-approved`, `draft`, `held`). The routine does `next` once, rereads, and follows each item's
  `recommendedCall` literally; it never reorders the work. It stops on `completion.stopReason` (`queue-empty`, `needs-a-person`,
  `needs-another-intent` or `blocked`) and reports `unverified` honestly: while its state is `pending-connections-capture` the count
  is not known.
- **Send right after a deposit.** When `outreach_deposit_conversation` answers `delivery.state` `deliverable` and recommends
  `send_approved_follow_up`, the routine sends that approved follow-up at once with `delivery.body`, `delivery.messageId` and
  `delivery.messageUrl`, without rereading the queue. `held` and `none` send nothing. It opens the item's `messageUrl`: the full
  messaging page when the basis is `conversation` or `stored`; when the basis is `profile` it uses the Message button and closes any open
  message window before it navigates to the next profile and after each send. Typed text is proved by the thread capture after the
  send, not by sight (a script that reads the compose box is deferred). One pass per thread stays.
- **Record and continue.** `thread-person-held-by-other-lead` on a deposit (the person is already another Lead of the owner) and a
  blocked `outreach_record_connection_evidence` (`profile-capture-failed`, with `profileCaptureFailures`, `givenUp` and `inToSort`) are
  recorded in the report and the run moves on; neither is retried in the same run.
- **Connection-evidence script, redirect retry (row 21).** When the first profile query fails (404, 410, or a 2xx with no usable
  profile) and the browser page has followed a redirect to a different `/in/<slug>/`, the script asks once more with the page's own
  slug, never more than once and never after a refusal, a rate limit, a server error or a dropped call. For an opaque member id the retry
  is accepted only when its profile carries that member id. The sealed output reports both `requestedIdentifier` (what the run asked
  for) and `resolvedIdentifier` (what LinkedIn named); nothing is swapped silently. `status` is the last call's status (a dropped retry
  keeps the first status). Mosaico stores the old identifier as an alias when it receives the resolved one.
- The Follow-up schedule text is stamped 0.9.16 or later. The installer moves a saved 0.9.15 Follow-up text to the 0.9.16 text in place
  ("Update the standing answers in place"), keeping its cron, name and enabled state. The Send invitations and Withdraw stale invitations
  texts stay at 0.9.15; the Source leads (0.9.13) and Repair (0.9.6) texts are unchanged.
- The Codex package states the queue read for its check and send scopes and still does not run the scheduled routine. Its
  tool-contract test now also reads the follow-up queue's tool name from the application's shared constant.

### 0.9.15

Requires the Mosaico server release 20261012c (promotion mosaicohr-com/mosaico#1907, stage-v2 to main-v2, carrying
mosaicohr-com/mosaico#1906), which ships `outreach_get_withdraw_queue` and `outreach_record_withdrawal`. Install the Withdraw stale invitations schedule only after that
release is live. Send invitations and Follow-up need no new server tools.

- The single daily Sync data routine is split into three daily routines, each with its own schedule, so one slow or blocked
  step no longer holds up the others. The installer installs three tasks and retires the old one:
  - **Send invitations** (invite-run skill, "Send invitations routine", default 1:00 PM): for today, writes the owner's missing
    invitation drafts from `draftsToWrite`, then sends the approved invitations. Nothing else.
  - **Follow-up** (follow-up-run skill, "Follow-up routine", default 1:30 PM): checks accepted invitations (with replies and with
    no replies), checks message replies to follow-ups, one pass per thread across all dates, and sends the approved follow-ups.
  - **Withdraw stale invitations** (invite-run skill, "Withdraw stale invitations routine", default 2:00 PM): starts a run with
    intent `manage_leads` and passes its `runId` to both tools. It reads `outreach_get_withdraw_queue` (candidates, `count`, `cap`,
    `completion`, `blockers`, `allowedActions`, `recommendedAction`, `next`) and follows `recommendedAction` literally. For the Lead
    in `next` it withdraws the pending invitation in Claude's browser pane, then calls `outreach_record_withdrawal`, and rereads
    after every write. It stops when `next` is null or `completion.mustContinue` is false and reports the `stopReason`. A blocked
    read (for example `linkedin-identity-not-registered`) stops and reports; a `blocked` write (for example
    `invitation-accepted` or `invitation-too-recent`) writes nothing, so that Lead is skipped, reported and the run continues.
    Mosaico owns the 30-day rule and the per-run cap (25); the skill never recomputes either. It never sends, never clicks
    Connect and never withdraws an invitation Mosaico did not list. A LinkedIn warning or captcha stops the run, which reports.
- The "Sync data routine" section of the follow-up-run skill is now a short "Sync data routine (superseded)" note. An old saved
  Sync data schedule starts no run, touches nothing, and reports that it must be reinstalled. Run the installer again: it creates the
  three tasks first and then retires (disables or deletes) the old Sync data task, so nothing runs twice.
- The three new texts are stamped 0.9.15 or later. The Source leads (0.9.13) and Repair (0.9.6) texts are unchanged.
- The three daily schedules share one browser pane and must not overlap (defaults 30 minutes apart). The installer keeps every Source
  leads time at least 60 minutes from each of them, so the own lane no longer runs at 2:00 PM (`0 0,2,4,6,8,12,16,18,20,22 * * *`);
  run the installer again to move a saved own-lane cron.
- The Codex package has no browser capture, so it still installs only Source leads; its installer and overview now name the new
  schedules as installed from Claude.

### 0.9.14

Requires the Mosaico server release of 2026-10-11 (main-v2 at 518b4c5e9, mosaicohr-com/mosaico#1888, production
build 321), which carries `convert_methodology_from_text`, `get_next_methodology_model_request`,
`submit_methodology_model_response` and `cancel_methodology_analysis` (status contract 9). That release is live.

- New skill `mosaico-methodology-convert`, in both the Claude and the Codex packages. It converts a methodology,
  playbook or framework document the person gave in the conversation: one `convert_methodology_from_text` preview
  with the text (the person sees the name, size, checksum and excerpt), one execute call with only the token (the
  host asks the person to approve it), then it reads `get_methodology_project_status` and follows its
  `recommendedAction` exactly: wait, show blockers in Mosaico's words, retry only when the status offers it, ask
  the person before `set_conversion_level_positions` or `discard_conversion_components`, and leave
  `start_conversion_in_app`, `review_analysis` and approval to the person in the app. A PDF or Word file is
  uploaded in the Methodology page instead; a methodology in several parts is one project per part.
- The skill adds no Mosaico server and holds no workflow state; Mosaico owns it.

- New skill `mosaico-methodology-conversion-run`, in both the Claude and the Codex packages. It runs the "answer model
  requests" loop of a conversion that uses the person's own connected Claude: find the project with
  `list_methodology_projects`, start with `start_methodology_analysis` and provider `client` only when the status
  offers it (the app's preview, approved once by the host, is the single confirmation), then follow
  `get_methodology_project_status` and its one `recommendedAction` until `analysis.stop.validStops` allows a stop.
- Where the host can start sub-agents, the skill fans out `parallel` helpers with one fixed brief and no document
  text, and rereads the status after them. Otherwise it answers one request at a time (`claimNext: true`, status every
  3 requests). A refused answer is fixed from `issues`, at most twice. After a
  chat stops, the skill reads the status and says when held parts free up. It gives every refusal code with Mosaico's
  own sentence, never approves or installs, and sends the person to the app to review.
- The skill adds no Mosaico server and holds no workflow state. `tests/test_methodology_conversion_run_skill.py` checks
  the tool, action and code names, the sentences and the loop rules, and with `--app-repo` the application too.

### 0.9.13

Requires the Mosaico server release that carries mosaicohr-com/mosaico#1834 (sourcing writes no drafts; `draftsToWrite`).
Do not publish or install this plugin before that release is live on main-v2; until then the server still expects Source
leads to write drafts.

- Source leads finds Leads, saves them and lets Mosaico place them on days, then ends the run. It never writes an
  invitation draft, for its own Leads or a colleague's. Mosaico refuses the write with `sourcing-writes-no-drafts`
  (blocked, recommended action `continue_with_next_lead`, nothing saved, the Lead stays saved and placed); the skill treats
  that answer as expected and moves on, and does not attempt a draft in the first place. After the plan is done a
  sourcing run's recommended action is `end_run`. The Sync-time drafting of a colleague's proven Lead and the
  `lead-awaiting-owner-check` and `colleague-draft-invite-only` refusals are gone from the skill. The action name
  "source Leads and prepare invitation drafts" is gone too: the one action is "source Leads only".
- Sync data writes the missing invitation drafts for the person's own Leads, from `draftsToWrite` (on `outreach_get_day`
  in `workflowStatus`, and top-level on `outreach_get_follow_ups`): `count`, `entries` (`leadId`, `name`, `agentId`, `day`,
  `action`), `writtenBy`, `writableInThisRun`, `allowedActions`, `recommendedAction` (`draft_invitation_messages` or
  `none`) and `note`. The new invite-run section "Write missing invitation drafts" follows that list and its recommended
  action, reads the person's own Agents with `outreach_get_agents` (no arguments), and writes each draft with
  `outreach_record_message` (`kind` `invite`, `direction` `outbound`, `sentAt` null, a `checklistReview` for the Agent's
  rules, the `runId`). The Sync data routine runs it first in its invitation step; it never approves or sends a draft.
- Installer: the Sync data text and both Source leads lane texts (and the Codex Source leads text) are stamped 0.9.13 or
  later. The Sync data text names the actions "write missing invitation drafts" and "send approved invitations"; the
  Source leads texts name the one action "source Leads only". Repair is unchanged (0.9.6). Run the installer again to move a
  saved Sync data or Source leads text to the new stamp.
- The Claude and Codex packages both move to 0.9.13. Codex's invite-run skill carries the same Source leads change and the
  same "Write missing invitation drafts" section; it still installs only Source leads.

### 0.9.12

Requires Mosaico server release 20261008e (PR #1831) or later; install only after that release is live on main-v2.
Before that release the server does not know `sourcingScope`, `workNow` or the two-reason `outreach_end_run`.

- Source leads runs in two lanes. The saved text carries one standing line, `sourcing scope: own` or
  `sourcing scope: colleagues`, and the run passes exactly that word as `sourcingScope` on `outreach_start_run`; with no
  such line it sends nothing and works the whole plan. It never chooses or invents a scope, checks the echo in the
  start answer, and starts once per session. The report gains "Mosaico lane" and "Candidates skipped as held by
  another owner: N".
- The run works `workNow`, the Agent Mosaico names, re-read at every decision point: `workNow.brief` is that Agent's
  own search instructions, and `workNow.agentId` goes on every `outreach_save_lead` with no `ownerUserId` (Mosaico
  saves the Lead for the Agent's owner). In a colleagues run the run's own day is empty and it sources for the owner
  `workNow` names. While searching it calls `outreach_get_run` at least every 10 minutes.
- Start refusals are handled: `sourcing-run-busy` and `sourcing-scope-empty` are not failures (one line, then stop);
  `sourcing_scope_invalid` and `sourcing_plan_empty` are loud. A candidate held by another owner is a skip, never a
  failure, and there is no stop after a number of failures and no search budget: a run keeps searching until Mosaico
  says the numbers are met.
- `outreach_end_run` takes `complete` or `blocked` only; `abandoned` is gone. A refused end (`sourcing-run-open`) is not
  retried or argued: the run reads `workNow` and keeps sourcing. A finished run is always ended with `complete`. A
  write answered `run_ended` after an idle close stops the run, which reports and starts nothing. An Agent Mosaico
  closed as unavailable (`unavailableAgents`) is reported and never sourced for.
- The installer creates two Source leads tasks, "Mosaico Outreach — Source leads (own)" at
  `0 0,2,4,6,8,12,14,16,18,20,22 * * *` and "Mosaico Outreach — Source leads (colleagues)" at
  `0 1,3,5,7,9,11,15,17,19,21,23 * * *`, 60 minutes apart from each other, from Sync (13:00) and from Repair (Sunday
  10:00). A scope-less Source leads task is updated in place into the own lane. A person who does not source gets none.
  Both texts say "0.9.12 or later", so run the installer again to move a saved Source leads text; Sync data and Repair
  texts are unchanged.

### 0.9.11

- The Sales Navigator colleague check carries proof fields. Inside the sealed object (null allowed, covered by the
  digest) the script now also returns `complete` (the name-narrowed "Connections of" search was read to its end: its
  last page held fewer than 25 results, or start plus count reached `paging.total`; false at the 2-page cap or on an
  error), `controlTotal` (`paging.total` of the same filter with no keyword and count 1, one extra call paced like
  the others; null if that call failed or was not needed because the candidate was listed), `visibility` (`visible`
  when `controlTotal` is above 0, otherwise `unknown`) and `unreadableRows` (result rows of the narrowed pages whose id
  could not be read). `resultsTotal` stays; `pagesRead` now also counts the control search. A failed control call
  empties `controlTotal` only; `found` and `status` do not change.
- `visibility` is never `hidden`. The 2026-10-07 captures show an empty connection list as a plain 200 answer with
  `paging.total` 0 and no notice or marker, and the case of a colleague who hides her connections was not captured, so
  no hidden-list marker is known. A control total of 0 is reported as `"0"` with `unknown`, and Mosaico treats it as
  unproven.
- Source leads (Claude): a candidate saved with the note `colleague-check-negative-proven` is verified not connected by
  the colleague check, and the run drafts her invitation in the same run (`outreach_record_message`, her `leadId`, no
  `ownerUserId`); the run reads her day (`outreach_get_day` with her `ownerUserId`) to see which of her Leads need
  drafts. A Lead saved with `colleague-check-negative-unproven` stays undrafted: continue sourcing. A run never records
  connection evidence for a colleague's Lead and no longer sends colleague Leads through "Capture connection
  evidence". The report splits the colleague's Leads into "verified not connected by colleague check (proven)" and
  "unproven, awaiting her Sync", and lists the drafts written for her.
- Sync data (Claude): the verification queue may list `colleague-verified-needs-own-check` Leads first; verify them from
  your own pane like any other. If `outreach_mark_message_sent` answers `own-evidence-required`, run the connection-
  evidence script, record it, reread, then continue. The Codex package states the same rules; it cannot run the script.
- Needs the Mosaico release that carries the proof matrix (mosaico-app pull request 1822). A 0.9.10 capture carries
  none of the new fields and stays an unproven negative ("update the plugin to 0.9.11 or later").
- No new routine section and no new minimum for the saved schedule texts: they still say "0.9.9 or later" and need no
  reinstall, because the procedure lives in the installed plugin's routine sections.

### 0.9.10

- Source leads now reads every planned Agent. After `outreach_start_run` it calls `outreach_get_agents` with the
  `runId` (never with `ownerUserId`) and works from each returned Agent's own instructions, colleagues' Agents
  included.
- A Source leads run never ends on its own. There is no search limit: few results, weak results, "slow" or "enough
  found" are never a reason to stop, and when results are few the run widens inside the Agent's brief (more keywords,
  more pages, other filters, other regions the brief allows, Premium Daily Prospects). An Agent brief that says to
  report a supply constraint means note it for the final report and keep searching. The run stops only on Mosaico's
  completion (`sourcing-quota-met` or `sourcing-days-full`), `stop_run` after the tenth failure,
  `end_run_days_full`, or a genuine blocker. A run that ends with any line open is reported as "run failed: stopped
  with N open".
- Every run ends through `outreach_end_run` with reason `complete` or `blocked`; Mosaico decides the outcome and
  records a claim it cannot back as abandoned. The sourcing report (`outreach_record_sourcing_report`) is written
  only after the tenth failure; Mosaico refuses it with `sourcing-not-complete` before then.
- The start answer names the Mosaico environment (`environmentName`). Each report begins with "Mosaico environment:
  production", and a run on anything else stops. If the answer carries `previous-run-abandoned`, the report says so
  next: "Previous run failed: stopped with N open". The Follow-up (Sync data) and Repair routines end their runs
  through `outreach_end_run` and report the environment too.
- No new routine section, so the saved schedule texts still say "0.9.9 or later" and need no reinstall.
- Depends on the Mosaico application change that adds `runId` to `outreach_get_agents`, `outreach_end_run`,
  `runOutcome` and `environmentName` (mosaicohr-com/mosaico pull request 1820) being deployed first.

### 0.9.9

- Source leads now delivers Leads per run, and the application files the Leads into free days. Each Agent in
  Outreach has a new field, Leads per run (`leadsPerRun`, 1 to 100), beside Leads per day (now the most Leads on one
  day). An Agent is sourced only when it is on and both are set; Mosaico says so on every Agent read (`sourcing`:
  `sourced`, `not-configured` or `off`, with `sourcingReason`). A run's quota is the sum of the Leads per run of the
  Agents it sources; nothing is taken off for earlier runs.
- The invite-run skills (Claude and Codex) leave `day` out of `outreach_get_day` for a sourcing run, never send
  `scheduledDate` (Mosaico ignores it and files each Lead on a free day) or `targetCount`, and pass the `agentId`
  on every save. They keep sourcing while any Agent line in `workflowStatus.sourcingPlan` is `open`, following
  `nextOwnerUserId` and `nextAgentId`; the run ends only on Mosaico's completion (`sourcing-quota-met` or
  `sourcing-days-full`), never on the model's judgement. After sourcing they verify and draft across every day in
  `runDays`, and end when Mosaico recommends `end_run_days_full`.
- Two start outcomes: `sourcing_plan_empty` (now recommended action `set_agent_sourcing_numbers_in_outreach`)
  stops the run with "Set Leads per day and Leads per run on an Agent in Outreach (Agent tab), then rerun.", and
  `sourcing-days-full` ends it with "Every Agent is full for the next 10 business days; nothing to source", which is
  not a failure. The note `sourcing-plan-already-met` is gone. The skills also handle the save blocks
  `sourcing-quota-met` and `sourcing-days-full`, which save nothing and count as no failure.
- The report gives, from Mosaico's counts, each Agent's target, accepted, remaining and status, the days the Leads
  were filed on, and the shortfalls. A run that saved nothing because of a blocker other than days-full is still a
  failed run; days-full with nothing saved is reported as nothing to source.
- The Source leads schedule text drops "day: the next business day" and needs plugin 0.9.9 or later. The Agent
  skill and the overview skill describe both numbers and the sourcing state.
- What a person does once: set both Leads per day and Leads per run on each Agent to be sourced in Outreach. Run the
  installer once to move a Source leads schedule to the 0.9.9 text, or leave it: a text saved for 0.9.8 still runs on
  0.9.9, and the day it names is ignored.
- Depends on the Mosaico application change that adds Leads per run and day placement (mosaicohr-com/mosaico pull
  request 1817) being deployed first.

### 0.9.8

- Source leads now follows the sourcing plan on the Agents. Each Agent in Outreach has two new fields, Leads per day
  (`leadsPerDay`, 1 to 100) and Sourced by (`sourcedByUserId`, an active member, empty means the owner). The
  invite-run skills (Claude and Codex) start a sourcing run with no quota and no colleague; Mosaico works out how
  many Leads each owner still needs today and returns it as `run.quota` with `run.sourcingPlan`. They never send
  `targetCount` for sourcing, read `workflowStatus.sourcingPlan`, `agentId` and `nextAgentId` from the day, and pass
  the `agentId` on every save. They handle `agent-not-in-sourcing-plan`, `planned-agent-quota-met` and `agent-required`.
- Two new outcomes at the start: `sourcing_plan_empty` stops the run with "Set Leads per day on an Agent in Outreach
  (Agent tab), then rerun." and a run issued with the note `sourcing-plan-already-met` ends with a short report.
  The report now gives Leads saved and Leads remaining today per owner and per Agent, from Mosaico's counts. The
  failed-run rule and the colleague check are unchanged (Codex still cannot run the colleague check).
- The quota is gone from the schedules. The Source leads text drops the quota map and needs plugin 0.9.8 or later;
  the "Offer to save the quota into the Source leads schedule" section and the quota questions are removed. The
  Agent skill and the overview skill describe the two new Agent fields; `outreach_update_agent` sets them (Owner,
  Admin or the Agent's owner; Sourced by must be an active member).
- What a person does once: set Leads per day (and, if wanted, Sourced by) on an Agent in Outreach. Run the installer
  once to drop the quota from the Source leads schedule, or leave it: the extra standing answer is ignored.
- Depends on the Mosaico application change that adds the sourcing plan (mosaicohr-com/mosaico pull request 1815)
  being deployed first.

### 0.9.7

- The bundled Mosaico server is removed. `plugins/mosaico-claude/.mcp.json`, `plugins/mosaico-codex/.mcp.json`
  and the Codex manifest's `mcpServers` entry are gone, and with them the bundled server's sign-in
  settings. The plugins now ship only skills, hooks and browser scripts.
- Runs use the person's own Mosaico connector only: the one that serves production (`https://app.mosaico.one`).
  The Source leads, Sync data and Repair routine sections and the `mosaico-outreach` skill say so. If no Mosaico
  connector is connected, the run stops and tells the person to connect it in Claude's connectors (not `/mcp`),
  then rerun. A server whose address contains amplifyapp.com, stage, staging, test or localhost is never used, and
  a server is never chosen because its organisation id matches, because stage and production share ids. This
  replaces the "production connector only" wording of the earlier unreleased change (pull request 32), which still
  allowed the plugin's own server.
- The schedule installer has two checks before installing: a project or user MCP server that points at a
  non-production Mosaico address must be removed first (a scheduled Source leads run had started its Mosaico run on a
  stage server this way), and a Mosaico connector pointing at `https://app.mosaico.one` must be connected and
  signed in. "Set up a second person" step 2 now says she connects the connector in her own Claude.
- Nothing in the hooks needed to change: the browser-script gate matches the browser tools, never a Mosaico tool
  name, and the tool-contract test reads the skills and the application registry, not the plugin's server.
- README: new architecture paragraph, connector sign-in instructions, and the "After a Mosaico deploy" note above.
- Issue mosaicohr-com/mosaico#1804 (the bundled server's client-metadata sign-in) becomes moot for the plugin. The
  server-side allowlist and localhost question stays with the Mosaico application.
- Consequence: Claude keeps a copy of the connector's tool list, so after a Mosaico deploy it can go stale. Disconnect
  and reconnect the connector, or restart Claude, if a tool argument is refused as unknown.
- Codex: the package no longer brings a server. Add your own Mosaico connector in Codex (see the Codex section).
- What a person does once: nothing, if the Mosaico connector is already connected and signed in in Claude. If it is
  not, connect it in Claude's connectors and sign in.

### 0.9.6

- Thin routines. The schedule installer now saves, for each of Sync data, Source leads and Repair, a short text
  (under 200 words) that holds only the person's standing answers and tells the run to follow the installed plugin's
  skill: the "Sync data routine" section of `mosaico-outreach-follow-up-run`, the "Source leads routine" section of
  `mosaico-outreach-invite-run` and the "Repair routine" section of `mosaico-outreach-repair-run`. Before this, each
  schedule text held the whole procedure, so every release left saved schedules stale until someone ran the installer
  again (a Mac was still running 0.5.0-era Source leads text with 0.9.3 installed).
- The procedure itself moved, word for word except that the placeholders now refer to the schedule's standing
  answers, from the schedule texts into those three named sections. Nothing about what a run does changes.
- Version stamp: each thin text names the minimum plugin version it needs (0.9.6, the first release that contains
  the routine sections). A run on an older plugin, or on one without the section, stops and reports that the plugin
  needs updating. The Codex package gets the same for its Source leads automation.
- "Update the Source leads quota in place" is now "Update the standing answers in place": it changes the timezone,
  the LinkedIn public identifier or the quota map of any schedule and replaces a long-form text with the thin text,
  keeping the cron times, enabled state, name and answers.
- What a person does once: run the schedule installer again. It swaps each saved long text for the thin one and
  keeps the times, enabled state, name and answers. After that, plugin releases are picked up without reinstalling.
- The approved browser scripts and the application contract are unchanged. Existing schedules keep their long
  texts until the installer is run again once; the thin texts need plugin 0.9.6 or later.

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
python3 tests/test_run_guards_skill.py
python3 tests/test_sync_drafts_skill.py
python3 tests/test_lead_management_skill.py --app-repo ../mosaico-app
python3 tests/test_methodology_conversion_run_skill.py --app-repo ../mosaico-app
python3 tests/test_connector_acting_skill.py --app-repo ../mosaico-app
```

## License

Copyright Mosaico Limited. See [LICENSE](LICENSE).
