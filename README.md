# Mosaico assistant plugins

Public, read-only distribution repository for the official Mosaico plugins for Codex and Claude
Code.

Architecture. The plugins ship no Mosaico server. They contain only skills. Every Mosaico call goes through the person's own Mosaico
connector, the one that points at production (`https://app.mosaico.one/api/mcp`) and is signed in with
their own Mosaico account. There is one door and one sign-in.

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
`mosaico` skill says so when a tool it names is missing.

## What is in the plugin

Three skills, in both the Claude Code and the Codex package:

- `mosaico`: manage your Mosaico organization through the connector (flows, domains, capabilities, positions,
  teams, members, analytics, support, the example catalogue, and working as a member of a customer for
  resellers).
- `mosaico-methodology-convert`: turn a methodology document into Mosaico flows, domains and capabilities.
- `mosaico-methodology-conversion-run`: work a methodology conversion that is already running.

## Changelog

### 1.0.0

The first customer release. The plugin is now the public Mosaico plugin only: the `mosaico`,
`mosaico-methodology-convert` and `mosaico-methodology-conversion-run` skills in both packages, the Mosaico
logo (`assets/mosaico-logo.svg`, plus a 512x512 transparent `assets/mosaico-logo.png` that the manifests point at) and
nothing else. It needs Mosaico server release 20261017a or later. Skills
only: the plugin bundles no Mosaico server, address or token. Versions before 1.0.0 were internal and are not
supported for customers.

## Tests

The tests are standalone scripts (no pytest needed):

```bash
python3 tests/test_connector_acting_skill.py
python3 tests/test_methodology_conversion_run_skill.py
python3 tests/test_public_package.py
```

Pass `--app-repo <path to the Mosaico application>` to the first two to also check them against the
application source.

## Public exposure boundary

Assume every file in this repository and every installed plugin file is public and inspectable.
The MCP tool names, descriptions and schemas are public contracts. All enforcement and proprietary
implementation remain on the Mosaico server.

## License

Copyright Mosaico Limited. See [LICENSE](LICENSE).
