"""Shared helpers for the Outreach skill tests: where the skills are and how to read them."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "plugins" / "mosaico-claude"
CODEX = ROOT / "plugins" / "mosaico-codex"
PACKAGES = {"Claude": CLAUDE, "Codex": CODEX}

VERSION = "0.11.1"  # the plugin version; the server's OUTREACH_PLUGIN_VERSION is the same
CATALOGUE_VERSION = "2026-10-27.4"  # the server's OUTREACH_ROUTINE_CATALOGUE_VERSION this plugin expects

HUB = "mosaico-outreach"
INVITE = "mosaico-outreach-invite-run"
FOLLOW_UP = "mosaico-outreach-follow-up-run"
SCHEDULE = "mosaico-outreach-schedule-install"
AGENTS = "mosaico-outreach-agent-management"
LEADS = "mosaico-outreach-lead-management"
OUTREACH_SKILLS = (HUB, INVITE, FOLLOW_UP, SCHEDULE, AGENTS, LEADS)

# The one limit Outreach has, in the one sentence the hub skill says it.
LIMIT_SENTENCE = "The one limit is 20 invitation sends per owner per day, which Mosaico enforces."


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def skill_path(package: str, name: str) -> Path:
    return PACKAGES[package] / "skills" / name / "SKILL.md"


def skill(package: str, name: str) -> str:
    return read(skill_path(package, name))


def flat(text: str) -> str:
    """One line, no backticks: what a sentence says, whatever way the file wraps it."""
    return " ".join(text.replace("`", "").split())


def words(text: str) -> int:
    return len(text.split())


def section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    check(match is not None, f"missing section: {heading}")
    return match.group(1)


def manifests() -> dict[str, dict]:
    return {
        "Claude": json.loads(read(CLAUDE / ".claude-plugin" / "plugin.json")),
        "Codex": json.loads(read(CODEX / ".codex-plugin" / "plugin.json")),
    }
