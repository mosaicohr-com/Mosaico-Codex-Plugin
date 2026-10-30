#!/usr/bin/env python3
"""The Routines Board page (Claude package only) keeps the document shape the thin skills point at.

The invite-run and follow-up-run skills say: when the routine text has a `routines board:` line, write the run to that board in one batch
after the report, in the shape the page's header comment gives. A failed board write is one line in the report, never a halt (rule R098).
"""

from __future__ import annotations

from skill_text import CLAUDE, CODEX, FOLLOW_UP, INVITE, check, flat, read, skill


def main() -> None:
    board = read(CLAUDE / "assets" / "routines-board.html")
    for needle in (
        "<title>Outreach Routines Board</title>", "DATABASE SCHEMA (db capability)", "runs/<id>", "actions/<id>", "issues/<id>", "improvements/<id>", "meta/board",
        '"follow-up" | "send-invitations" | "load-leads" | "withdraw"', "only Editors/Owner (admin) write",
        "WRITING (a routine records its run", "pass its version as if_version", "one batch", "never a retry loop and never a halt", "Routines Board not updated: <reason>",
        "act-<slug>-<yyyymmdd>", "iss-<slug>", "never write improvements", "sched-<routine key>-", "recorded by the Routines report",
    ):
        check(needle in board, f"the board page lacks: {needle}")
    check(not (CODEX / "assets").exists() and not list(CODEX.rglob("routines-board*")), "the Codex package carries the board page")
    for package in ("Codex",):
        for name in (INVITE, FOLLOW_UP):
            check("Routines Board" not in skill(package, name), f"the {package} {name} skill mentions the Routines Board")
    for name in (INVITE, FOLLOW_UP):
        text = flat(skill("Claude", name))
        for needle in ("routines board:", "ArtifactData", "one batch", "assets/routines-board.html", "never a halt"):
            check(needle in text, f"the Claude {name} skill lacks: {needle}")
    print("PASS: the Routines Board page carries the document shape and the writing rules the Claude skills point at; the Codex package carries neither the page nor the board step.")


if __name__ == "__main__":
    main()
