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

- `plugins/mosaico-claude/browser/` holds the three approved capture scripts. Each runs inside the
  signed-in LinkedIn page in Claude's built-in browser pane, calls one fixed LinkedIn endpoint, uses the
  page's own session and CSRF material without ever returning it, and returns only the fields Mosaico's
  evidence parser reads (status, relationship state, profile identifier, capture time). Names, headlines
  and every other field are dropped before anything leaves the page.
- `plugins/mosaico-claude/browser/linkedin-whoami.js` is the identity script: one call to LinkedIn's "who am I" endpoint that returns only the account's numeric id, URNs and public identifier, which a run passes unchanged as `identityEvidence` to `outreach_start_run`.
- `plugins/mosaico-claude/hooks/browser-script-gate.py` runs before every browser script call. It allows
  an approved script word for word (only the first line's value may change) and refuses any other script
  that names LinkedIn or reads a credential store. It logs nothing and never echoes a script, header,
  cookie or response.
- When the capability is unavailable, the skills leave the Lead unverified, report only what the LinkedIn
  page visibly shows, and stop the step. They never scrape browser storage, profile files, DevTools data
  or the keychain.

The Codex package ships no such capability, so its Outreach skills do not capture connection evidence.

## Changelog

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
```

## License

Copyright Mosaico Limited. See [LICENSE](LICENSE).
