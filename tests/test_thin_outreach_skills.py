#!/usr/bin/env python3
"""0.10.0, the thin plugin: the Outreach skills follow the step Mosaico returns and hold no Outreach know-how of their own.

The order of the work, when a run stops, how to search, how to write, the routine texts and the report wording live on the Mosaico
server (stage-v2 PRs #2168 to #2182, ADR-0012 and ADR-0023). These checks pin the thin contract in both packages: start the run, read
the step, do exactly what step.call, step.agentInstructions and step.guidance say, record, end the run and give the server's report
unchanged; stop on a blocker; say that plugin and server must be updated together when the step is missing; keep the routine section
names the server's routine texts point at; and carry none of the know-how that moved (the old tokens below).
"""

from __future__ import annotations

import re

from skill_text import (
    AGENTS, CATALOGUE_VERSION, CLAUDE, CODEX, FOLLOW_UP, HUB, INVITE, LEADS, OUTREACH_SKILLS, PACKAGES, ROOT, SCHEDULE, VERSION,
    check, flat, manifests, read, section, skill, skill_path,
)

RUN_SKILLS = (HUB, INVITE, FOLLOW_UP)
CONTRACT = (
    "outreach_start_run", "step.call", "supplyAlso", "step.agentInstructions", "step.guidance", "outreach_end_run", "report.lines",
    "report.sections", "recommendedAction", "must be updated together",
)
# Know-how that now lives on the server. None of it may come back into a skill.
MOVED = (
    "draftsToWrite", "sendRun.", "workNow", "checklistReview", "verifyAction", "sourcing_plan_empty", "sourcing-run-open", "send-run-open",
    "Judge the Lead's latest message", "declined, interested or neutral", "outreach_get_follow_ups", "outreach_get_repair_queue",
    "sendNotBefore", "history-mismatch", "completion.mustContinue", "Standing answers for this recurring automation", "No pressure",
)
# What the run skills and the hub leave to the step (the write tools and Agent fields are named by step.call, not by the skill).
MOVED_IN_RUN_SKILLS = (
    "Leads per day", "Leads per run", "messagingChecklist", "Messaging Checklist", "outreach_get_agents", "outreach_deposit_conversation",
    "outreach_mark_message_sent", "outreach_record_connection_evidence", "outreach_record_connections_snapshot", "outreach_save_lead",
    "outreach_record_message", "outreach_link_duplicate_leads",
)
INTENTS = {INVITE: ("send_approved_invitations", "source_invitation_leads", "manage_leads"), FOLLOW_UP: ("follow_up_pass",)}
READS = {INVITE: ("outreach_get_day", "outreach_get_withdraw_queue"), FOLLOW_UP: ("outreach_get_follow_up_queue",)}
# The routine sections the server's routine texts name: "Follow that skill's <section> section exactly" (outreach-routine-catalogue.ts).
SECTIONS = {
    "Claude": {INVITE: ("Source leads routine", "Send invitations routine", "Withdraw stale invitations routine"),
               FOLLOW_UP: ("Follow-up routine", "Routines report routine")},
    "Codex": {INVITE: ("Source leads routine",), FOLLOW_UP: ("Follow-up routine",)},
}


def main() -> None:
    # Version: both manifests are at 0.10.0 and the skills name it.
    for package, manifest in manifests().items():
        check(manifest["version"] == VERSION, f"the {package} manifest is not at {VERSION}")
        check("mcpServers" not in str(manifest), f"the {package} manifest bundles a Mosaico server")
    check(not list(ROOT.rglob(".mcp.json")), "the plugin ships a .mcp.json: it must bundle no Mosaico server")
    check(VERSION in flat(skill("Claude", SCHEDULE)) and CATALOGUE_VERSION in flat(skill("Claude", SCHEDULE)), "the Claude installer does not name its plugin and catalogue versions")

    for package, root in PACKAGES.items():
        # Repair is retired: no skill directory, no mention.
        check(not (root / "skills" / "mosaico-outreach-repair-run").exists(), f"the {package} package still has the Repair skill")
        names = {path.parent.name for path in (root / "skills").glob("*/SKILL.md")}
        check(set(OUTREACH_SKILLS) <= names, f"the {package} package lacks an Outreach skill: {sorted(set(OUTREACH_SKILLS) - names)}")
        check(not [n for n in names if n.startswith("mosaico-outreach") and n not in OUTREACH_SKILLS], f"the {package} package has an unexpected Outreach skill")

        for name in OUTREACH_SKILLS:
            raw = skill(package, name)
            text = flat(raw)
            check(raw.startswith(f"---\nname: {name}\ndescription: "), f"{package} {name} has no front matter naming itself")
            for token in MOVED + (MOVED_IN_RUN_SKILLS if name in RUN_SKILLS + (SCHEDULE,) else ()):
                check(token not in text, f"{package} {name} still carries Mosaico's know-how: {token}")
            check(not re.search(r"\bRepair\b|repair[- ](?:run|queue|routine)", text), f"{package} {name} still mentions Repair")
            # Every skill that makes Outreach calls says what to do on the acting refusal.
            for needle in ("acting as a member of another organisation", "word for word", "Never end the acting session yourself"):
                check(needle in text, f"{package} {name} lacks the acting rule: {needle}")

        # The run skills: the whole contract, the intent, the read, no questions.
        for name in RUN_SKILLS:
            text = flat(skill(package, name))
            for needle in CONTRACT:
                check(needle in text, f"{package} {name} lacks: {needle}")
            check("never pass owneruserid" in text.lower(), f"{package} {name} does not forbid ownerUserId")
            check("unchanged" in text and "adding only what a heading asks for" in text, f"{package} {name} does not give the report unchanged")
            if name in INTENTS:
                for intent in INTENTS[name]:
                    check(intent in text, f"{package} {name} lacks the intent {intent}")
                for read_tool in READS[name]:
                    check(read_tool in text, f"{package} {name} lacks the read {read_tool}")
                check("Do not ask the person" in text, f"{package} {name} may ask the person for days or scopes")
            check("Mosaico decides" in text, f"{package} {name} does not leave the decisions to Mosaico")
        for name, headings in SECTIONS[package].items():
            for heading in headings:
                section(skill(package, name), heading)

        # Claude runs captures through the gate; Codex has no scripts and says so, starting runs with browserEvidence false.
        for name in RUN_SKILLS:
            text = flat(skill(package, name))
            if package == "Claude":
                for needle in ("identityEvidence", "// mosaico run <script>.js <PLACEHOLDER>=<value>", "step.evidence.directive", "integrity"):
                    check(needle in text, f"Claude {name} lacks: {needle}")
            else:
                check("browserEvidence: false" in text, f"Codex {name} does not declare browserEvidence false")
                check("cannot run the approved LinkedIn captures" in text, f"Codex {name} does not say Codex cannot capture")
                check("observedLinkedInProfile" in text, f"Codex {name} does not start with the Me page profile")
                check("// mosaico run" not in text and "whoami" not in text, f"Codex {name} names a script it cannot run")

    # The Claude hub: menu once, routes to the skills, inspect needs no change, the one limit.
    hub = flat(skill("Claude", HUB))
    for needle in ("What do you want to do in Mosaico Outreach?", "never show the menu again", "intent: inspect_day", "It changes nothing",
                   "It needs no Outreach run", "Only Owners and Admins can use Outreach", "20 invitation sends per owner per day"):
        check(needle in hub, f"the Claude hub lacks: {needle}")
    for target in (INVITE, FOLLOW_UP, AGENTS, LEADS, SCHEDULE):
        check(f"/mosaico:{target}" in hub, f"the Claude hub does not route to {target}")
        check(f"$mosaico:{target}" in flat(skill("Codex", HUB)), f"the Codex hub does not route to {target}")

    # The invite-run skill keeps the machine-only rules and the routine details Mosaico cannot know.
    invite = flat(skill("Claude", INVITE))
    for needle in ("onBehalfOfMemberId", "sourcingScope", "https://www.linkedin.com/feed/", "Board key", "ArtifactData", "assets/routines-board.html",
                   "acknowledgeProfileOnOtherOwner", "email-required", "never cannot-message"):
        check(needle in invite, f"the Claude invite-run skill lacks: {needle}")
    follow = flat(skill("Claude", FOLLOW_UP))
    for needle in ("Never reorder or skip items", "writes follow-up drafts only", "never invitation drafts",
                   "outreach_get_routine_setup", "list_task_runs", "Sync data routine", "mosaico-outreach-schedule-install"):
        check(needle in follow, f"the Claude follow-up-run skill lacks: {needle}")
    check("Run nothing from it" in follow, "the Claude follow-up-run skill may run a saved Sync data schedule")

    # Agents and Leads: the tools they use, the confirmation before every change, nothing about another owner's records being off limits.
    agents = flat(skill("Claude", AGENTS))
    for needle in ("outreach_get_agents", "outreach_update_agent", "outreach_create_agent", "get_team_profiles", "immediately before", "ownerUserId"):
        check(needle in agents, f"the Claude agent-management skill lacks: {needle}")
    check("works only on the signed-in person's own" not in agents and "Do not pass ownerUserId" not in agents, "the agent-management skill still refuses another member's Agents")
    leads = flat(skill("Claude", LEADS))
    for needle in ("outreach_update_lead", "outreach_save_lead", "outreach_load_leads", "outreach_request_redraft", "outreach_transfer_lead", "outreach_transfer_leads",
                   "nextTouchOn", "Never infer a bulk target from a partial name", "immediately before", "acknowledgeProfileOnOtherOwner"):
        check(needle in leads, f"the Claude lead-management skill lacks: {needle}")
    check(flat(skill("Codex", AGENTS)) == agents.replace("/mosaico:", "$mosaico:"), "the Codex agent-management skill differs from Claude's")

    # The installer: Claude saves what the server returns; Codex installs nothing.
    codex_schedule = flat(skill("Codex", SCHEDULE))
    check("installs no routine from Codex" in codex_schedule and "outreach_get_routine_setup" in codex_schedule, "the Codex installer does not leave installing to Claude")

    # README: the release note, the pairing with the server release, what was removed.
    readme = read(ROOT / "README.md")
    check(readme.index("### 0.10.0") < readme.index("### 0.9.26"), "the README changelog lacks 0.10.0 above 0.9.26")
    entry = flat(readme[readme.index("### 0.10.0"):readme.index("### 0.9.26")])
    for needle in ("#2168 to #2182", "Do not tag, publish or install this plugin before that release is live on main-v2", "Plugin and server release together",
                   "mosaico-outreach-repair-run", "outreach_get_repair_queue", "24-hour rules", "20 invitation sends per owner per day", "outreach_get_routine_setup",
                   "outreach_record_routine_schedule", "catalogueVersion", "remove_retired_routines", CATALOGUE_VERSION, "browser-script gate",
                   "tests/test_thin_outreach_skills.py", "tests/test_client_only_rules.py", "tests/test_thin_skill_budget.py"):
        check(needle in entry, f"the README 0.10.0 entry lacks: {needle}")
    check("## Current state (0.10.0)" in readme, "the README lacks the 0.10.0 current state")

    print(
        "PASS: both packages carry thin Outreach skills (start the run, follow the step, end the run, give the server's report unchanged, stop on a blocker), "
        "name the routine sections the server's texts point at, carry none of the moved know-how and no Repair, the installer saves what the server returns, "
        f"and both manifests and the README are at {VERSION}."
    )


if __name__ == "__main__":
    main()
