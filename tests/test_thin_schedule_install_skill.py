#!/usr/bin/env python3
"""0.10.0: the schedule installer takes routines, texts, times and steps only from outreach_get_routine_setup.

Mosaico's routine catalogue (server, outreach-routine-catalogue.ts) owns each routine's task name, text, default schedule, steps and
report headings. The installer saves what the read returns and tells Mosaico what it saved. Nothing of that may be hard-coded in the
skill: no cron, no clock time, no task title, no routine text. The machine checks stay; so does the Routines Board it publishes.
"""

from __future__ import annotations

import re

from skill_text import CATALOGUE_VERSION, SCHEDULE, VERSION, check, flat, skill

ALLOW_RULES = ("mcp__Claude_Browser__javascript_tool", "mcp__Claude_Browser__computer", "mcp__Claude_Browser__browser_batch")
CRON = re.compile(r"(?<![\w-])(?:[\d*/,]+\s+){4}[\d*/,]+(?![\w-])")
CLOCK_TIME = re.compile(r"\b\d{1,2}:\d{2}\b|\b\d{1,2}\s?(?:AM|PM)\b|\bHH:MM\b", re.I)
TITLE = re.compile(r"Mosaico Outreach\s+[—-]")
ROUTINE_TEXT = re.compile(r"Standing answers for this recurring automation|Follow that skill's|This is the (?:Send invitations|Follow-up|Source leads|Withdraw|Routines report) routine", re.I)


def main() -> None:
    claude = skill("Claude", SCHEDULE)
    text = flat(claude)

    # Nothing about a routine is hard-coded.
    check(not CRON.search(text), f"the Claude installer hard-codes a cron: {CRON.search(text) and CRON.search(text).group(0)}")
    check(not CLOCK_TIME.search(text.replace("`HH:MM`", "")), f"the Claude installer hard-codes a time: {CLOCK_TIME.search(text) and CLOCK_TIME.search(text).group(0)}")
    check(not TITLE.search(text), "the Claude installer hard-codes a task title")
    check(not ROUTINE_TEXT.search(text), "the Claude installer carries a routine text")
    for stale in ("Sync data", "evening review", "quota"):
        check(stale not in text.replace("Sync data routine", ""), f"the Claude installer still carries: {stale}")

    # It reads the setup, saves it as returned, records each routine with the catalogue version and offers to remove a retired one.
    for needle in (
        "outreach_get_routine_setup", "timeZone", "boardUrl", "routinesToInstall", "routinesToUpdate", "retiredRoutines", "remove_retired_routines",
        "routineText.text", "exactly as returned", "defaultSchedule.cron", "defaultSchedule.paused", "taskName", "routineText.complete",
        "outreach_record_routine_schedule", "catalogueVersion", "pluginVersion", "minimumPluginVersion", "register_linkedin_identity",
        "must be updated together", CATALOGUE_VERSION, VERSION, "list_scheduled_tasks", "create_scheduled_task", "update_scheduled_task", "delete_scheduled_task",
        "only after the person agrees", "standingAnswers.reviewWindow.state", "ask_review_window", "When do you usually review and approve drafts?",
        "reviewWindow", "reviewWindowUsed", "readback", "defaultSchedule.crons", "never move, add or drop one yourself", "Never ask", "Never add, shorten or copy a step into a text", "Read each saved task back", "Never pass ownerUserId",
    ):
        check(needle in text, f"the Claude installer lacks: {needle}")
    check(text.index("outreach_get_routine_setup") < text.index("outreach_record_routine_schedule"), "the installer records before it reads the setup")

    # It asks about the review window once, only when Mosaico says it is missing, before it saves any task; no times or rules are its own.
    check(text.count("When do you usually review and approve drafts?") == 1, "the installer must ask about the review window exactly once")
    check(text.index("ask_review_window") < text.index("create_scheduled_task") or text.index("ask_review_window") < text.index("routinesToInstall and"),
          "the installer asks for the review window after it saves tasks")
    check("is missing" in text and "when the state is given or registered" in text, "the installer does not ask only when the window is missing")
    for hard_coded in ("15 minutes", "30 minutes", "90 minutes", "7:00", "10:30"):
        check(hard_coded not in text, f"the Claude installer states a time rule of its own: {hard_coded}")
    codex_ask = flat(skill("Codex", SCHEDULE))
    check("When do you usually review" not in codex_ask, "the Codex installer asks for a window although it installs no routine")

    # The machine checks and the Routines Board stay.
    for needle in (*ALLOW_RULES, "mosaico-outreach-*", "~/.codex/skills/", "~/.claude/skills/", "daily-approved-outreach-sends", "mosaico-lead-preparation",
                   ".mcp.json", "~/.claude.json", "amplifyapp.com", "https://app.mosaico.one", "assets/routines-board.html", "Outreach Routines Board",
                   '"db"', '"user"', '"write": "admin"', "each person's tasks are saved on her own machine"):
        check(needle in text, f"the Claude installer lacks: {needle}")

    # Codex installs no routine: the texts name Claude's pane and need the captures.
    codex = flat(skill("Codex", SCHEDULE))
    check(not CRON.search(codex) and not TITLE.search(codex) and not ROUTINE_TEXT.search(codex), "the Codex installer hard-codes a routine")
    for needle in ("installs no routine from Codex", "outreach_get_routine_setup", "remove_retired_routines", CATALOGUE_VERSION, VERSION, "mosaico-outreach-*"):
        check(needle in codex, f"the Codex installer lacks: {needle}")
    check("outreach_record_routine_schedule" not in codex, "the Codex installer records a schedule it did not install")

    print("PASS: both installers hard-code no cron, time, task title or routine text; Claude saves what outreach_get_routine_setup returns, records each routine "
          f"with the catalogueVersion ({CATALOGUE_VERSION}), offers to remove a retired one, keeps its machine checks and the Routines Board; Codex installs none.")


if __name__ == "__main__":
    main()
