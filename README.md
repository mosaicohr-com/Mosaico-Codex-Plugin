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

## Public exposure boundary

Assume every file in this repository and every installed plugin file is public and inspectable.
The MCP tool names, descriptions and schemas are public contracts. All enforcement and proprietary
implementation remain on the Mosaico server.

## License

Copyright Mosaico Limited. See [LICENSE](LICENSE).
