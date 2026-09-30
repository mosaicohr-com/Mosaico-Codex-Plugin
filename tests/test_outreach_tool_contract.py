#!/usr/bin/env python3
"""Fail when either Outreach plugin names a tool absent from the application registry."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


TOOL_REFERENCE = re.compile(r"`(outreach_[a-z0-9_]+)`")
REGISTERED_TOOL = re.compile(r"(?:name|toolName):\s*'(?P<name>outreach_[a-z0-9_]+)'")
REGISTRY_FILES = (
    "features/outreach/server/outreach-mcp-registry.ts",
    "features/outreach/server/outreach-transfer-tool.ts",
)
REQUIRED_TOOLS = {"outreach_start_run"}


def referenced_tools(skill_root: Path) -> set[str]:
    return {
        tool
        for skill in skill_root.glob("*/SKILL.md")
        for tool in TOOL_REFERENCE.findall(skill.read_text(encoding="utf-8"))
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--app-repo",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "mosaico-app",
        help="Path to the mosaico-app checkout that owns the MCP registry.",
    )
    args = parser.parse_args()
    plugin_root = Path(__file__).resolve().parents[1] / "plugins"
    codex = referenced_tools(plugin_root / "mosaico-codex" / "skills")
    claude = referenced_tools(plugin_root / "mosaico-claude" / "skills")
    if codex != claude:
        raise SystemExit(
            "Provider Outreach tool references differ: "
            f"Codex-only={sorted(codex - claude)}, Claude-only={sorted(claude - codex)}"
        )

    registered: set[str] = set()
    for relative in REGISTRY_FILES:
        registry_path = args.app_repo.resolve() / relative
        if not registry_path.is_file():
            raise SystemExit(f"Application Outreach registry not found: {registry_path}")
        registered |= set(REGISTERED_TOOL.findall(registry_path.read_text(encoding="utf-8")))
    unused = REQUIRED_TOOLS - codex
    if unused:
        raise SystemExit(f"Skills never start a run: missing {sorted(unused)}")
    for skill in plugin_root.glob("*/skills/*/SKILL.md"):
        for number, line in enumerate(skill.read_text(encoding="utf-8").splitlines(), 1):
            if "ownerUserId" in line and not re.search(r"(Never|Do not) pass", line):
                raise SystemExit(f"{skill}:{number} tells the model about ownerUserId")
    missing = codex - registered
    if missing:
        raise SystemExit(
            "Plugin references unavailable Outreach MCP tools: "
            + ", ".join(sorted(missing))
        )
    print(
        f"PASS: {len(codex)} Outreach tools referenced identically by Codex and Claude "
        "are registered by mosaico-app."
    )


if __name__ == "__main__":
    main()
