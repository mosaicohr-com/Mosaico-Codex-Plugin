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
action. The schedule option installs two per-user local-time schedules: Sync data (connections and
messaging, once a day, the only one that sends) and Source leads (every two hours in business hours,
at least 60 minutes from Sync, never sends). Before installing, the Claude package checks that
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
   Leads herself.

Each person's Sync data schedule runs on that person's own Mac, in that person's own pane, and sends only
from that person's account. Nobody's run touches another owner's Leads.

## Connection-evidence capability (Claude Code)

The Claude Code package verifies LinkedIn connection status through a browser-side capability instead
of any cookie or session export:

- `plugins/mosaico-claude/browser/` holds the five approved capture scripts. Each runs inside the
  signed-in LinkedIn page in Claude's built-in browser pane, calls one fixed LinkedIn endpoint, uses the
  page's own session and CSRF material without ever returning it, and returns only the fields Mosaico's
  evidence parser reads (status, relationship state, profile identifier, capture time). Names, headlines
  and every other field are dropped before anything leaves the page.
- `plugins/mosaico-claude/browser/linkedin-whoami.js` is the identity script: one call to LinkedIn's "who am I" endpoint that returns only the account's numeric id, URNs and public identifier, which a run passes unchanged as `identityEvidence` to `outreach_start_run`.
- `plugins/mosaico-claude/browser/linkedin-thread-messages.js` is the thread script: it takes the Lead's public identifier on its first line, finds the one-to-one conversation with that Lead among LinkedIn's recent conversations, and returns only the participants' member ids and the messages oldest first, each with its delivery time, sender and text. A run passes the output unchanged as `threadEvidence` to `outreach_deposit_conversation`; Mosaico derives each message's direction and time from it. It runs only in Claude's built-in browser pane.
- `plugins/mosaico-claude/browser/linkedin-sent-invitations.js` is the sent-invitations script (0.8.0): it takes the Lead's public identifier on its first line, reads LinkedIn's Sent invitations list (100 a page, up to five pages) until the Lead is found, and returns only `{ status, signedIn, capturedAt, state, publicIdentifier, invitation, pagesRead }`, where `state` is `found`, `not-found` or `error` and `invitation` is `{ sentTime, inviteeUrn, invitationUrn }` or null. A run passes the output unchanged as `sentInvitationEvidence` to `outreach_mark_message_sent`. The endpoint is not validated against a live account yet (validated: pending). It runs only in Claude's built-in browser pane.
- `plugins/mosaico-claude/hooks/browser-script-gate.py` runs before every browser script call. It allows
  an approved script word for word (only the first line's value may change) and refuses any other script
  that names LinkedIn or reads a credential store. It logs nothing and never echoes a script, header,
  cookie or response.
- When the capability is unavailable, the skills leave the Lead unverified, report only what the LinkedIn
  page visibly shows, and stop the step. They never scrape browser storage, profile files, DevTools data
  or the keychain.

The Codex package ships no such capability, so its Outreach skills do not capture connection evidence.

## Changelog

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
