#!/usr/bin/env python3
"""A send is confirmed from LinkedIn's data: the skills run an approved script after the send and pass it to
outreach_mark_message_sent (an invitation: the sent-invitations script as sentInvitationEvidence; a follow-up: the
thread script as threadEvidence); Codex cannot, so its sends are declared as by screen. The one script this release
adds is the sent-invitations script; no gate rule changed."""

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
        "run the approved sent-invitations script with the Lead's public identifier after the send and pass its output exactly as returned as `sentInvitationEvidence`",
        "only its Sent invitations list can",
        "`send-evidence-cannot-prove`",
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
    check("run the approved connection-evidence script again" not in invite, "Claude invite-run still confirms a send from the profile call")
    whole = flat(read(CLAUDE, "mosaico-outreach-invite-run"))
    check("## Capture the sent invitation" in read(CLAUDE, "mosaico-outreach-invite-run") and "browser/linkedin-sent-invitations.js" in whole,
          "Claude invite-run has no procedure for the sent-invitations script")
    check(whole.count("`sendEvidence`") == 1 and "Do not pass `sendEvidence`" in whole, "Claude invite-run tells the model to pass sendEvidence")

    follow = flat(section(read(CLAUDE, "mosaico-outreach-follow-up-run"), "Send approved drafts"))
    for needle in (
        "run the approved thread script again",
        "`threadEvidence`",
        "the script's output exactly as returned (`integrity` included) as `threadEvidence`",
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
        check("`sendEvidence`" not in codex and "`sentInvitationEvidence`" not in codex.replace("cannot pass `sentInvitationEvidence`", "")
              and "`threadEvidence`" not in codex.replace("cannot pass `threadEvidence`", ""),
              f"Codex {skill} tells the model to pass send evidence it cannot produce")
    check("by screen" in flat(section(read(CODEX, "mosaico-outreach-follow-up-run"), "One pass per thread")),
          "Codex one pass per thread does not name its sends as by screen")

    # 0.8.4 changes the gate (the run directive) and no approved browser script.
    changed = subprocess.run(
        ["git", "diff", "--name-only", "origin/main", "--", "plugins/mosaico-claude/browser", "plugins/mosaico-claude/hooks"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if changed.returncode == 0:
        files = set(changed.stdout.split())
        gate = {"plugins/mosaico-claude/hooks/browser-script-gate.py"}
        check(files <= gate, f"a file other than the gate changed, or an approved browser script changed: {sorted(files - gate)}")
    print("PASS: both invite-run and follow-up-run skills confirm a send from LinkedIn's data (Claude) or declare it by screen (Codex).")


if __name__ == "__main__":
    main()
