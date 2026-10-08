#!/usr/bin/env python3
"""0.9.10: runs read every planned Agent, never end early, and end through outreach_end_run.

The application owns when a run is over (ADR-0005); these checks pin that the skills tell the model to ask it,
not to decide: the runId read of every planned Agent, the five stop sentences, outreach_end_run on every
routine, the environment line and the previous-run-abandoned note.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "plugins" / "mosaico-claude"
CODEX = ROOT / "plugins" / "mosaico-codex"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flat(text: str) -> str:
    return " ".join(text.replace("`", "").split())


# The five stop sentences. The wording is the owner's: there is no search budget.
STOP_SENTENCES = (
    "Stop only when Mosaico says the run is complete (workflowStatus.completion is complete with reason sourcing-quota-met or sourcing-days-full) and nothing is left to verify or draft, when Mosaico recommends end_run_days_full, or when Mosaico reports stop_run after the tenth failure (then write the sourcing report Mosaico asks for).",
    'There is no search limit: do as many searches as it takes, and "I could not find candidates", "few results", "weak results", "slow" and "enough found" are never a reason to stop.',
    "When results are few, widen inside the Agent's brief (more keywords, more results pages, other filters, other regions the brief allows, Premium Daily Prospects) and keep searching; never widen past the brief's qualification rules.",
    "If an Agent's brief says to report a lead supply constraint, note it for the final report and keep searching inside the brief; it never means stop.",
    'A run that ends with any line still open and no stop_run is a failed run: report it as "run failed: stopped with N open".',
)


def main() -> None:
    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        raw = read(root / "skills" / "mosaico-outreach-invite-run" / "SKILL.md")
        text = flat(raw)
        routine = flat(raw[raw.index("## Source leads routine"):])
        sourcing = flat(raw[raw.index("## Source Leads and prepare drafts"):raw.index("## Source Leads only")])

        # 1. Every planned Agent is read by run id, never with an owner.
        check("Call outreach_get_agents with the runId. Never pass ownerUserId with it." in sourcing, f"{package} Source Leads section does not read outreach_get_agents with the runId and no ownerUserId")
        check("Before you source, call outreach_get_agents with the runId. Never pass ownerUserId with it." in routine, f"{package} Source leads routine does not read outreach_get_agents with the runId and no ownerUserId")
        for where, body in (("section", sourcing), ("routine", routine)):
            check("every Agent in this run's plan" in body and "colleagues' Agents" in body and "own search and message instructions" in body, f"{package} {where} does not say to work from every returned Agent's own instructions, colleagues' included")
        check("Read outreach_get_agents, then" not in routine and "Read `outreach_get_agents`, then call" not in raw, f"{package} invite-run skill still reads Agents without the runId")
        for number, line in enumerate(raw.splitlines(), 1):
            if "ownerUserId" in line:
                # Only a prohibition, or (0.9.11) the read of a colleague's day and the draft call that carries no ownerUserId.
                check(bool(re.search(r"(Never|Do not) pass|no `ownerUserId`|as `ownerUserId`|as ownerUserId", line)), f"{package} invite-run line {number} tells the model about ownerUserId")

        # 2. The five stop sentences, in the section (backticks aside) and word for word in the routine step 4.
        step4 = routine[routine.index("Step 4."):routine.index("Step 5.")]
        for number, sentence in enumerate(STOP_SENTENCES, 1):
            check(sentence in step4, f"{package} Source leads Step 4 lacks stop sentence {number}: {sentence[:60]}")
            check(sentence in sourcing, f"{package} Source Leads section lacks stop sentence {number}: {sentence[:60]}")
        check("Never stop while any line of workflowStatus.sourcingPlan is open, and never because you think enough was found" in step4, f"{package} Step 4 lost the open-line rule")
        for banned in ("search budget", "search limit of", "after three searches", "after a few searches"):
            check(banned not in text, f"{package} invite-run skill speaks of a search budget: {banned}")

        # 3. Runs end through outreach_end_run, with an honest reason; the application decides.
        check("## End the run" in raw and "`outreach_end_run`" in raw, f"{package} invite-run skill lacks the End the run section")
        end_section = flat(raw[raw.index("## End the run"):raw.index("## Source leads routine")])
        for needle in ("End every run with outreach_end_run and the honest reason", "Mosaico decides how the run ended, not you", "complete: Mosaico says the run is complete", "blocked: a genuine blocker stops the run", "blockerCode", "linkedInIssue (warning, captcha or restricted)", "records a wrong one as abandoned", "outreach_record_sourcing_report only when Mosaico reports stop_run after the tenth failure", "sourcing-not-complete", "runOutcome"):
            check(needle in end_section, f"{package} End the run section lacks: {needle}")
        check("Then end the run with outreach_end_run and the honest reason, and let Mosaico decide the outcome" in step4 and "reason complete" in step4 and "reason blocked" in step4, f"{package} Step 4 does not end the run through outreach_end_run")
        check("Never write a sourcing report while a line is open unless Mosaico says the failure stop fired" in step4 and "sourcing-not-complete" in step4, f"{package} Step 4 allows a sourcing report while a line is open")
        check("End the run (see **End the run**), then finish with **Report a sourcing run**" in sourcing, f"{package} Source Leads section does not end the run before the report")

        # 4. The environment and a previous abandoned run.
        step1 = routine[routine.index("Step 1."):routine.index("Step 2.")]
        check("Read environmentName in the start answer. If it is not production, stop and report it" in step1 and '"Mosaico environment: production"' in step1, f"{package} Step 1 does not state the environment or stop on a non-production one")
        check("previous-run-abandoned" in step1 and "Previous run failed: stopped with N open" in step1 and "previousRun.openLines" in step1, f"{package} Step 1 does not handle previous-run-abandoned")
        check("Every start answer names the Mosaico environment in environmentName. If it is not production, stop and report it" in sourcing_start(raw), f"{package} Start the run does not state the environment")
        check("previous-run-abandoned" in sourcing_start(raw) and "Previous run failed: stopped with N open" in sourcing_start(raw), f"{package} Start the run does not handle previous-run-abandoned")
        report = flat(raw[raw.index("## Report a sourcing run"):raw.index("## Send approved invitations")])
        check('The first line is "Mosaico environment: <environmentName>"' in report and "previous-run-abandoned" in report and "runOutcome" in report, f"{package} sourcing report does not start with the environment or report runOutcome")
        step5 = routine[routine.index("Step 5."):]
        check('Start the report with the line "Mosaico environment: <environmentName>"' in step5 and "previous-run-abandoned" in step5 and "runOutcome" in step5 and 'report it as "run failed: stopped with N open"' in step5, f"{package} Step 5 does not report the environment, the previous run or the outcome")

        overview = flat(read(root / "skills" / "mosaico-outreach" / "SKILL.md"))
        check("environmentName" in overview and "a run on anything but production stops" in overview, f"{package} overview skill lacks the environment rule")
        check("with the runId, which returns every Agent in the run's plan" in overview, f"{package} overview skill does not read the planned Agents by run id")
        installer = flat(read(root / "skills" / "mosaico-outreach-schedule-install" / "SKILL.md"))
        check("environmentName" in installer and "a run on anything but production stops" in installer, f"{package} schedule-install skill lacks the environment rule")
        check("0.9.9 or later" in installer and "0.9.10 or later" not in installer, f"{package} schedule-install changed a thin text's version although no new routine section is required")

    # The follow-up (Sync data) and repair routines end their runs through outreach_end_run and report the environment.
    for name, marker, stop_text in (
        ("mosaico-outreach-follow-up-run", "## Sync data routine", "continue until Mosaico reports completion (no-approved-invitations-remain)"),
        ("mosaico-outreach-repair-run", "## Repair routine", "never earlier for volume and never later by starting another run."),
    ):
        raw = read(CLAUDE / "skills" / name / "SKILL.md")
        routine = flat(raw[raw.index(marker):])
        check("End each run with outreach_end_run" in routine or "End the run with outreach_end_run" in routine, f"{name} routine does not end runs through outreach_end_run")
        check("reason complete" in routine.lower() and "reason blocked" in routine.lower() and "blockerCode" in routine and "linkedInIssue" in routine, f"{name} routine lacks the complete and blocked reasons")
        check(flat(stop_text) in routine, f"{name} routine lost its stop rule")
        check("Read environmentName in the start answer: if it is not production, stop and report it" in routine and '"Mosaico environment: production"' in routine, f"{name} routine does not state the environment")
        check("the Mosaico environment (the first line)" in routine, f"{name} report does not carry the environment")
    # Codex has no Sync data or Repair routine, so it neither ends nor reports those runs.
    for name in ("mosaico-outreach-follow-up-run", "mosaico-outreach-repair-run"):
        check("outreach_end_run" not in read(CODEX / "skills" / name / "SKILL.md"), f"Codex {name} names outreach_end_run although it runs no such routine")

    # Versions and README.
    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json"):
        check(json.loads(read(manifest))["version"] == "0.9.11", f"{manifest.name} is not at 0.9.11")
    readme = read(ROOT / "README.md")
    check(readme.index("### 0.9.10") < readme.index("### 0.9.9"), "README changelog lacks 0.9.10 above 0.9.9")
    entry = flat(readme[readme.index("### 0.9.10"):readme.index("### 0.9.9")])
    for needle in ("outreach_get_agents with the runId (never with ownerUserId)", "no search limit", "outreach_end_run", "reason complete or blocked", "sourcing-not-complete", "environmentName", "Mosaico environment: production", "previous-run-abandoned", "run failed: stopped with N open", "still say \"0.9.9 or later\"", "pull request 1820"):
        check(needle in entry, f"README 0.9.10 entry lacks: {needle}")
    check("**How a run ends.**" in readme, "README lacks the How a run ends paragraph")
    print("PASS: the skills read every planned Agent by run id, state the five stop sentences, end every routine through outreach_end_run, report the environment and a previous abandoned run, and the version is 0.9.11.")


def sourcing_start(raw: str) -> str:
    return flat(raw[raw.index("## Start the run"):raw.index("## Source Leads and prepare drafts")])


if __name__ == "__main__":
    main()
