#!/usr/bin/env python3
"""0.9.13: Source leads writes no invitation drafts; Sync data writes the missing ones from `draftsToWrite`.

The application owns the list, its recommended action and the refusal (ADR-0005): a draft write inside any sourcing run is refused
with `sourcing-writes-no-drafts`, and `outreach_get_day` (in `workflowStatus`) and `outreach_get_follow_ups` return `draftsToWrite`.
These checks pin that the skills only follow that list: Source leads never attempts a draft and treats the refusal as expected, the
Sync data routine writes drafts for the owner's own Leads from the list, never approves or sends one, and the installer stamps the
Sync data and Source leads texts 0.9.13 while Repair is untouched.

0.9.19: the Send invitations run works one ordered list Mosaico keeps (`workflowStatus.sendRun`: send, check, draft). These checks
also pin that the skills follow `sendRun.recommendedAction` after every answer, order the work send, check, draft (never drafts
first), end `complete` only when Mosaico says `end_run`, do what a refused end (`send-run-open`) names without arguing, and no longer
carry their own "do not try a refused Lead again" rule (Mosaico skips a Lead it refused twice and lists it under `skippedThisRun`).
They also pin the owner's limits (server release 20261014a): checks and drafts are for Leads placed on a later day, Mosaico hands out
at most `checkLimit` checks and `draftLimit` drafts a run and counts them (`checksThisRun`, `draftsThisRun`), the skills point at those
fields and state no number of their own, and the interactive opening question says that Send invitations is one run (send, check, draft).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "plugins" / "mosaico-claude"
CODEX = ROOT / "plugins" / "mosaico-codex"

LIST_FIELDS = ("count", "entries", "leadId", "name", "agentId", "day", "action", "writtenBy", "writableInThisRun", "allowedActions", "recommendedAction", "note")
OPTIONAL_APP_NEEDLES = (
    "SOURCING_WRITES_NO_DRAFTS_CODE = 'sourcing-writes-no-drafts'",
    "DRAFT_INVITATION_ACTION = 'draft_invitation_messages'",
    "readonly writableInThisRun: boolean",
    "readonly recommendedAction: typeof DRAFT_INVITATION_ACTION | 'none'",
    "readonly leadId: string",
    "readonly agentId: string | null",
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flat(text: str) -> str:
    return " ".join(text.replace("`", "").split())


def section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    check(match is not None, f"missing section {heading}")
    return match.group(1)


def main() -> None:
    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        raw = read(root / "skills" / "mosaico-outreach-invite-run" / "SKILL.md")
        text = flat(raw)

        # 1. Source leads: finds, saves, places, ends. It never writes a draft and takes the refusal as expected.
        sourcing = flat(section(raw, "Source Leads"))
        for needle in (
            "never writes an invitation draft, for its own Leads or a colleague's",
            "Mosaico refuses a draft write inside any sourcing run with sourcing-writes-no-drafts",
            "Do not write any invitation draft, for your Lead or hers",
            "sourcing-writes-no-drafts (state blocked, recommended action continue_with_next_lead), that is expected and not a failure",
            "nothing was saved, the Lead stays saved and placed; continue with the next Lead",
            "its writableInThisRun is false and its recommendedAction is none",
            "recommends end_run or end_run_days_full",
            "nothing is left to verify or sort",
        ):
            check(needle in sourcing, f"{package} Source Leads section lacks: {needle}")
        for gone in ("Source Leads and prepare drafts", "Source Leads only", "source Leads and prepare invitation drafts", "prepare invitation drafts", "Draft a colleague's invitation", "lead-awaiting-owner-check", "colleague-draft-invite-only", "verify or draft"):
            check(gone not in text, f"{package} invite-run skill still holds: {gone}")
        check("Write the missing outbound Invite draft" not in text and "write a missing invitation draft" not in text.lower(), f"{package} invite-run skill still tells a sourcing run to write a draft")

        # 2. The Source leads routine: one action, no drafts, the refusal is expected.
        routine = flat(raw[raw.index("## Source leads routine"):].split("\n## Send invitations routine")[0])
        check('the action is "source Leads only"' in routine, f'{package} Source leads routine does not name the one action "source Leads only"')
        check("It never writes invitation drafts, approves, sends or messages; the Send invitations schedule" in routine, f"{package} Source leads routine intro still allows drafts")
        step3 = routine[routine.index("Step 3."):routine.index("Step 4.")]
        for needle in ("writes no invitation draft, for your Leads or a colleague's", "draftsToWrite list", "do not attempt one", "sourcing-writes-no-drafts", "expected and not a failure", "continue_with_next_lead", "Never approve or send an invitation"):
            check(needle in step3, f"{package} Source leads Step 3 lacks: {needle}")
        step4 = routine[routine.index("Step 4."):routine.index("Step 5.")]
        check("nothing is left to verify or sort, or when Mosaico recommends end_run or end_run_days_full" in step4, f"{package} Source leads Step 4 does not stop at end_run")
        step5 = routine[routine.index("Step 5."):]
        check("drafts written" not in step5 and "sourcing-writes-no-drafts is not reported as a failure" in step5, f"{package} Source leads Step 5 still reports drafts or fails on the refusal")
        report = flat(section(raw, "Report a sourcing run"))
        check("no drafts: a Source leads run writes none" in report and "never reported as a failure or a blocker" in report, f"{package} sourcing report does not treat the refusal as expected")

        # 3. The drafting procedure follows the application's list and recommended action; it never rebuilds either.
        drafts_raw = section(raw, "Write missing invitation drafts")
        drafts = flat(drafts_raw)
        for field in LIST_FIELDS:
            check(field in drafts, f"{package} 'Write missing invitation drafts' lacks the field name: {field}")
        for needle in (
            "the Lead owner's work, done in the Send invitations routine for the person's own Leads only",
            "A Source leads run never does it",
            "outreach_get_day for today with intent: send_approved_invitations",
            "outreach_get_follow_ups carries the same list as a top-level draftsToWrite",
            "never rebuild it from other reads or from memory",
            "Work the list only when it is draft_invitation_messages. When it is none, write nothing",
            "outreach_get_agents with no arguments",
            "messageInstructions", "messagingChecklist", "checklistReview",
            "outreach_record_message", "kind invite", "direction outbound", "sentAt null", "Pass no ownerUserId",
            "for no other Lead",
            "Never approve, send or mark sent a draft you wrote",
            # 0.9.19: a Send invitations run follows the work list Mosaico keeps; Mosaico, not the model, skips a Lead it refused twice.
            "In a Send invitations run Mosaico hands the drafts out as the last step of its one work list, after the sends and the connection checks",
            "the Lead to draft is the one in sendRun.next",
            "the answer to each draft carries sendRun",
            "its next is the next Lead and its recommendedAction the one thing to do, so no reread is needed",
            # 0.9.19 (server release 20261014a): drafts are for Leads placed on a later day whose connection was checked and is not connected, within the run's draft limit.
            "Mosaico hands out a draft only for a Lead placed on a later day (after today) whose connection was checked and is not connected, and at most sendRun.draftLimit drafts in the run; it counts them itself (sendRun.draftsThisRun, sendRun.draftsLeft)",
            "Keep no list of Leads tried: Mosaico skips a Lead whose draft it refused twice in the run and lists it under sendRun.skippedThisRun",
            "the Leads that need a person, and the Leads left over once the draft limit is reached (draft-limit-reached), under sendRun.waiting",
            "until recommendedAction is no longer draft_invitation_messages",
            "from its answers and not from memory",
        ):
            check(needle in drafts, f"{package} 'Write missing invitation drafts' lacks: {needle}")
        for gone in ("do not try it again in this run", "A Lead Mosaico refused stays on the list", "once every entry has been tried", "Stop when every entry has been tried"):
            check(gone not in drafts, f"{package} 'Write missing invitation drafts' still holds the model-side retry rule: {gone}")
        check(not re.search(r"ownerUserId", drafts_raw.replace("Pass no `ownerUserId`", "")), f"{package} 'Write missing invitation drafts' tells the model about ownerUserId")
        both = flat(section(raw, "Both"))
        # 0.9.19: Mosaico orders a send run's list: sends, then checks, then drafts. The model never drafts first.
        check("Never approve a newly created draft automatically" in both and "Sourcing is never part of this" in both, f"{package} Both section does not send approved only and keep sourcing out")
        check("sends come first, then connection checks, then drafts" in both and "Mosaico sets the order, not you" in both, f"{package} Both section does not say Mosaico orders send, check, draft")
        check("Complete **Write missing invitation drafts** first" not in both and both.index("Complete **Send approved invitations** first") < both.index("complete **Write missing invitation drafts**"), f"{package} Both section still drafts first")
        check("Do not write a draft before Mosaico offers it: it recommends none while a send or a check is left" in both, f"{package} Both section does not hold the draft back until Mosaico offers it")
        check("Mosaico also sets how much one run does: checks and drafts are for Leads placed on a later day (after today), and it hands out at most sendRun.checkLimit checks and sendRun.draftLimit drafts in a run" in both,
              f"{package} Both section does not point at Mosaico's check and draft limits")
        # 0.9.19 (server release 20261014a): the skills carry no limit of their own and no old wording of the first draft of this release.
        for gone in ("at most 20", "up to 20", "20 checks", "from today on", "checkCap", "sendRun.checkCap"):
            check(gone not in text, f"{package} invite-run skill still holds the old send-run wording: {gone}")
        # (colleague-check-cap-reached is the Source leads colleague check's own note, not the send run's old waiting reason.)
        check(not re.search(r"(?<![\w-])check-cap-reached", text), f"{package} invite-run skill still names the send run's old waiting reason check-cap-reached")
        check(not re.search(r"\b(?:20|100) (?:checks|drafts)\b", text), f"{package} invite-run skill states a send-run limit as a number; it points at sendRun.checkLimit and sendRun.draftLimit")
        # The interactive opening question tells the person that Mosaico runs send, check, draft in one run (no drafts-only or send-only choice for a send run).
        opening = flat(raw[raw.index("Before using any Outreach or browser tool"):raw.index("## Start the run")])
        check('"For those days, do you want to source Leads only, or run Send invitations? Send invitations is one run in which Mosaico first sends the approved invitations, then checks the connections it hands out, then writes the missing invitation drafts, in that order."' in opening,
              f"{package} opening question does not say that Send invitations is one run in the order send, check, draft")
        check("write missing invitation drafts, send approved invitations, or write drafts and send" not in opening, f"{package} opening question still offers drafts only or send only for a send run")
        if package == "Codex":
            # Codex cannot capture connection evidence, so it cannot do the check step; it stops there and never asks to end as complete.
            check("follow it, and never count or remember what is left yourself" in both and "when sendRun.recommendedAction is verify_connection, stop there, do not ask to end the run as complete" in both and "left for a Claude Send invitations run" in both, "Codex Both section does not stop at the check step it cannot do")
        # 0.9.19: a refused end of a send run is not argued with, in the End the run section of both packages.
        end = flat(section(raw, "End the run"))
        for needle in (
            "a Send invitations run is done when Mosaico says its work list is empty: workflowStatus.sendRun.phase is done and the recommended action is end_run",
            "Mosaico refuses the same way for a Send invitations run whose work list is not empty: the answer is blocked with send-run-open, the run stays open, nothing is recorded, and the answer names the count left and the next action (sendRun.next, recommendedAction)",
            "Do not argue and do not ask again: do what the answer names and go on from there",
            "A blocked end needs the same proof as above",
        ):
            check(needle in end, f"{package} End the run section lacks: {needle}")
        send = flat(section(raw, "Send approved invitations"))
        check("outreach_record_message" not in send, f"{package} Send approved invitations may write a draft")
        start = flat(raw[raw.index("## Start the run"):raw.index("## Source Leads\n")])
        check("Sourcing is always its own run; writing drafts and sending share one send_approved_invitations run" in start, f"{package} Start the run does not keep sourcing apart from drafting and sending")
        check("missing invitation drafts" in flat(raw.split("---", 2)[1]), f"{package} invite-run description does not name drafting")

    # 4. Send invitations routine (Claude, invite-run): since 0.9.19 one run works the ordered list Mosaico keeps (send, check, draft),
    #    follows its recommended action after every answer, ends only when Mosaico says end_run and never argues with a refused end.
    follow = read(CLAUDE / "skills" / "mosaico-outreach-follow-up-run" / "SKILL.md")
    invite_claude = read(CLAUDE / "skills" / "mosaico-outreach-invite-run" / "SKILL.md")
    sync = flat(section(invite_claude, "Send invitations routine"))
    for needle in (
        "It never approves a draft, and it does nothing else: no follow-ups, no messages, no withdrawals, no sourcing",
        "One run works one ordered list that Mosaico keeps for the person's own Leads: it sends the invitations that are already approved, then checks the connections Mosaico hands out, then writes the missing invitation drafts",
        'the scope is invitations for today with the actions "write missing invitation drafts" and "send approved invitations"',
        # (a) the run follows the application's recommended action; it never counts, orders or rebuilds the list.
        "Call outreach_get_day for today with intent send_approved_invitations and the runId",
        "Follow sendRun.recommendedAction for the Lead in sendRun.next, and do that action and nothing else",
        "verify_connection means run the approved connection-evidence script for that Lead (next.verifyAction is the exact call",
        "send_approved_invitations means send, as Step 3 says",
        "draft_invitation_messages means write one draft with sentAt null for that Lead, as the \"Write missing invitation drafts\" section says, and never approve or send it",
        "end_run means end the run (see Step 4 below)",
        "The answer to a connection check or a draft carries sendRun with the next Lead and the one recommendedAction: do that, with no reread",
        "The answer to a send or a recorded delivery block does not: reread the day",
        "Never count, order or remember what is left yourself, and never rebuild the list from draftsToWrite or any other read",
        "A Lead that needs a person, or that is left over once a limit is reached (reasons check-limit-reached and draft-limit-reached), is listed under sendRun.waiting with a reason, and a Lead whose check or draft Mosaico refused twice in this run is skipped and listed under sendRun.skippedThisRun: leave both alone, they never hold the end of the run",
        # 0.9.19 (server release 20261014a): checks are for Leads placed on a later day and not checked yet; drafts for those checked and not connected; both within Mosaico's limits, counted by Mosaico.
        "first the approved invitations to send (a Lead holding one is checked first, and that check never counts toward a limit)",
        "then the connections to check (every Lead placed on a later day, after today, whose connection is not checked yet, soonest day first)",
        "then the missing invitation drafts for the person's own Leads placed on a later day whose connection was checked and is not connected",
        "Mosaico hands out at most sendRun.checkLimit checks and sendRun.draftLimit drafts in one run and counts both itself (sendRun.checksThisRun and sendRun.checksLeft, sendRun.draftsThisRun and sendRun.draftsLeft): you never count them",
        'with the selected action "send approved invitations", when sendRun.recommendedAction is send_approved_invitations',
        # (b) a refused end is not argued with: do what the answer names.
        "End the run with outreach_end_run, with reason complete only when Mosaico says its work list is empty (sendRun.phase done, completion complete, recommendedAction end_run)",
        "Mosaico refuses with send-run-open, records nothing and keeps the run open; its answer names the count left and the next action. Do not argue and do not ask again: do what the answer names",
        "a Lead that cannot be invited is not a blocker",
        # the report states Mosaico's figures, not memory.
        "using Mosaico's counts from its answers, not memory",
        "invitation drafts written (sendRun.draftsThisRun), each with its Lead",
        "connection checks made (sendRun.checksThisRun) and what Mosaico answered",
        "the Leads that waited (sendRun.waiting in the end answer, each with its reason: a person is needed, or check-limit-reached, or draft-limit-reached)",
        "the Leads Mosaico skipped after two refusals (sendRun.skippedThisRun, each with its step and code)",
    ):
        check(needle in sync, f"Send invitations routine lacks: {needle}")
    # (c) the order is send, then check, then draft, in the routine's own words.
    check(sync.index("first the approved invitations to send") < sync.index("then the connections to check") < sync.index("then the missing invitation drafts for the person's own Leads"), "Send invitations routine does not order send, check, draft")
    for gone in ("at most 20", "Leads placed from today on", "sendRun.checkCap", "checkCap"):
        check(gone not in sync, f"Send invitations routine still holds the old check wording: {gone}")
    check(sync.index("Step 3. Sending") < sync.index("Step 4. End the run") < sync.index("Step 5. Report"), "Send invitations routine steps are out of order")
    for gone in (
        "draftsToWrite on the day read (outreach_get_follow_ups carries the same list) and follow its recommendedAction",
        "Reread the day after every write and continue until Mosaico reports completion (no-approved-invitations-remain)",
        "Step 2. Run this skill with the selected day today and the selected action \"write missing invitation drafts\"",
    ):
        check(gone not in sync, f"Send invitations routine still holds the drafts-first procedure: {gone}")
    # The Follow-up routine writes no invitation draft and sends no invitation; the old Sync data heading is only a superseded note.
    fu = flat(section(follow, "Follow-up routine"))
    for gone in ("write missing invitation drafts", "send approved invitations", "linkedin-sent-invitations.js", "draftsToWrite list"):
        check(gone not in fu, f"Follow-up routine still holds invitation work: {gone}")
    check("\n## Sync data routine\n" not in follow and "## Sync data routine (superseded)" in follow, "the follow-up-run skill still has a live Sync data routine")
    old = flat(section(follow, "Sync data routine (superseded)"))
    check("Do not run any part of it" in old and "has to be reinstalled" in old and "start no Outreach run" in old, "the superseded note does not stop an old saved schedule")
    note = flat(section(follow, "Missing invitation drafts are not follow-up work"))
    check("draftsToWrite" in note and "do not act on it" in note and "a Source leads run never does" in note, "follow-up-run lacks the note that draftsToWrite is not follow-up work")
    codex_follow = read(CODEX / "skills" / "mosaico-outreach-follow-up-run" / "SKILL.md")
    check("Sync data routine" not in codex_follow, "Codex follow-up-run holds a Sync data routine")

    # 5. The installer: the Sync data and Source leads texts carry the 0.9.13 stamp, Repair keeps 0.9.6, nothing says 0.9.12 any more.
    installer_raw = read(CLAUDE / "skills" / "mosaico-outreach-schedule-install" / "SKILL.md")
    texts = re.findall(r"```text\n(.*?)\n```", installer_raw, re.S)
    check(len(texts) == 6, f"Claude installer must hold six schedule texts, found {len(texts)}")
    sync_text, follow_text, withdraw_text, own_text, colleagues_text, repair_text = texts
    for label, text, section_name, stamp in (("Send invitations", sync_text, "Send invitations routine", "0.9.15"), ("Follow-up", follow_text, "Follow-up routine", "0.9.18"), ("Withdraw stale invitations", withdraw_text, "Withdraw stale invitations routine", "0.9.15"), ("Source leads (own)", own_text, "Source leads routine", "0.9.13"), ("Source leads (colleagues)", colleagues_text, "Source leads routine", "0.9.13")):
        check(f"({stamp} or later)" in text and f'is older than {stamp} or has no "{section_name}" section' in text, f"the {label} text is not stamped {stamp}")
        check("0.9.12" not in text, f"the {label} text still names 0.9.12")
        check(len(text.split()) <= 200, f"the {label} text is not thin")
        for procedure in ("outreach_", "draftsToWrite", "Step 1", "checklistReview"):
            check(procedure not in text, f"the {label} text holds procedure: {procedure}")
    check('"write missing invitation drafts"' in sync_text and '"send approved invitations"' in sync_text and '"one pass per thread"' not in sync_text, "the Send invitations text lacks its two actions")
    check('"one pass per thread"' in follow_text and "invitation" not in follow_text.replace("accepted invitations", ""), "the Follow-up text lacks its action or names invitation work")
    check('action: "source Leads only"' in own_text and 'action: "source Leads only"' in colleagues_text, 'a Source leads text does not name the one action "source Leads only"')
    check("(0.9.6 or later)" in repair_text, "the Repair stamp changed")
    codex_installer_raw = read(CODEX / "skills" / "mosaico-outreach-schedule-install" / "SKILL.md")
    codex_texts = re.findall(r"```text\n(.*?)\n```", codex_installer_raw, re.S)
    check(len(codex_texts) == 1 and "(0.9.13 or later)" in codex_texts[0] and 'action: "source Leads only"' in codex_texts[0], "the Codex Source leads text is not stamped 0.9.13 with the one action")
    check("### Update the standing answers in place" in installer_raw, "the installer lost the update-in-place path")
    flat_installer = " ".join(installer_raw.split())
    check('a saved Sync data task, which is not updated in place but retired' in flat_installer and 'still names the action "source Leads and prepare invitation drafts"' in flat_installer, "the installer does not move older Sync data or Source leads texts in place")

    # 6. Overview skills.
    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        overview = flat(read(root / "skills" / "mosaico-outreach" / "SKILL.md"))
        check("A Source run never writes drafts: the Lead owner's Send invitations run does" in overview and "Write missing invitation drafts" in overview and "draftsToWrite" in overview, f"{package} overview skill does not describe who writes drafts")
        check("save personalized invitation drafts" not in overview, f"{package} overview skill still says Source saves drafts")

    # 7. Versions and the changelog entry that holds the release gate.
    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json"):
        check(json.loads(read(manifest))["version"] == "0.9.20", f"{manifest.name} is not at 0.9.20")
    readme = read(ROOT / "README.md")
    check(readme.index("### 0.9.13") < readme.index("### 0.9.12"), "README changelog lacks 0.9.13 above 0.9.12")
    entry = flat(readme[readme.index("### 0.9.13"):readme.index("### 0.9.12")])
    for needle in (
        "mosaicohr-com/mosaico#1834", "Do not publish or install this plugin before that release is live on main-v2",
        "sourcing-writes-no-drafts", "continue_with_next_lead", "end_run", "draftsToWrite", "draft_invitation_messages", "writableInThisRun",
        "Write missing invitation drafts", "outreach_get_agents", "checklistReview", "never approves or sends a draft", "stamped 0.9.13 or later", "Repair is unchanged",
    ):
        check(needle in entry, f"README 0.9.13 entry lacks: {needle}")
    check("tests/test_sync_drafts_skill.py" in readme, "README does not list this test")

    # 8. When the application checkout is at hand, the server still carries what this release relies on.
    app = os.environ.get("MOSAICO_APP_REPO")
    if app:
        server = Path(app) / "features" / "outreach" / "server"
        module, registry = server / "outreach-drafts-to-write.ts", server / "outreach-mcp-registry.ts"
        if module.is_file() and registry.is_file():
            source = read(module)
            for needle in OPTIONAL_APP_NEEDLES:
                check(needle in source, f"the application's drafts module lacks: {needle}")
            registry_text = read(registry)
            check("draftsToWrite: draftsToWrite(" in registry_text and "SOURCING_WRITES_NO_DRAFTS" in registry_text, "the application registry does not return draftsToWrite or refuse sourcing drafts")

    print("PASS: Source leads saves and places Leads only and treats sourcing-writes-no-drafts as expected; Sync data writes the missing invitation drafts from draftsToWrite for its own Leads and never approves or sends; the Sync data and Source leads texts are stamped 0.9.13; the Send invitations run follows Mosaico's ordered work list (send, check, draft) and its refused end.")


if __name__ == "__main__":
    main()
