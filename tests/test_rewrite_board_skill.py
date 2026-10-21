#!/usr/bin/env python3
"""0.9.24: rewrite work for returned drafts, the Routines Board write, the Routines report routine and the new default schedule times.

Needs the Mosaico release that ships PRs 2053, 2057 and 2058 (not yet promoted). The application owns what is rewrite work and in which order;
these checks pin that the skills work the items as the application orders them, never approve, and leave a record on the board only when the
schedule text carries a board address, without ever holding back the run's own report.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "plugins" / "mosaico-claude"
CODEX = ROOT / "plugins" / "mosaico-codex"
VERSION = "0.9.24"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flat(text: str) -> str:
    return " ".join(text.replace("`", "").split())


def section(text: str, name: str) -> str:
    match = re.search(rf"^## {re.escape(name)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    check(match is not None, f"missing section: {name}")
    return match.group(1)


def main() -> None:
    # Version, README entry and the page asset.
    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json"):
        check(json.loads(read(manifest))["version"] == VERSION, f"{manifest.name} is not at {VERSION}")
    readme = read(ROOT / "README.md")
    check(readme.index(f"### {VERSION}") < readme.index("### 0.9.23"), f"README changelog lacks {VERSION} above 0.9.23")
    entry = flat(readme[readme.index(f"### {VERSION}"):readme.index("### 0.9.23")])
    for needle in (
        "the Mosaico release that ships PRs 2053, 2057 and 2058; not yet promoted", "Do not tag, publish or install", "rewrite_returned_invitation_draft", "sendRun.rewrites", "sendRun.rewriteCount",
        "rewrite-limit-reached", "rewrite-draft", "rewrite_follow_up_draft", "counts.rewrite", "existing messageId", "never approves", "Record the run on the Routines Board", "routines board: https://claude.ai/artifact/<id>",
        "ArtifactData", "Routines report", "45 6,23 * * *", "45 18,22 * * *", "30 23 * * *", "0 0,3 * * *", "30 1,4 * * *", "0 6 * * *", "installed paused", "review window",
        "plugins/mosaico-claude/assets/routines-board.html", "does not get it", "30 minutes", "90 minutes",
    ):
        check(needle in entry, f"README {VERSION} entry lacks: {needle}")
    check("## Current state (0.9.24)" in readme, "README lacks the 0.9.24 current state")
    board = read(CLAUDE / "assets" / "routines-board.html")
    for needle in ("<title>Outreach Routines Board</title>", "DATABASE SCHEMA (db capability)", "runs/<id>", "actions/<id>", "issues/<id>", "meta/board", '"follow-up" | "send-invitations" | "source-own" | "source-colleagues" | "withdraw"',
                   "only Editors/Owner (admin) write"):
        check(needle in board, f"the board page lacks: {needle}")
    check(not (CODEX / "assets").exists() and not list(CODEX.rglob("routines-board*")), "the Codex package carries the board page")

    invite = {"Claude": read(CLAUDE / "skills" / "mosaico-outreach-invite-run" / "SKILL.md"), "Codex": read(CODEX / "skills" / "mosaico-outreach-invite-run" / "SKILL.md")}
    follow = {"Claude": read(CLAUDE / "skills" / "mosaico-outreach-follow-up-run" / "SKILL.md"), "Codex": read(CODEX / "skills" / "mosaico-outreach-follow-up-run" / "SKILL.md")}

    # 1. Rewrite: invitation drafts (both packages hold the same section text).
    rewrite = {package: section(text, "Rewrite returned invitation drafts") for package, text in invite.items()}
    check(rewrite["Claude"] == rewrite["Codex"], "the two packages hold different Rewrite returned invitation drafts sections")
    flat_rewrite = flat(rewrite["Claude"])
    for needle in (
        "checklist-changed or instructions-changed", "rewrite_returned_invitation_draft", "every scheduled day", "sendRun.rewrites lists up to 50 items", "leadId, name, messageId, kind, day, agentId, agentName, body (the draft as it stands), reason, basis, returnedAt and recommendedCall",
        "sendRun.next.rewrite", "sendRun.remaining.rewrite", "sendRun.rewriteCount", "outreach_record_message with the existing messageId", "checklistReview", "runId", "keeps the kind, the day and any booked day",
        "never creates a second unsent draft", "Never approve, send or mark sent a rewritten draft", "share the run's draft limit", "go first", "rewrite-limit-reached", "sendRun.rewritesThisRun",
        "the drafts rewritten (the count, and each with its Lead name and day)",
    ):
        check(needle in flat_rewrite, f"the Rewrite returned invitation drafts section lacks: {needle}")
    for package, text in invite.items():
        both = flat(section(text, "Both"))
        check("sends come first, then rewrites of returned drafts, then connection checks, then drafts" in both, f"{package} Both section does not put the rewrites after the sends")
        check("Rewrite returned invitation drafts" in both, f"{package} Both section does not send the run to the rewrite section")
        check(text.index("## Rewrite returned invitation drafts") < text.index("## Write missing invitation drafts"), f"{package} rewrite section is not before the draft section")
    send = flat(section(invite["Claude"], "Send invitations routine"))
    for needle in ("rewrite_returned_invitation_draft means rewrite that draft in place", "record it with the existing messageId, never a new one", "and never approve it", "rewrite-limit-reached",
                   "invitation drafts rewritten (sendRun.rewritesThisRun, with the count, each Lead's name and day)", "or rewrite-limit-reached)"):
        check(needle in send, f"Send invitations routine lacks: {needle}")

    # 2. Rewrite: follow-up drafts (the Claude queue section and routine, the Codex note).
    queue = flat(section(follow["Claude"], "The follow-up queue (intent `follow_up_pass`)"))
    for needle in (
        "6. rewrite-draft (nextStep rewrite_follow_up_draft)", "between send-approved and draft", "rewriteDraft (messageId, kind, body, reason, basis, returnedAt, sendNotBefore)", "readConversationCall first",
        "the invitation actually sent is in it", "without repeating the words of the invitation that was sent", "existing messageId", "Never approve or send it", "counts.rewrite", "7. draft (draft_follow_up)", "8. held (sort_in_application)",
    ):
        check(needle in queue, f"the follow-up queue section lacks: {needle}")
    routine = flat(section(follow["Claude"], "Follow-up routine"))
    for needle in ("For a rewrite-draft item (nextStep rewrite_follow_up_draft, between send-approved and draft), make its readConversationCall first", "the invitation actually sent is in the thread",
                   "never repeating the words of the invitation", "outreach_record_message with the existing messageId", "Never approve a rewritten draft and never send one written in this run",
                   "follow-up drafts rewritten after an Agent change (the count, and each Lead's name"):
        check(needle in routine, f"Follow-up routine lacks: {needle}")
    codex_queue = flat(section(follow["Codex"], "The follow-up queue"))
    check("rewrite-draft" in codex_queue and "rewrite_follow_up_draft" in codex_queue and "read its thread first" in codex_queue and "never approve it" in codex_queue, "the Codex follow-up queue note lacks the rewrite-draft stage")

    # 3. The board write: one shared section per skill, a last step in every routine, silent skip, never blocking.
    board_sections = {"invite-run": section(invite["Claude"], "Record the run on the Routines Board"), "follow-up-run": section(follow["Claude"], "Record the run on the Routines Board")}
    for where, text in board_sections.items():
        f = flat(text)
        for needle in (
            "routines board: https://claude.ai/artifact/<id>", "skip this whole step silently", "ArtifactData tool with ToolSearch (select:ArtifactData)", "Every call takes the board address as url",
            "one batch", "id = this run's runId", "id, routine, startedAt and endedAt (ISO 8601, UTC), outcome (complete, blocked, nothing-to-do, failed or refused-busy:", "headline (one sentence)",
            "counts (an object of named numbers", "notes (an array of short strings)", "reportText (this run's final report, plain text",
            "id act-<slug>-<yyyymmdd>", "createdAt", "status open", "source (the run's id)", "id iss-<slug>", "firstSeenAt (kept as it is when the document exists, otherwise now)", "lastSeenAt (now)", "fixRef",
            "meta/board: id board, lastUpdatedAt (now) and lastUpdatedBy", "Keep the states object", "never write improvements",
            "get each document you may update", "passes that number as if_version", "A failed write never blocks the report", "Routines Board not updated: <reason>",
        ):
            check(needle in f, f"{where} board section lacks: {needle}")
    check("`source-own` or `source-colleagues`" in board_sections["invite-run"] and "`send-invitations`" in board_sections["invite-run"] and "`withdraw`" in board_sections["invite-run"], "invite-run board section lacks the routine keys")
    check("`follow-up`" in board_sections["follow-up-run"], "follow-up-run board section lacks the follow-up key")
    for name, source, last in (("Source leads routine", invite["Claude"], "source-own"), ("Send invitations routine", invite["Claude"], "send-invitations"), ("Withdraw stale invitations routine", invite["Claude"], "withdraw"), ("Follow-up routine", follow["Claude"], "follow-up")):
        body = section(source, name)
        steps = re.findall(r"^Step (\d+)\. ([^\n]*)", body, re.M)
        number, text = steps[-1]
        check(text.startswith("Record the run on the Routines Board") and last in text, f"{name} does not end with the Routines Board step")
        check("skip this step silently" in text and "routines board:" in text and "never a halt" in text and "one batch" in text, f"{name} board step does not skip silently and never halt")
        check(number == str(len(steps)), f"{name} steps are not numbered in order")
        check(body.index("Step 6." if name != "Follow-up routine" else "Step 4.") < body.index("Guards:"), f"{name} board step is after the guards")
    for package in ("Codex",):
        check("Routines Board" not in invite[package] and "Routines Board" not in follow[package], "the Codex package mentions the Routines Board")

    # 4. The Routines report routine.
    report = flat(section(follow["Claude"], "Routines report routine"))
    for needle in (
        "safety net for the person's Routines Board", "touches no Mosaico record, opens no LinkedIn page, starts no Outreach run", "needs no Mosaico connector", "No Routines Board address in this schedule; nothing to do.",
        "ToolSearch (select:ArtifactData)", "list_scheduled_tasks", "list_task_runs", "follow-up, send-invitations, withdraw, source-own and source-colleagues", "Ignore this task itself, the Repair task",
        "already holds a runs document of that routine", "sched-<routine key>-", "a run with no report, or one that stopped before it ended, is failed", "Invent nothing", "one batch", "This routine writes no runs document of its own and never writes improvements",
        "Guards: this routine is read-only everywhere except the Routines Board",
    ):
        check(needle in report, f"the Routines report routine lacks: {needle}")
    check("Routines report routine" in follow["Claude"].split("## Sync data routine")[0] and follow["Claude"].index("## Routines report routine") < follow["Claude"].index("## Sync data routine (superseded)"), "the Routines report section is misplaced")
    check("Routines report" not in follow["Codex"], "the Codex follow-up skill holds the Routines report routine")

    # 5. The installer: times, board, review window, paused Withdraw, Routines report task.
    installer = read(CLAUDE / "skills" / "mosaico-outreach-schedule-install" / "SKILL.md")
    flat_installer = " ".join(installer.split())
    texts = re.findall(r"```text\n(.*?)\n```", installer, re.S)
    check(len(texts) == 7, f"the installer holds {len(texts)} schedule texts, not seven")
    for text in texts[:6]:
        check(re.search(r"\n\nroutines board: <board url>(\n|$)", text) is not None, "a routine text lacks the board line as its own paragraph")
    check("routines board:" not in texts[6], "the Repair text carries a board line")
    check("This is the Routines report routine" in texts[5] and "(0.9.24 or later)" in texts[5], "the sixth text is not the Routines report text")
    for needle in (
        "Mosaico Outreach — Routines report", "`45 6,23 * * *`", "`45 18,22 * * *`", "`30 23 * * *`", "`0 0,3 * * *`", "`30 1,4 * * *`", "`0 6 * * *`", "`0 10 * * 0`",
        "installed paused (disabled) until the person has tested it", "enable it only on their word", "the person reviews and approves drafts between 7:00 PM and 10:30 PM",
        "the 6:45 PM Follow-up drafts for that review, the 10:45 PM Follow-up sends what was approved, Send invitations sends in the morning and drafts the coming days",
        "### Ask once about the review window", "15 minutes before the window starts and the second is 15 minutes after it ends", "shift only the two Follow-up times",
        "at least 30 minutes from every other start of these, and the two Source leads lanes sit 90 minutes apart",
        "## The Routines Board", "If any carries a `routines board: https://claude.ai/artifact/<id>` line, that address is the person's board: reuse it for every text and publish nothing",
        "assets/routines-board.html", "publish that file unchanged with the Artifact tool", 'title "Outreach Routines Board", icon `dashboard`', "the Codex package does not carry it",
        "Append the single line `routines board: <url>` as its own paragraph to every routine text", "Read each saved text back and confirm that it ends with the line", "A routine whose text has no board line skips the board silently",
        "that every routine text except Repair ends with the same `routines board:` line", "that the Routines report task exists with the cron `45 6,23 * * *`",
    ):
        check(needle in flat_installer, f"the installer lacks: {needle}")
    capabilities = re.search(r"```json\n\s*(\{\s*\"db\".*?\})\s*\n\s*```", installer, re.S)
    check(capabilities is not None, "the installer does not give the board's capabilities")
    declared = json.loads(capabilities.group(1))
    check(set(declared) == {"db", "user"}, f"the board's capabilities are not db and user: {sorted(declared)}")
    rules = {rule["path"]: rule for rule in declared["db"]["rules"]}
    check(set(rules) == {"runs", "actions", "issues", "improvements", "meta"} and all(rule["read"] == "view" and rule["write"] == "admin" for rule in rules.values()), "the board's db rules are not read-for-all, write-admin on the five collections")
    check("Codex" not in flat_installer.split("## The Routines Board")[1].split("## Install")[0].replace("the Codex package does not carry it", "").replace("the Codex package", ""), "the board section talks about Codex beyond saying it does not carry the page")
    codex_installer = read(CODEX / "skills" / "mosaico-outreach-schedule-install" / "SKILL.md")
    check("routines board" not in codex_installer.lower() and "Routines report" not in codex_installer, "the Codex installer mentions the board")
    # Defaults are internally consistent: the spacing is the one the installer states.
    crons = {"send": "0 6 * * *", "own": "0 0,3 * * *", "colleagues": "30 1,4 * * *", "follow": "45 18,22 * * *", "withdraw": "30 23 * * *"}
    starts = []
    for name, cron in crons.items():
        minute, hours = cron.split()[:2]
        starts += [(name, int(hour) * 60 + int(minute)) for hour in hours.split(",")]
    for index, (a_name, a) in enumerate(starts):
        for b_name, b in starts[index + 1:]:
            gap = min(abs(a - b), 1440 - abs(a - b))
            check(gap >= (90 if {a_name, b_name} == {"own", "colleagues"} else 30), f"{a_name} and {b_name} are too close ({gap} minutes)")

    # 6. The overview names the new times and the board.
    for needle in ("6:00 AM every day", "6:45 PM and 10:45 PM", "11:30 PM, installed paused", "Routines report", "Routines Board"):
        check(needle in " ".join(read(CLAUDE / "skills" / "mosaico-outreach" / "SKILL.md").split()), f"the Claude overview lacks: {needle}")

    print(f"PASS: both packages work rewrite items as Mosaico orders them and never approve; every Claude routine ends with the Routines Board step; the Routines report, the board page, the new default times and the review window are in the installer; plugin is at {VERSION}.")


if __name__ == "__main__":
    main()
