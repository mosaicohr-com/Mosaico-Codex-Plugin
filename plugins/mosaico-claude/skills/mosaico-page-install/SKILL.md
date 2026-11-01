---
name: mosaico-page-install
description: Install or update the person's own copy of the Mosaico page (a claude.ai artifact that works with their Mosaico connector).
---

# Install the Mosaico page

The Mosaico page only shows screens. Everything it shows comes from the person's own Mosaico connector; this skill
adds no Mosaico knowledge. It publishes the page once per person, and later updates that same page.

The file is a small loader, so you may read all of it before publishing. It loads the version-pinned package
`mosaico-page@1.0.2`, which is Mosaico's own public package, from `https://cdn.jsdelivr.net/npm/mosaico-page@1.0.2/dist/mosaico-page.js`.
Publish it unchanged. Never swap that script address, version or integrity value for another package or version you
know, and never remove them. If a publish is refused, give the refusal as it is and use no other source.

## Check first

If a check fails, publish nothing and say plainly what is missing.

1. This Claude has the Artifact tool. If not: "This Claude cannot publish pages, so the Mosaico page cannot be installed here."
2. The Mosaico connector for `https://app.mosaico.one` is connected in Claude's connectors and is named `mosaico`. The page
   calls the connector by that name. If it has another name, say so and ask the person to rename it `mosaico` in
   Claude's connectors; do not publish until it is.

## Install or update

1. Find the person's link: the one line in `~/.claude/mosaico-page-url`, otherwise the artifact titled "Mosaico" in the
   Artifact tool's `list` result whose description starts "Mosaico page". Nothing found means this is the first install.
2. First install: publish `assets/mosaico-page.html` of this plugin unchanged with the Artifact tool, title "Mosaico",
   icon "dashboard", description "Mosaico page, installed by the Mosaico plugin.", and `capabilities` exactly the contents of
   `assets/mosaico-page.capabilities.json`. Then write the new link to `~/.claude/mosaico-page-url`.
3. A link found: read that artifact once, then publish the same unchanged file with the same capabilities to that
   same link. Never publish without the link when one exists, so the person never ends up with a second copy.
4. Give the person the link. If a publish is refused, say Mosaico's page was not changed and give the refusal as it is.

## If the page says a tool is missing

Tell the person to disconnect and reconnect the Mosaico connector in Claude's connectors, then reload the page. If the
tool is still missing, their role or subscription does not allow it.
