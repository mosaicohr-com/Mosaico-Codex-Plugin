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
action. The schedule option installs two per-user local-time automations: invitation preparation at
8:00 AM and delivery of already-approved invitations at 8:00 PM. Plugin installation never creates
or enables a user's schedules silently.

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
