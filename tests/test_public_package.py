#!/usr/bin/env python3
"""The public Mosaico plugin carries three skills and no internal tooling.

Customers receive everything in this repository, so nothing about Mosaico's internal staff tooling may be in it: no skills, browser
scripts, hooks, keywords, example prompts or documentation. The internal tool's name is spelled in two halves below so this file
stays clean too. Both packages also keep the same three skills, and both manifests
are at the first customer release.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "plugins" / "mosaico-claude"
CODEX = ROOT / "plugins" / "mosaico-codex"
SKILLS = {"mosaico", "mosaico-methodology-convert", "mosaico-methodology-conversion-run"}
VERSION = "1.0.0"
FORBIDDEN_WORDS = ("out" + "reach", "linkedin", "salesnav", "browser-script")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> None:
    for package in (CLAUDE, CODEX):
        found = {path.name for path in (package / "skills").iterdir()}
        check(found == SKILLS, f"{package.name} skills are {sorted(found)}, not {sorted(SKILLS)}")
    for gone in (CLAUDE / "browser", CLAUDE / "hooks", ROOT / "plugins" / "mosaico-claude" / "hooks" / "hooks.json"):
        check(not gone.exists(), f"{gone.relative_to(ROOT)} must not ship in the public plugin")
    check(not list(ROOT.rglob(".mcp.json")), "the plugin ships a .mcp.json: it must bundle no Mosaico server")

    scanned = [ROOT / "README.md", ROOT / ".claude-plugin" / "marketplace.json", ROOT / ".agents" / "plugins" / "marketplace.json"]
    scanned += [path for package in (CLAUDE, CODEX) for path in package.rglob("*") if path.is_file() and path.suffix in {".md", ".json", ".js", ".py", ".svg"}]
    for path in scanned:
        text = path.read_text(encoding="utf-8").lower()
        for word in FORBIDDEN_WORDS:
            check(word not in text, f"{path.relative_to(ROOT)} mentions {word}")

    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json"):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        check(data["name"] == "mosaico" and data["version"] == VERSION, f"{manifest.name} is not mosaico {VERSION}")
        check("mcpServers" not in data, f"{manifest.name} bundles a Mosaico server")
        check("hooks" not in data, f"{manifest.name} declares hooks")
    prompts = json.loads((CODEX / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))["interface"]["defaultPrompt"]
    check(len(prompts) == 2, f"the Codex plugin has {len(prompts)} default prompts, not 2")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    check("### 1.0.0" in readme and "first customer release" in readme, "README does not say 1.0.0 is the first customer release")
    print("PASS: both packages carry exactly the three public skills, no browser scripts, hooks or internal wording, and are at 1.0.0 as the first customer release.")


if __name__ == "__main__":
    main()
