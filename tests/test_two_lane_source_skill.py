#!/usr/bin/env python3
"""0.9.12: Source leads runs in two lanes (own and colleagues) against the sourcing-lanes server contract.

The application owns the lane, the single-flight rule, the end rule and the work to do now (ADR-0005). These checks pin that the
skills only pass the lane word they were given, work `workNow`, never ask for `abandoned`, never promise a stop after a number of
failures or a search budget, and that the installer saves two thin texts that differ only in the scope line, on crons that never
overlap each other, Sync data (13:00) or Repair (Sunday 10:00).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "plugins" / "mosaico-claude"
CODEX = ROOT / "plugins" / "mosaico-codex"

OWN_CRON = "0 0,2,4,6,8,12,14,16,18,20,22 * * *"
COLLEAGUES_CRON = "0 1,3,5,7,9,11,15,17,19,21,23 * * *"
SYNC_HOUR = 13
REPAIR_HOUR = 10  # Sunday


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flat(text: str) -> str:
    return " ".join(text.replace("`", "").split())


def hours_of(cron: str) -> list[int]:
    fields = cron.split()
    check(len(fields) == 5 and fields[0] == "0" and fields[2:] == ["*", "*", "*"], f"cron is not a plain hour list: {cron}")
    check(re.fullmatch(r"\d{1,2}(,\d{1,2})*", fields[1]) is not None, f"cron hours are not an explicit list: {cron}")
    return [int(hour) for hour in fields[1].split(",")]


def gap_minutes(a: int, b: int) -> int:
    """Minutes between two on-the-hour times on a 24-hour clock that wraps at midnight."""
    difference = abs(a - b) % 24
    return min(difference, 24 - difference) * 60


def main() -> None:
    installer_raw = read(CLAUDE / "skills" / "mosaico-outreach-schedule-install" / "SKILL.md")
    installer = " ".join(installer_raw.split())  # backticks kept
    codex_installer = flat(read(CODEX / "skills" / "mosaico-outreach-schedule-install" / "SKILL.md"))

    # 1. Two Source leads tasks: identical texts but for the scope line; both stamped 0.9.13 (0.9.13: Source leads writes no drafts).
    texts = re.findall(r"```text\n(.*?)\n```", installer_raw, re.S)
    check(len(texts) == 4, f"installer must hold four schedule texts, found {len(texts)}")
    _, own_text, colleagues_text, _ = texts
    for scope, text in (("own", own_text), ("colleagues", colleagues_text)):
        check(f"sourcing scope: {scope};" in text, f"the {scope} lane text lacks the line 'sourcing scope: {scope}'")
        check("(0.9.13 or later)" in text and "is older than 0.9.13 or has no \"Source leads routine\" section" in text, f"the {scope} lane text is not stamped 0.9.13")
        check("Follow that skill's \"Source leads routine\" section exactly" in text, f"the {scope} lane text does not name its routine section")
        check("Proceed without asking which days or which scope" in text, f"the {scope} lane text may ask which scope")
        check(len(text.split()) <= 200, f"the {scope} lane text is not thin")
        for procedure in ("Step 1", "outreach_", "// mosaico run", "quota", "day:"):
            check(procedure not in text, f"the {scope} lane text holds procedure or a number: {procedure}")
    check(own_text.replace("sourcing scope: own;", "sourcing scope: colleagues;") == colleagues_text, "the two lane texts differ in more than the scope line")
    check("sourcing scope" not in " ".join(texts[0].split()) and "sourcing scope" not in texts[3], "Sync data or Repair text carries a scope line")
    check("(0.9.13 or later)" in texts[0] and "(0.9.6 or later)" in texts[3], "the Sync data stamp is not 0.9.13 or the Repair stamp changed")
    check("Mosaico Outreach — Source leads (own)" in installer and "Mosaico Outreach — Source leads (colleagues)" in installer, "installer lacks the two lane task titles")
    check("sourcing scope" not in codex_installer, "the Codex installer text carries a scope line although it installs one whole-plan task")

    # 2. The crons are explicit hour lists that never overlap each other, Sync data (13:00) or Sunday Repair (10:00).
    check(f"`{OWN_CRON}`" in installer_raw and f"`{COLLEAGUES_CRON}`" in installer_raw, "installer lacks the two exact lane crons")
    own, colleagues = hours_of(OWN_CRON), hours_of(COLLEAGUES_CRON)
    check(own == [0, 2, 4, 6, 8, 12, 14, 16, 18, 20, 22] and colleagues == [1, 3, 5, 7, 9, 11, 15, 17, 19, 21, 23], "the lane hour lists changed")
    check(not set(own) & set(colleagues), "the two lanes share an hour")
    check(len(own) + len(colleagues) == 22, "the lanes do not make 22 runs a day")
    for hour in own + colleagues:
        check(hour != SYNC_HOUR, f"a Source leads time falls on the Sync data hour {SYNC_HOUR}:00")
        check(gap_minutes(hour, SYNC_HOUR) >= 60, f"{hour}:00 is closer than 60 minutes to Sync data")
        check(gap_minutes(hour, REPAIR_HOUR) >= 60 and hour != REPAIR_HOUR, f"{hour}:00 is closer than 60 minutes to Sunday Repair")
    for a in own:
        for b in colleagues:
            check(gap_minutes(a, b) >= 60, f"{a}:00 and {b}:00 are closer than 60 minutes across the lanes")
    for needle in ("at least 60 minutes from every time of the other lane, from the Sync data time, and on the day Repair runs from the Repair time", "`0 13 * * *`", "`0 10 * * 0`"):
        check(needle in installer, f"installer's spacing rule lacks: {needle}")

    # 3. The installer matches by routine and scope, replaces a scope-less task in place, keeps 'no Source leads task', reads both lanes back.
    for needle in (
        "Match a Source leads task by routine and scope",
        "A Source leads task with no scope line is the older whole-plan task: update it in place into the own lane",
        "never leave it enabled beside the lanes",
        "No Source leads task at all is a valid answer",
        "a person who also sources for a colleague gets both lanes",
        "Read both Source leads lanes back and show, for each, its name, cron, enabled state, next run",
        "holds no steps",
        "no Source leads task without a scope line remains enabled",
        "`list_scheduled_tasks`", "`create_scheduled_task`", "`update_scheduled_task`",
        "install no Source leads task for her",
    ):
        check(needle in installer, f"installer lacks: {needle}")

    # 4. Skill texts, both packages: the lane word, workNow, the busy/empty/invalid answers, the end rule, no budget, no failure stop.
    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        raw = read(root / "skills" / "mosaico-outreach-invite-run" / "SKILL.md")
        text = flat(raw)
        routine = flat(raw[raw.index("## Source leads routine"):])
        step1 = routine[routine.index("Step 1."):routine.index("Step 2.")]
        step2 = routine[routine.index("Step 2."):routine.index("Step 3.")]
        step4 = routine[routine.index("Step 4."):routine.index("Step 5.")]
        step5 = routine[routine.index("Step 5."):]
        end_section = flat(raw[raw.index("## End the run"):raw.index("## Source leads routine")])

        # The lane word is passed as given and never chosen.
        for where, body in (("Start the run", flat(raw[raw.index("## Start the run"):raw.index("## Source Leads\n")])), ("Step 1", step1)):
            check("sourcing scope: own" in body and "sourcing scope: colleagues" in body, f"{package} {where} does not name the two scope lines")
            check("exactly that word as sourcingScope on outreach_start_run" in body, f"{package} {where} does not pass the scope word as given")
            check("send nothing" in body and "never choose, change or invent a scope" in body.lower(), f"{package} {where} may choose or invent a scope")
        check("never start a second" in text.lower() and "once per session" in text, f"{package} skill may start a second sourcing run in a session")
        check("Check the echo" in text and "top-level sourcingScope" in text, f"{package} skill does not check the sourcingScope echo")

        # Busy and empty are not failures; invalid and plan-empty are loud.
        for needle in ("sourcing-run-busy", "wait_for_current_run", "Another Source leads run is working on this account; nothing started.", "sourcing-scope-empty", "nothing_to_source", "Nothing to source for the <own|colleagues> Agents.", "sourcing_scope_invalid", "correct_sourcing_scope"):
            check(needle in text, f"{package} skill lacks: {needle}")
            check(needle in step1, f"{package} Step 1 lacks: {needle}")
        check("This is not a failure" in text and "This is loud" in text, f"{package} skill does not separate quiet blockers from loud ones")
        check("previous-run-finished-not-ended" in text, f"{package} skill does not handle previous-run-finished-not-ended")
        check("run failed: stopped with N open" in text and "Previous run failed: stopped with N open" in text, f"{package} skill lost the previous-run report line")

        # workNow: work it, re-read it, save with its Agent, no owner on a write.
        for needle in ("workNow", "workNow.agentId", "workNow.brief", "read it again at every decision point", "no ownerUserId", "briefMissing", "run-ended", "planned-agent-unavailable", "sourcing-agent-unavailable", "unavailableAgents", "profile-exists-under-other-owner", "heldByOtherOwner"):
            check(needle in text, f"{package} skill lacks: {needle}")
        for needle in ("workNow.agentId", "no ownerUserId", "workNow.brief", "read it again at every decision point"):
            check(needle in step2, f"{package} Step 2 lacks: {needle}")
        check("Pass workNow.agentId as agentId on every outreach_save_lead and pass no ownerUserId" in text, f"{package} Which Agent section does not save with workNow.agentId and no owner")
        # Liveness read.
        check("outreach_get_run at least every 10 minutes" in step2, f"{package} Step 2 lacks the liveness read")
        sourcing_section = flat(raw[raw.index("## Source Leads\n"):raw.index("## Which Agent a Lead goes to")])
        check("outreach_get_run at least every 10 minutes" in sourcing_section, f"{package} Source Leads section lacks the liveness read")

        # The end rule: two reasons, a refusal is not argued with, a finished run is always ended, an idle close stops the run.
        for needle in ("Never ask for abandoned", "sourcing-run-open", "Do not retry the end and do not argue", "Always call it on a finished run", "run_ended", "report_run_closed", "do not start another run", "Mosaico closed this run after 30 minutes without a call"):
            check(needle in end_section, f"{package} End the run section lacks: {needle}")
        for needle in ("always call it on a finished run", "never ask for abandoned", "sourcing-run-open", "do not retry the end and do not argue", "run_ended", "report_run_closed", "do not start another run"):
            check(needle in step4, f"{package} Step 4 lacks: {needle}")
        check("reason complete" in step4 and "reason blocked" in step4 and "INTERNAL_SERVER_ERROR" in step4 and "linkedin_account_changed" in step4, f"{package} Step 4 does not state the two reasons and the proofs")

        # Report lines.
        for body in (flat(raw[raw.index("## Report a sourcing run"):raw.index("## Send approved invitations")]), step5):
            check("Mosaico lane: own" in body and "Mosaico lane: colleagues" in body and "Mosaico lane: whole plan" in body, f"{package} report lacks the Mosaico lane line")
            check("Candidates skipped as held by another owner: N" in body, f"{package} report lacks the held-by-another-owner line")
            check("unavailableAgents" in body, f"{package} report lacks the unavailable Agents")

        # Words that must be gone: the abandoned request, a failure stop, a search budget.
        leftover = text
        for allowed in ("previous-run-abandoned", "Never ask for abandoned", "never ask for abandoned"):
            leftover = leftover.replace(allowed, "")
        check("abandon" not in leftover.lower(), f"{package} invite-run skill still speaks of abandoned outside the note and the prohibition")
        for banned in ("tenth failure", "ten failures", "ten distinct", "stop_run", "sourcing-exhausted", "failure stop", "outreach_record_sourcing_report", "sourcing-not-complete", "search budget", "search limit of", "after three searches", "after a few searches", "records a wrong one"):
            check(banned not in text, f"{package} invite-run skill still holds: {banned}")
        check("There is no search limit" in text, f"{package} skill lost the no-search-limit rule")

    # No skill anywhere asks for the removed reason or promises a failure stop.
    for path in sorted((ROOT / "plugins").glob("*/skills/*/SKILL.md")):
        body = flat(read(path))
        leftover = body.replace("previous-run-abandoned", "").replace("Never ask for abandoned", "").replace("never ask for abandoned", "")
        check("abandon" not in leftover.lower(), f"{path.relative_to(ROOT)} speaks of abandoned")
        for banned in ("tenth failure", "ten failures", "stop_run", "sourcing-exhausted", "search budget"):
            check(banned not in body, f"{path.relative_to(ROOT)} holds: {banned}")

    # 5. Sync data and Repair are untouched by the lanes.
    for name, marker in (("mosaico-outreach-follow-up-run", "## Sync data routine"), ("mosaico-outreach-repair-run", "## Repair routine")):
        routine = flat(read(CLAUDE / "skills" / name / "SKILL.md"))
        check("sourcingScope" not in routine and "sourcing scope" not in routine, f"{name} mentions the Source leads scope")

    # 6. Versions and the changelog entry that names the server release.
    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json"):
        check(json.loads(read(manifest))["version"] == "0.9.13", f"{manifest.name} is not at 0.9.13")
    readme = read(ROOT / "README.md")
    check(readme.index("### 0.9.12") < readme.index("### 0.9.11"), "README changelog lacks 0.9.12 above 0.9.11")
    entry = flat(readme[readme.index("### 0.9.12"):readme.index("### 0.9.11")])
    for needle in (
        "equires Mosaico server release 20261008e (PR #1831) or later; install only after that release is live on main-v2",
        "sourcingScope", "workNow", "workNow.agentId", "outreach_get_run at least every 10 minutes", "sourcing-run-busy", "sourcing-scope-empty", "sourcing_scope_invalid",
        "abandoned is gone", "sourcing-run-open", "run_ended", "unavailableAgents", OWN_CRON, COLLEAGUES_CRON, "scope-less Source leads task is updated in place into the own lane",
        "Mosaico lane", "Candidates skipped as held by another owner: N",
    ):
        check(needle in entry, f"README 0.9.12 entry lacks: {needle}")

    # 7. When the application checkout is at hand, the server still carries what this release relies on.
    app = os.environ.get("MOSAICO_APP_REPO")
    if app:
        registry = Path(app) / "features" / "outreach" / "server" / "outreach-mcp-registry.ts"
        end = Path(app) / "features" / "outreach" / "server" / "outreach-run-end.ts"
        if registry.is_file() and end.is_file():
            source = read(registry)
            for needle in ("sourcingScope: z.enum(OUTREACH_SOURCING_SCOPES).optional()", "sourcing-run-busy", "sourcing-scope-empty", "sourcing_scope_invalid", "workNow", "planned-agent-unavailable", "sourcing-run-open", "unavailableAgents"):
                check(needle in source, f"the application registry lacks: {needle}")
            check("OUTREACH_END_REASONS = ['complete', 'blocked']" in read(end), "the application's end reasons are not complete and blocked")

    print("PASS: Source leads runs in two lanes: the skills pass only the lane word they were given, work workNow, never ask for abandoned or promise a failure stop, and the installer saves two thin texts on non-overlapping crons.")


if __name__ == "__main__":
    main()
