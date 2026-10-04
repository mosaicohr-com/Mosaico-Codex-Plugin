#!/usr/bin/env python3
"""A send is confirmed from LinkedIn's data: the skills run the approved script again after the send and pass it to
outreach_mark_message_sent; Codex cannot, so its sends are declared as by screen. No script or gate rule changed."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "plugins" / "mosaico-claude" / "skills"
CODEX = ROOT / "plugins" / "mosaico-codex" / "skills"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    check(match is not None, f"missing section {heading}")
    return match.group(1)


def read(root: Path, skill: str) -> str:
    return (root / skill / "SKILL.md").read_text(encoding="utf-8")


def main() -> None:
    invite = flat(section(read(CLAUDE, "mosaico-outreach-invite-run"), "Send approved invitations"))
    for needle in (
        "run the approved connection-evidence script again",
        "`sendEvidence`",
        "fresh `identityEvidence`",
        "`send-not-confirmed`",
        "Do not retype the note",
        "Retry the send once",
        "`outreach_record_delivery_block` with `reason: cannot-message`",
        "`send-evidence-stale`",
        "`send-evidence-before-send`",
        "`send-evidence-malformed`",
        "`send-evidence-lead-mismatch`",
        "Never mark an invitation sent from the screen alone",
        "`send-proof-missing`",
        "sends confirmed from data separately from any marked by screen",
    ):
        check(needle in invite, f"Claude invite-run send section lacks: {needle}")
    check("Verify each invitation against LinkedIn rather than trusting the click" not in invite,
          "Claude invite-run still verifies a send against the screen")

    follow = flat(section(read(CLAUDE, "mosaico-outreach-follow-up-run"), "Send approved drafts"))
    for needle in (
        "run the approved thread script again",
        "`threadEvidence`",
        "fresh `identityEvidence`",
        "`send-not-confirmed`",
        "Do not retype it",
        "Retry the send once",
        "`outreach_record_delivery_block` with `reason: cannot-message`",
        "`send-evidence-stale`",
        "`send-evidence-lead-mismatch`",
        "Never mark a message sent from the screen alone",
        "`send-proof-missing`",
        "count the sends confirmed from data separately from any marked by screen",
    ):
        check(needle in follow, f"Claude follow-up-run send section lacks: {needle}")
    check("Verify delivery on LinkedIn rather than trusting the click" not in follow,
          "Claude follow-up-run still verifies a send against the screen")
    one_pass = flat(section(read(CLAUDE, "mosaico-outreach-follow-up-run"), "One pass per thread"))
    check("confirm it from data" in one_pass and "`threadEvidence`" in one_pass and "`send-not-confirmed`" in one_pass
          and "from the screen alone" in one_pass, "One pass per thread does not confirm the send from data")

    for skill, scope in (("mosaico-outreach-invite-run", "Send approved invitations"), ("mosaico-outreach-follow-up-run", "Send approved drafts")):
        codex = flat(section(read(CODEX, skill), scope))
        check("Codex cannot run" in codex and "`send-proof-missing`" in codex and "reading of the screen" in codex,
              f"Codex {skill} does not declare its sends as by screen")
        check("`send-not-confirmed`" in codex and "do not retype it" in codex, f"Codex {skill} does not say what to do on send-not-confirmed")
        check("`sendEvidence`" not in codex.replace("cannot pass `sendEvidence`", "")
              and "`threadEvidence`" not in codex.replace("cannot pass `threadEvidence`", ""),
              f"Codex {skill} tells the model to pass send evidence it cannot produce")
    check("by screen" in flat(section(read(CODEX, "mosaico-outreach-follow-up-run"), "One pass per thread")),
          "Codex one pass per thread does not name its sends as by screen")

    # Browser scripts and the gate must not change in this release.
    changed = subprocess.run(
        ["git", "diff", "--name-only", "origin/main", "--", "plugins/mosaico-claude/browser", "plugins/mosaico-claude/hooks", "tests/test_browser_script_gate.py"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if changed.returncode == 0:
        check(changed.stdout.strip() == "", f"browser scripts or the gate changed: {changed.stdout.strip()}")
    print("PASS: both invite-run and follow-up-run skills confirm a send from LinkedIn's data (Claude) or declare it by screen (Codex).")


if __name__ == "__main__":
    main()
