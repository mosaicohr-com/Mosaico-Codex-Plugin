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
        "`thread-not-found-in-window`",
        "Never call it \"no conversation\"",
        "`coverage`",
        "`pagesRead`",
        "up to 8 pages",
        "`outcome`",
        "`outcome-required`",
        "`draftsDiscarded`",
        "`evidence-altered`",
        "### Judge the Lead's latest message",
        "A no ends the Lead. Never draft a follow-up for a Lead who said no, never ask twice, never try to change the Lead's mind.",
        "choose `declined`",
        "Judge only the Lead's latest message, never an older one, never our own words and never the Lead's silence",
        "Mosaico moves the Lead to Drop",
        "Mosaico marks the Lead Warm",
        "do not use the by-eye fallback for it unless the person asks",
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

    # Rules Mosaico enforces, repair, and script output passed exactly as returned.
    whole_claude = flat(claude)
    for needle in (
        "`follow-up-declined`", "`follow-up-awaiting-reply`", "`follow-up-thread-unread`", "`awaiting-reply`", "`connection-accepted-no-reply`",
        "`repair_drafts`", "`repairSuggestions`", "`draftsDiscarded: [{ messageId, reason }]`", "Before drafting anything new",
        "never work around it", "`recapture`", "exactly as returned", "`integrity` included", "never retyped, trimmed, reformatted, translated or \"fixed\"",
        "`evidence-altered`", "(`status`, `signedIn`, `capturedAt`, `profileIdentifier`, `entries` and `integrity`)", "`{elements, entries, integrity}`",
        "how many drafts Mosaico discarded",
    ):
        check(needle in whole_claude, f"Claude follow-up-run skill lacks: {needle}")
    check("thread not found in window" in whole_claude, "Claude follow-up-run skill does not name the thread not found in window report")
    check("run **Capture the thread** for it and deposit with `outcome`" in whole_claude, "repair does not run the thread capture with an outcome")
    check("**Repair drafts first**" in check_follow and "**Repair drafts first**" in one_pass, "check and one-pass scopes do not do the repair first")
    check("`outcome`" in flat(check_follow) and "`outcome`" in one_pass, "check and one-pass scopes do not pass the outcome")
    for name in ("mosaico-outreach-invite-run", "mosaico-outreach"):
        text = flat((CLAUDE / f"skills/{name}/SKILL.md").read_text(encoding="utf-8"))
        check("exactly as returned" in text and "`integrity`" in text and "`evidence-altered`" in text, f"Claude {name} skill does not say to pass script output exactly as returned")
    invite = flat((CLAUDE / "skills/mosaico-outreach-invite-run/SKILL.md").read_text(encoding="utf-8"))
    check("(`status`, `signedIn`, `capturedAt`, `profileIdentifier`, `entries` and `integrity`)" in invite and "`recapture`" in invite, "Claude invite-run does not pass the whole connection evidence")

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
    whole_codex = flat(codex)
    for needle in (
        "`outcome`", "`outcome-required`", "### Judge the Lead's latest message", "A no ends the Lead. Never draft a follow-up for a Lead who said no, never ask twice, never try to change the Lead's mind.",
        "`follow-up-declined`", "`follow-up-awaiting-reply`", "`follow-up-thread-unread`", "`awaiting-reply`", "`repair_drafts`", "`repairSuggestions`", "`draftsDiscarded`",
        "never work around it", "how many drafts Mosaico discarded",
    ):
        check(needle in whole_codex, f"Codex follow-up-run skill lacks: {needle}")
    # The outcome checklist reads the same in both packages.
    def checklist(text: str) -> str:
        match = re.search(r"^### Judge the Lead's latest message\n(.*?)(?=^## |\Z)", text, re.S | re.M)
        check(match is not None, "missing the outcome checklist")
        return flat(match.group(1))
    check(checklist(claude) == checklist(codex), "the outcome checklist differs between the Claude and Codex skills")
    check("`threadEvidence`" not in checklist(codex), "Codex outcome checklist mentions script evidence")

    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json"):
        check(json.loads(manifest.read_text(encoding="utf-8"))["version"] == "0.8.1", f"{manifest.name} is not at 0.8.1")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    check("### 0.7.0" in readme and readme.index("### 0.8.1") < readme.index("### 0.8.0") < readme.index("### 0.7.1") < readme.index("### 0.7.0") < readme.index("### 0.6.1"), "README changelog lacks 0.8.1 above 0.8.0, 0.7.1, 0.7.0 and 0.6.1")
    check("linkedin-thread-messages.js" in readme, "README does not describe the thread script")
    entry = flat(readme[readme.index("### 0.8.1") : readme.index("### 0.8.0")])
    for needle in ("up to 8 pages", "`coverage`", "`outcome`", "no-pressure", "awaiting", "`draftsDiscarded`", "`repair_drafts`", "`integrity`", "`evidence-altered`"):
        check(needle in entry, f"README 0.8.1 entry lacks: {needle}")
    print("PASS: both follow-up-run skills handle thread evidence as designed (Claude reads it from data, Codex cannot) outcome, no-pressure, repair and integrity rules are stated, and the version is 0.8.1.")


if __name__ == "__main__":
    main()
