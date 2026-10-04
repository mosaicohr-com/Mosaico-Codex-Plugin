#!/usr/bin/env python3
"""The follow-up-run skills read threads from LinkedIn's data in Claude and say plainly that Codex cannot."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "plugins" / "mosaico-claude"
CODEX = ROOT / "plugins" / "mosaico-codex"
SKILL = "skills/mosaico-outreach-follow-up-run/SKILL.md"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    check(match is not None, f"missing section {heading}")
    return match.group(1)


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def main() -> None:
    claude = (CLAUDE / SKILL).read_text(encoding="utf-8")
    codex = (CODEX / SKILL).read_text(encoding="utf-8")

    thread = flat(section(claude, "Capture the thread"))
    for needle in (
        "browser/linkedin-thread-messages.js",
        "`threadEvidence`",
        "`identityEvidence`",
        "`outreach_deposit_conversation`",
        "exactly as returned",
        "built-in browser pane",
        "Never pass `messages` with it",
        "by-eye deposit is the fallback",
        "say in the final report which Leads were read by eye",
        "changing only the value on its first line to the Lead's public identifier",
        "`no-conversation`",
    ):
        check(needle in thread, f"Claude thread section lacks: {needle}")
    check_follow = section(claude, "Check for new follow-ups")
    check("**Capture the thread**" in check_follow and "`threadEvidence`" in check_follow and "fresh `identityEvidence`" in check_follow,
          "Check for new follow-ups does not pass threadEvidence with fresh identityEvidence")
    check("say so in the report" in flat(check_follow), "Check for new follow-ups does not require the report to say so")
    one_pass = flat(section(claude, "One pass per thread"))
    check("**Capture the thread**" in one_pass and "`threadEvidence`" in one_pass and "fresh `identityEvidence`" in one_pass,
          "One pass per thread does not pass threadEvidence with fresh identityEvidence")
    check("only when the script cannot run" in one_pass, "One pass per thread does not limit the by-eye deposit to a script that cannot run")
    check("say so in the report" in one_pass, "One pass per thread does not require the report to say so")
    check("Do not search LinkedIn lists" in claude, "lost the no-list-search rule")

    codex_thread = flat(section(codex, "Capture the thread"))
    for needle in (
        "linkedin-thread-messages.js",
        "Claude's built-in browser pane",
        "sandboxed",
        "cannot run it",
        "Do not pass `threadEvidence`",
        "by eye",
    ):
        check(needle in codex_thread, f"Codex thread section lacks: {needle}")
    check("read by eye" in flat(section(codex, "Check for new follow-ups")), "Codex check scope does not report threads as read by eye")
    check("by-eye form" in flat(section(codex, "One pass per thread")), "Codex one-pass scope does not name the by-eye form")

    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json"):
        check(json.loads(manifest.read_text(encoding="utf-8"))["version"] == "0.7.1", f"{manifest.name} is not at 0.7.1")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    check("### 0.7.0" in readme and readme.index("### 0.7.1") < readme.index("### 0.7.0") < readme.index("### 0.6.1"), "README changelog lacks 0.7.0 above 0.6.1")
    check("linkedin-thread-messages.js" in readme, "README does not describe the thread script")
    print("PASS: both follow-up-run skills handle thread evidence as designed (Claude reads it from data, Codex cannot) and the version is 0.7.1.")


if __name__ == "__main__":
    main()
