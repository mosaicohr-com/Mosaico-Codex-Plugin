#!/usr/bin/env python3
"""The schedule-install skills describe the two Outreach schedules and refuse unsafe installs."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "plugins" / "mosaico-claude"
CODEX = ROOT / "plugins" / "mosaico-codex"
SKILLS = {
    "Claude": (CLAUDE / "skills" / "mosaico-outreach-schedule-install" / "SKILL.md").read_text(encoding="utf-8"),
    "Codex": (CODEX / "skills" / "mosaico-outreach-schedule-install" / "SKILL.md").read_text(encoding="utf-8"),
}

TITLES = (
    "Mosaico Outreach — Sync data (connections and messaging)",
    "Mosaico Outreach — Source leads",
)
OUTREACH_SKILLS = (
    "mosaico-outreach-invite-run",
    "mosaico-outreach-follow-up-run",
    "mosaico-outreach-lead-management",
    "mosaico-outreach-agent-management",
)
FORBIDDEN = ("Connect means", "Message means", "Pending means", "already-connected", "invite-pending")
ALLOW_RULES = ("mcp__Claude_Browser__javascript_tool", "mcp__Claude_Browser__computer")
OLD_AUTOMATIONS = (
    "~/.codex/automations/daily-approved-outreach-sends",
    "~/.codex/automations/mosaico-lead-preparation",
)
SCRIPTS = ("browser/linkedin-whoami.js", "browser/linkedin-connection-evidence.js", "browser/linkedin-recent-connections.js")
STALE_DIRS = ("~/.codex/skills/", "~/.claude/skills/")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> None:
    for package, text in SKILLS.items():
        for title in TITLES:
            check(title in text, f"{package} skill is missing the schedule title: {title}")
        for name in OUTREACH_SKILLS:
            for match in re.finditer(re.escape(name), text):
                check(text[: match.start()].endswith("mosaico:"), f"{package} skill names {name} without the mosaico: prefix")
        check(any(f"mosaico:{name}" in text for name in OUTREACH_SKILLS[:2]), f"{package} skill never names a qualified skill")
        for phrase in FORBIDDEN:
            check(phrase not in text, f"{package} skill contains forbidden phrase: {phrase}")
        reasons = re.findall(r"outreach_record_delivery_block with reason (\S+)", text)
        check(all(reason == "cannot-message" for reason in reasons), f"{package} skill records a delivery block for another reason")
        for directory in STALE_DIRS:
            check(directory in text, f"{package} skill does not check {directory} for stale copies")
        for path in OLD_AUTOMATIONS:
            check(path in text, f"{package} skill does not name the old Codex automation {path}")
        check("_archived" in text and "mv " in text, f"{package} skill does not give the archive command")

    claude = SKILLS["Claude"]
    for rule in ALLOW_RULES:
        check(rule in claude, f"Claude skill does not name the allow rule {rule}")
    check("permissions.allow" in claude and "~/.claude/settings.json" in claude, "Claude skill does not name the settings file")
    check("cannot write that file" in claude, "Claude skill does not say the plugin cannot write the settings file")
    for script in SCRIPTS:
        check(script in claude, f"Claude skill does not name the approved script {script}")
    check("60 minutes" in claude, "Claude skill does not keep the schedules 60 minutes apart")

    codex = SKILLS["Codex"]
    check("cannot capture connection evidence" in codex, "Codex skill does not say it cannot capture connection evidence")
    check("must not send" in codex, "Codex skill does not forbid a Codex-installed Sync data schedule from sending")
    check("mcp__Claude_Browser__" not in codex, "Codex skill mentions the Claude browser permissions")

    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        overview = (root / "skills" / "mosaico-outreach" / "SKILL.md").read_text(encoding="utf-8")
        for old in ("8:00 AM", "8:00 PM"):
            check(old not in overview, f"{package} overview skill still mentions {old}")
        check("mosaico:mosaico-outreach-schedule-install" in overview, f"{package} overview does not name the qualified schedule-install skill")
        check("Sync data" in overview and "Source leads" in overview, f"{package} overview does not describe the two schedules")
    codex_overview = (CODEX / "skills" / "mosaico-outreach" / "SKILL.md").read_text(encoding="utf-8")
    check("installed from Claude" in codex_overview, "Codex overview does not say Sync data is installed from Claude")

    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json"):
        check(json.loads(manifest.read_text(encoding="utf-8"))["version"] == "0.6.0", f"{manifest.name} is not at 0.6.0")
    print("PASS: both schedule-install skills describe the two schedules, qualified skill names and the stale-copy checks.")


if __name__ == "__main__":
    main()
